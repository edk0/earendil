#!/usr/bin/env python3

import argparse
import json
import sys

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
    elif arg.startswith('#'):
        typ, arg = 'channel', arg[1:]
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
    if not typ in ['str', 'int', 'flag', 'literal', 'channel']:
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

def check_verb(verb):
    if not verb.upper() == verb: # verbs should be upper case
        warn('verb not upcased: {}'.format(verb))
    if verb.isnumeric():
        # numerics must be 000 formatted
        if verb != '{:03d}'.format(int(verb)):
            warn('invalid numeric format: {}'.format(verb))
        verb = int(verb)
        # numerics must be within this range
        if verb <= 0 or verb > 999:
            warn('invalid numeric code: {}'.format(verb))
    return verb

def parse_format(fmt, data):
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
    data['verb'] = check_verb(verb)
    if isinstance(data['verb'], int):
        data['type'] = 'numeric'
    else:
        data['type'] = 'text'

    associativity = set(['left', 'right'])
    data['arguments'] = []
    argnames = []
    for a in args:
        assoc, arg = parse_arg(a)
        associativity = associativity.intersection(assoc)
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

section_names = []
def check_section(title, data):
    required = ['name']
    
    # must have these fields
    for k in required:
        if not k in data:
            warn('required field `{}` missing'.format(k))
            return None

    # validate name
    data['name'] = check_name(data['name'])
    
    # section names must be unique
    if data['name'] in section_names:
        warn('non-unique section name: {}'.format(data['name']))
    section_names.append(data['name'])

    # add title
    data['title'] = title
    
    return data

message_names = []
message_verbs = {}
def check_message(fmt, data):
    required = ['name']
    
    # must have these fields
    for k in required:
        if not k in data:
            warn('required field `{}` missing'.format(k))
            return None

    # fill in computed details from format
    parse_format(fmt, data)

    # validate name
    data['name'] = check_name(data['name'])

    # message names must be unique
    if data['name'] in message_names:
        warn('non-unique message name: {}'.format(data['name']))
    message_names.append(data['name'])

    # message verbs must be unique
    if data['verb'] in message_verbs:
        warn('non-unique verb: {}'.format(data['verb']))
    message_verbs[data['verb']] = data['name']

    # related is a comma-seperated list
    if 'related' in data:
        data['related'] = [check_verb(r.strip()) for r in data['related'].split(',')]

    # only refer to section by name
    data['section'] = data['section']['name']

    return data

def check_version(ver, data):
    if not '.' in ver:
        warn('invalid version format')
        return (0, 0)
    maj, min = ver.split('.', 1)
    if not maj.isnumeric() or not min.isnumeric():
        warn('invalid version format')
        return (0, 0)
    return (int(maj), int(min))

def check_whole(data):
    # make sure all related verbs actually exist
    # and resolve them into names
    for msg in data['messages']:
        resolved_rel = []
        for rel in msg.get('related', []):
            if not rel in message_verbs:
                warn('unknown related verb for {}: {}'.format(msg['verb'], rel))
            else:
                resolved_rel.append(message_verbs[rel])
        if resolved_rel:
            msg['related'] = resolved_rel
    
    return data

def create_description(f, fname):
    lineno = 0
    lastheaderno = 0
    room_for_header = True
    sections = []
    messages = []
    version = None

    header = None
    gather = {}

    fields = {
        'Version': [],
        'Section': ['name', 'url'],
        'Message': ['name', 'related', 'documentation'],
    }
    
    warnings = 0
    def local_warn(s):
        nonlocal warnings
        warnings += 1
        if 'verb' in gather:
            print('{}:{}: (verb {}) {}'.format(fname, lastheaderno, gather['verb'], s))
        else:
            print('{}:{}: {}'.format(fname, lastheaderno, s))

    global warn
    warn = local_warn

    def emit():
        nonlocal header, gather, sections, messages, version
        if header is not None:
            if header[0] == 'Version':
                if version:
                    warn('only one version allowed')
                version = check_version(header[1], gather)
            elif header[0] == 'Section':
                section = check_section(header[1], gather)
                if section:
                    sections.append(section)
            elif header[0] == 'Message':
                if sections:
                    gather['section'] = sections[-1]
                    message = check_message(header[1], gather)
                    if message:
                        messages.append(message)
                else:
                    # every message must have a section
                    warn('message has no section')
        header = None
        gather = {}

    for l in f.readlines():
        lineno += 1
        
        if l.strip().startswith('#'):
            # comment
            continue

        if not l.strip():
            # blank
            room_for_header = True
            continue

        if not ':' in l:
            warn('no `:` found')
            continue

        key, val = l.split(':', 1)
        key = key.strip()
        val = val.strip()

        if key in fields:
            # new header
            emit()
            lastheaderno = lineno
            header = (key, val)
            if not room_for_header:
                warn('need whitespace before new header')
        elif header is not None and key in fields[header[0]]:
            gather[key] = val
        else:
            warn('invalid key in this location: {}'.format(key))
        room_for_header = False
    emit()

    if not version:
        warn('no version found')
        version = (0, 0)

    data = {}
    data['major-version'], data['minor-version'] = version
    data['sections'] = sections
    data['messages'] = messages

    return check_whole(data)

p = argparse.ArgumentParser()
p.add_argument('input', type=argparse.FileType('r'))
p.add_argument('output', type=argparse.FileType('w'))

if __name__ == "__main__":
    args = p.parse_args()
    data = create_description(args.input, args.input.name)
    if data is None:
        sys.exit(1)
    json.dump(data, args.output, indent=2)
    args.output.write('\n')
