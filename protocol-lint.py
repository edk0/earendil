#!/usr/bin/env python3

import argparse
import json
import sys
import io

warn = None

def unpack_brackets(s):
    pairs = ["<>", "[]", "()"]
    if len(s) < 2:
        return None, s
    for a, b in pairs:
        if s[0] == a and s[-1] == b:
            return a, s[1:-1]
    return None, s

def parse_inner_arg(arg, ret):
    if arg.endswith(','):
        return dict(type='comma-list', inner=parse_inner_arg(arg[:-1], ret))
    elif arg.endswith('_'):
        return dict(type='space-list', inner=parse_inner_arg(arg[:-1], ret))
    elif ':' in arg:
        typ, arg = arg.split(':', 1)
    else:
        typ = 'str'

    data = {}
    if '(' in typ and typ.endswith(')'):
        typ, typarg = typ.split('(', 1)
        typarg = typarg[:-1]
        data['type-argument'] = typarg
        # make sure the type is a known argument type
        if not typ in ['flag', 'literal']:
            warn('type does not take argument: {}'.format(typ))

    # make sure the type is known
    if not typ in ['str', 'int', 'flag', 'literal']:
        warn('unknown type: {}'.format(typ))

    data['type'] = typ
    ret['name'] = check_name(arg)
    return data

def parse_arg(arg_orig):
    b, arg = unpack_brackets(arg_orig)
    ret = {}
    if not b:
        # literal
        return (['left', 'right'], {'type': 'literal', 'type-argument': arg})
    elif b == '<':
        typ = parse_inner_arg(arg, ret)
        ret.update(typ)
        return (['left', 'right'], ret)
    elif b == '[':
        ret['type'] = 'optional'
        ret['inner'] = parse_inner_arg(arg, ret)
        return (['left'], ret)
    elif b == '(':
        ret['type'] = 'optional'
        ret['inner'] = parse_inner_arg(arg, ret)
        return (['right'], ret)
    else:
        warn('cannot parse argument: {}'.format(arg_orig))

def check_name(name):
    name = name.strip()
    if not name: # names should have length
        warn('zero-length name')
    if name.lower() != name: # names should be lower-case
        warn('name not lowcased: {}'.format(name))
    if len(name.split()) > 1: # names should have no whitespace
        warn('name has whitespace: {}'.format(name))
    # names should be [a-z][0-9] and - only
    if not all(c.isalpha() or c.isdigit() or c == '-' for c in name):
        warn('name has invalid characters: {}'.format(name))
    return name

def parse_format(fmt, data):
    # formats should have a title, used as a name
    if not '{#' in fmt or not fmt.endswith('}'):
        warn('no name found')
    fmt, name = fmt.rsplit('{#', 1)
    fmt = fmt.strip()
    name = name[:-1]
    data['name'] = check_name(name)
    data['format'] = fmt

    # do our own tokenizing, to force balanced parens but handle : outside
    tokens = []
    expectstack = []
    expectmap = {'(': ')', '[': ']', '<': '>'}
    gather = ''
    split_on_space = True
    for c in fmt:
        if c in expectmap:
            expectstack.append(expectmap[c])
        if expectstack and c == expectstack[-1]:
            expectstack.pop()
        if c == ':' and not expectstack:
            split_on_space = False
            continue
        if split_on_space and c.isspace():
            if gather:
                tokens.append(gather)
            gather = ''
        else:
            gather += c
    if gather:
        tokens.append(gather)
    if expectstack:
        warn('unbalanced brackets, expecting: {}'.format(expectstack))
    
    # there should be at least a verb
    if not tokens:
        warn('no verb found')
    
    verb = tokens[0]
    args = tokens[1:]
    if not verb.upper() == verb: # verbs should be upper case
        warn('verb not upcased')
    if verb.isnumeric():
        # numerics must be 000 formatted
        if verb != '{:03d}'.format(int(verb)):
            warn('invalid numeric format')
        verb = int(verb)
        # numerics must be within this range
        if verb <= 0 or verb > 999:
            warn('invalid numeric code')
        data['type'] = 'numeric'
    else:
        data['type'] = 'text'
    data['verb'] = verb

    associativity = set(['left', 'right'])
    data['arguments'] = []
    argnames = []
    for a in args:
        assoc, arg = parse_arg(a)
        associativity.intersection(assoc)
        if 'name' in arg:
            # arguments must be unique
            if arg['name'] in argnames:
                warn('non-unique argument name: {}'.format(arg['name']))
            argnames.append(arg['name'])
        data['arguments'].append(arg)

    # rectify associativities
    if not associativity:
        warn('mixed associativities')
    associativity = list(associativity)
    associativity.sort()
    data['associativity'] = associativity[0]

    # numerics all have targets
    if data['type'] == 'numeric':
        if len(data['arguments']) < 1 or data['arguments'][0].get('name') != 'target' or data['arguments'][0].get('type') != 'str':
            print(data['arguments'][0])
            warn('numerics need a <target> argument')

    # a bunch of literals next to each other is always an error
    last_type = None
    for arg in data['arguments']:
        if arg['type'] == 'literal' and last_type == 'literal':
            warn('two successive literals, you need a :')
            break
        last_type = arg['type']

def create_description(f, fname):
    gather = {}
    section = None
    lineno = 0
    lastfmtno = 0
    docs = ''
    related = []
    l = None
    data = []
    names = []
    verbs = []
    version = None

    warnings = 0
    def local_warn(s):
        nonlocal warnings
        warnings += 1
        if 'verb' in gather:
            print('{}:{}: (verb {}) {}'.format(fname, lastfmtno, gather['verb'], s))
        else:
            print('{}:{}: {}'.format(fname, lastfmtno, s))

    global warn
    warn = local_warn

    def emit():
        nonlocal docs, section, gather, data
        if gather:
            docs = docs.strip()
            if docs:
                gather['documentation'] = docs
            if related:
                gather['related'] = related
            if section is None:
                # every message must have a section
                warn('no section here')
                gather['section'] = 'FIXME no section'
            else:
                gather['section'] = section
            data.append(gather)
    
    for l in f.readlines():
        lineno += 1
        origl = l
        l = l.strip()

        if l.startswith('*Version ') and l.endswith('*'):
            ver = l.split()[1]
            ver = ver[:-1]
            if not '.' in ver:
                warn('invalid version format')
            else:
                major, minor = ver.split('.', 1)
                if not major.isnumeric() or not minor.isnumeric():
                    warn('invalid version format')
                else:
                    version = (int(major), int(minor))
            
        if l.startswith('#') and not l.startswith('####'):
            emit()
            gather = {}
            docs = ''
            related = []

        if l.startswith('## '):
            _, section = l.split(' ', 1)

        if l.startswith('### '):
            _, fmt = l.split(' ', 1)
            lastfmtno = lineno
            parse_format(fmt, gather)
            # message names must be unique
            if gather['name'] in names:
                warn('non-unique name: {}'.format(gather['name']))
            names.append(gather['name'])
            # message verbs must be unique
            if gather['verb'] in verbs:
                warn('non-unique verb: {}'.format(gather['verb']))
            verbs.append(gather['verb'])
        else:
            if l.startswith('Related: '):
                related_l = l.split(': ', 2)[1]
                if related_l.endswith('.'):
                    related_l = related_l[:-1]
                related = related_l.split(', ')
                related = [(int(r) if r.isnumeric() else r) for r in related]
            else:
                docs += origl
    emit()

    # make sure all related verbs actually exist
    for msg in data:
        for rel in msg.get('related', []):
            if not rel in verbs:
                warn('unknown related verb for {}: {}'.format(msg['verb'], rel))

    if version is None:
        warn('no version found')

    if warnings > 0:
        return None
    ret = {}
    ret['messages'] = data
    ret['version-major'], ret['version-minor'] = version
    return ret

p = argparse.ArgumentParser()
p.add_argument('input', type=argparse.FileType('r'))
p.add_argument('-j', '--json', type=argparse.FileType('w'))
p.add_argument('-m', '--markdown', type=argparse.FileType('w'))

if __name__ == "__main__":
    args = p.parse_args()
    inp = args.input.read()

    f = io.StringIO(inp)
    data = create_description(f, args.input.name)
    if data is None:
        sys.exit(1)

    if args.json:
        json.dump(data, args.json, indent=2)

    if args.markdown:
        import markdown
        html = markdown.markdown(inp, extensions=['extra', 'toc'], safe_mode='escape')
        args.markdown.write(html + '\n')
