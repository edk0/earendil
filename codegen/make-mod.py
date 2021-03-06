#!/usr/bin/env python3

import argparse
import json
import io
import os.path
from contextlib import contextmanager

reserved_words = {
    'class': 'klass',
    'cls': 'kls',
    'data': 'dat',
    'source': 'src',
    'pass': 'passwd',
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

def make_arglist(msg):
    initargs = ''
    kwargs = ''
    for arg in msg['arguments']:
        if not 'name' in arg:
            continue
        if arg['type'] == 'optional':
            kwargs += ', {}: {} = None'.format(arg['name'], maketype(arg))
        else:
            initargs += ', {}: {}'.format(arg['name'], maketype(arg))
    initargs += kwargs
    return initargs

def write_docstring(ind, msg):
    # docstring (FIXME better docstring)
    ind.writeln('"""')
    ind.writeln('``{}``', msg['format'])
    if 'documentation' in msg:
        ind.writeln('')
        ind.writeln(msg['documentation'])
    ind.writeln('"""')
    ind.writeln('')

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

def parse_arg_to(ind, src, arg):
    if 'name' in arg:
        ind.writeln('{} = {}', arg['name'], parse_arg(src, arg))
    else:
        assert arg['type'] == 'literal'
        ind.writeln('# {}: {}', src, repr(arg['type-argument']))

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

    # classes
    for msg in data['messages']:
        ind.writeln('class {}(Message):', msg['clsname'])
        with ind.indent():
            write_docstring(ind, msg)
            
            # slots
            namedargs = [arg for arg in msg['arguments'] if 'name' in arg]
            if namedargs:
                ind.writeln('__slots__ = {}', repr([arg['name'] for arg in msg['arguments'] if 'name' in arg]))
                ind.writeln('')

            # init
            initargs = 'self, source: str' + make_arglist(msg)
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

            # from_line
            ind.writeln('@classmethod')
            ind.writeln('def from_line(cls, line: Line, decode: typing.Callable[[bytes], str] = lambda b: b.decode("utf-8")) -> Message:')
            with ind.indent():
                ind.writeln('source = None')
                ind.writeln('if line.source is not None:')
                with ind.indent():
                    ind.writeln('source = decode(line.source)')
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
                ind.writeln('if line.command != {}:', verb)
                with ind.indent():
                    ind.writeln('raise ValueError("incorrect verb")')
                ind.writeln('if not ({}):', arg_cmp)
                with ind.indent():
                    ind.writeln('raise ValueError("wrong number of arguments")')
                if msg['arguments']:
                    advancer = 'i += 1'
                    done = 'i == len(line.arguments)'
                    if msg['associativity'] == 'right':
                        ind.writeln('i = len(line.arguments) - 1')
                        advancer = 'i -= 1'
                        done = 'i == -1'
                    else:
                        ind.writeln('i = 0')
                for arg in msg['arguments']:
                    if arg['type'] == 'optional':
                        ind.writeln('if len(line.arguments) > {}:', min_args)
                        min_args += 1
                        with ind.indent():
                            parse_arg_to(ind, 'line.arguments[i]', arg)
                            ind.writeln(advancer)
                        if 'name' in arg:
                            ind.writeln('else:')
                            with ind.indent():
                                defval = 'None'
                                if arg['inner']['type'] == 'flag':
                                    defval = 'False'
                                ind.writeln('{} = {}', arg['name'], defval)
                    else:
                        parse_arg_to(ind, 'line.arguments[i]', arg)
                        ind.writeln(advancer)
                if msg['arguments']:
                    ind.writeln('assert {}', done)
                constrargs = 'source=source'
                for arg in namedargs:
                    constrargs += ', {0}={0}'.format(arg['name'])
                ind.writeln('return cls({})', constrargs)

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

    # verbmap
    ind.writeln('from_lines_by_verb = {{')
    with ind.indent():
        for msg in data['messages']:
            verb = 'b{}'.format(repr(msg['verb']))
            if isinstance(msg['verb'], int):
                verb = '{}'.format(msg['verb'])
            ind.writeln('{}: {}.from_line,', verb, msg['clsname'])
    ind.writeln('}}')

    # factory mixin
    ind.writeln('class MessageFactory:')
    with ind.indent():
        ind.writeln('message_source = None # type: str')
        ind.writeln('def message(self, msg: Message) -> None:')
        with ind.indent():
            ind.writeln('raise NotImplementedError("MessageFactory.message")')
        for msg in data['messages']:
            initargs = 'self' + make_arglist(msg)
            ind.writeln('def {}({}) -> None:', msg['name'], initargs)
            with ind.indent():
                write_docstring(ind, msg)
                constrargs = 'self.message_source'
                for arg in msg['arguments']:
                    if not 'name' in arg:
                        continue
                    constrargs += ', {0}={0}'.format(arg['name'])
                ind.writeln('self.message({}({}))', msg['clsname'], constrargs)

    # handler mixin
    ind.writeln('class MessageHandler:')
    with ind.indent():
        for msg in data['messages']:
            ind.writeln('def on_{0}(self, {0}: {1}) -> None: pass', msg['name'], msg['clsname'])
        ind.writeln('def on_message(self, msg: Message) -> None:')
        with ind.indent():
            cond = 'if'
            for msg in data['messages']:
                ind.writeln('{} isinstance(msg, {}):', cond, msg['clsname'])
                cond = 'elif'
                with ind.indent():
                    ind.writeln('self.on_{}(msg)', msg['name'])

p = argparse.ArgumentParser()
p.add_argument('input', type=argparse.FileType('r'))
p.add_argument('output', type=argparse.FileType('w'))

if __name__ == "__main__":
    args = p.parse_args()
    data = json.load(args.input)

    data_to_module(data, args.output)

