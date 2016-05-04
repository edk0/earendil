#!/usr/bin/env python3

import argparse
import json
import io
import os.path
from contextlib import contextmanager

reserved_words = {
    'class': 'cls',
    'data': 'dat',
    'source': 'src',
    'bytes': 'bytecount',
}

def name_camel(n: str) -> str:
    n = reserved_words.get(n, n)
    return ''.join(x.capitalize() for x in n.split('-'))

def name_snake(n: str) -> str:
    n = reserved_words.get(n, n)
    return n.replace('-', '_')

class Indenter:
    def __init__(self, file):
        self.level = 0
        self.file = file

    def writeln(self, fmt, *args, **kwargs):
        if fmt:
            self.file.write('    ' * self.level)
            self.file.write(fmt.format(*args, **kwargs))
        self.file.write('\n')

    @contextmanager
    def indent(self):
        self.level += 1
        try:
            yield
        finally:
            self.level -= 1
            if self.level <= 1:
                self.writeln('')

def maketype(arg):
    if arg['type'] == 'str':
        return 'str'
    elif arg['type'] == 'int':
        return 'int'
    elif arg['type'] == 'flag':
        return 'bool'
    elif arg['type'] == 'comma-list':
        return 'typing.List[{}]'.format(maketype(arg['inner']))
    elif arg['type'] == 'space-list':
        return 'typing.List[{}]'.format(maketype(arg['inner']))
    elif arg['type'] == 'optional':
        return maketype(arg['inner'])
    else:
        raise RuntimeError('unknown type: {}'.format(arg['type']))

def parse_arg(src, arg):
    if arg['type'] == 'str':
        return 'decode({})'.format(src)
    elif arg['type'] == 'int':
        return 'int({})'.format(src)
    elif arg['type'] == 'flag':
        return 'True'
    elif arg['type'] == 'comma-list':
        return '[{} for x in {}.split(b",")]'.format(parse_arg('x', arg['inner']), src)
    elif arg['type'] == 'space-list':
        return '[{} for x in {}.split()]'.format(parse_arg('x', arg['inner']), src)
    elif arg['type'] == 'optional':
        return parse_arg(src, arg['inner'])
    else:
        raise RuntimeError('unknown type: {}'.format(arg['type']))

def unparse_arg(src, arg):
    if arg['type'] == 'str':
        return 'encode({})'.format(src)
    elif arg['type'] == 'int':
        return 'encode(str({}))'.format(src)
    elif arg['type'] == 'flag':
        return 'b{}'.format(repr(arg['type-argument']))
    elif arg['type'] == 'comma-list':
        return 'b",".join({} for x in {})'.format(unparse_arg('x', arg['inner']), src)
    elif arg['type'] == 'space-list':
        return 'b" ".join({} for x in {})'.format(unparse_arg('x', arg['inner']), src)
    elif arg['type'] == 'optional':
        return unparse_arg(src, arg['inner'])
    else:
        raise RuntimeError('unknown type: {}'.format(arg['type']))

def parse_arg_to(ind, src, arg, prefix):
    if 'name' in arg:
        ind.writeln('{}_{} = {}', prefix, arg['name'], parse_arg(src, arg))
    else:
        assert arg['type'] == 'literal'
        ind.writeln('# {}_{}: {}', prefix, src, repr(arg['type-argument']))

def data_to_module(data, f):
    with open(os.path.join(os.path.split(__file__)[0], 'make-mod.header.py')) as j:
        header = j.read()
    f.write(header.format(**data))
    f.write('\n\n')
    ind = Indenter(f)

    # first, snake-namify all the argument names, because those drive me nuts
    for msg in data['messages']:
        msg['clsname'] = name_camel(msg['name'])
        msg['name'] = name_snake(msg['name'])
        for arg in msg['arguments']:
            if 'name' in arg:
                arg['name'] = name_snake(arg['name'])

    # turn a line into a message, if possible
    ind.writeln('def parse_message(line: Line, decode: typing.Callable[[bytes], str] = lambda b: b.decode("utf-8")) -> Message:')
    with ind.indent():
        ind.writeln('try:')
        with ind.indent():
            ind.writeln('source = None')
            ind.writeln('if line.source is not None:')
            with ind.indent():
                ind.writeln('source = decode(line.source)')
        ind.writeln('except Exception:')
        with ind.indent():
            ind.writeln('source = None')
        for msg in data['messages']:
            # figure out the min and max number of args
            min_args = 0
            max_args = 0
            for arg in msg['arguments']:
                max_args += 1
                if arg['type'] != 'optional':
                    min_args += 1
            arg_cmp = '{} <= len(line.arguments) <= {}'.format(min_args, max_args)
            if min_args == 0:
                arg_cmp = 'len(line.arguments) <= {}'.format(max_args)
            if min_args == max_args:
                arg_cmp = 'len(line.arguments) == {}'.format(min_args)
            verb = 'b{}'.format(repr(msg['verb']))
            if isinstance(msg['verb'], int):
                verb = '{}'.format(msg['verb'])
            ind.writeln('if line.command == {} and {}: # {}', verb, arg_cmp, msg['clsname'])
            with ind.indent():
                ind.writeln('try:')
                with ind.indent():
                    if msg['arguments']:
                        advancer = 'i += 1'
                        if msg['associativity'] == 'right':
                            ind.writeln('i = len(line.arguments) - 1')
                            advancer = 'i -= 1'
                        else:
                            ind.writeln('i = 0')
                    for arg in msg['arguments']:
                        if arg['type'] == 'optional':
                            ind.writeln('if len(line.arguments) > {}:', min_args)
                            min_args += 1
                            with ind.indent():
                                parse_arg_to(ind, 'line.arguments[i]', arg, msg['name'])
                                ind.writeln(advancer)
                            if 'name' in arg:
                                ind.writeln('else:')
                                with ind.indent():
                                    defval = 'None'
                                    if arg['inner']['type'] == 'flag':
                                        defval = 'False'
                                    ind.writeln('{}_{} = {}', msg['name'], arg['name'], defval)
                        else:
                            parse_arg_to(ind, 'line.arguments[i]', arg, msg['name'])
                            ind.writeln(advancer)
                    if msg['arguments']:
                        if msg['associativity'] == 'right':
                            ind.writeln('assert i == -1')
                        else:
                            ind.writeln('assert i == len(line.arguments)')
                    constrargs = 'source=source'
                    for arg in msg['arguments']:
                        if not 'name' in arg:
                            continue
                        constrargs += ', {0}={1}_{0}'.format(arg['name'], msg['name'])
                    ind.writeln('return {}({})', msg['clsname'], constrargs)
                ind.writeln('except Exception:')
                with ind.indent():
                    ind.writeln('pass')
        ind.writeln('return Unknown(source, line.command, line.arguments)')
    
    # classes
    for msg in data['messages']:
        ind.writeln('class {}(Message):', msg['clsname'])
        with ind.indent():
            # docstring (FIXME better docstring)
            ind.writeln('"""')
            ind.writeln('``{}``', msg['format'])
            if 'documentation' in msg:
                ind.writeln('')
                ind.writeln(msg['documentation'])
            ind.writeln('"""')
            ind.writeln('')

            # slots
            namedargs = [arg for arg in msg['arguments'] if 'name' in arg]
            if namedargs:
                ind.writeln('__slots__ = {}', repr([arg['name'] for arg in msg['arguments'] if 'name' in arg]))
                ind.writeln('')

            # init
            initargs = 'self, source: str'
            kwargs = ''
            for arg in namedargs:
                if arg['type'] == 'optional':
                    kwargs += ', {}: {} = None'.format(arg['name'], maketype(arg))
                else:
                    initargs += ', {}: {}'.format(arg['name'], maketype(arg))
            initargs += kwargs
            ind.writeln('def __init__({}) -> None:', initargs)
            with ind.indent():
                ind.writeln('self.source = source')
                for arg in namedargs:
                    ind.writeln('self.{0} = {0}', arg['name'])

            # repr
            ind.writeln('def __repr__(self) -> str:')
            with ind.indent():
                fmt = msg['clsname'] + '(source={}'
                args = 'repr(self.source)'
                for arg in namedargs:
                    fmt += ', ' + arg['name'] + '={}'
                    args += ', repr(self.{})'.format(arg['name'])
                fmt += ')'
                ind.writeln('return {}.format({})', repr(fmt), args)

            # to_line
            ind.writeln('def to_line(self, encode: typing.Callable[[str], bytes] = lambda s: s.encode("utf-8")) -> Line:')
            with ind.indent():
                verb = 'b{}'.format(repr(msg['verb']))
                if isinstance(msg['verb'], int):
                    verb = 'b"{:03d}"'.format(msg['verb'])
                ind.writeln('source = None')
                ind.writeln('if self.source is not None:')
                with ind.indent():
                    ind.writeln('source = encode(self.source)')
                if msg['arguments']:
                    ind.writeln('arguments = []')
                for arg in msg['arguments']:
                    if arg['type'] == 'optional':
                        ind.writeln('if self.{} is not None:', arg['name'])
                        with ind.indent():
                            ind.writeln('arguments.append({})', unparse_arg('self.' + arg['name'], arg))
                    else:
                        if 'name' in arg:
                            ind.writeln('arguments.append({})', unparse_arg('self.' + arg['name'], arg))
                        else:
                            assert arg['type'] == 'literal'
                            ind.writeln('arguments.append(b{})', repr(arg['type-argument']))
                if msg['arguments']:
                    ind.writeln('return Line(source, {}, arguments)', verb)
                else:
                    ind.writeln('return Line(source, {})', verb)

p = argparse.ArgumentParser()
p.add_argument('input', type=argparse.FileType('r'))
p.add_argument('output', type=argparse.FileType('w'))

if __name__ == "__main__":
    args = p.parse_args()
    data = json.load(args.input)

    data_to_module(data, args.output)

