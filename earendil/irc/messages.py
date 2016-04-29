import json
import inspect
import os.path

__all__ = ['Message']

class Message:
    __slots__ = []

def name_camel(n):
    if n == 'class':
        return 'Cls'
    return ''.join(x.capitalize() for x in n.split('-'))

def name_snake(n):
    # reserved words, either by python or by us
    if n == 'class':
        return 'cls'
    if n == 'data':
        return 'dat'
    return n.replace('-', '_')

def load_protocol_data():
    # FIXME better file finding
    here = os.path.split(__file__)[0]
    datapath = os.path.join(here, '..', '..', 'codegen', 'messages.json')
    with open(datapath) as f:
        data = json.load(f)
        if data['major-version'] != 0:
            raise ImportError('cannot find useful protocol data')
        return data['messages']

def fill_methods(d, msg):
    params = [inspect.Parameter('self', inspect.Parameter.POSITIONAL_OR_KEYWORD)]
    paramks = []
    for a in msg['arguments']:
        if not 'name' in a:
            continue
        if a['type'] == 'optional':
            p = inspect.Parameter(name_snake(a['name']), inspect.Parameter.KEYWORD_ONLY, default=None)
            paramks.append(p)
        else:
            p = inspect.Parameter(name_snake(a['name']), inspect.Parameter.POSITIONAL_OR_KEYWORD)
            params.append(p)
    sig = inspect.Signature(params + paramks)
    def __init__(self, *args, **kwargs):
        binds = sig.bind(self, *args, **kwargs)
        for a in msg['arguments']:
            if not 'name' in a:
                continue
            setattr(self, name_snake(a['name']), binds.arguments.get(name_snake(a['name'])))
    __init__.__signature__ = sig
    d['__init__'] = __init__

    @property
    def data(self):
        ret = {}
        for a in msg['arguments']:
            v = getattr(self, name_snake(a['name']))
            if v is None and a['type'] == 'optional':
                continue
            ret[name_snake(a['name'])] = v
        return ret
    d['data'] = data

    def __repr__(self):
        return '{}.{}({})'.format(self.__class__.__module__, self.__class__.__name__, ', '.join(k + '=' + repr(v) for k, v in self.data.items()))
    d['__repr__'] = __repr__

protocol_data = load_protocol_data()

for msg in protocol_data:
    clsname = name_camel(msg['name'])
    d = {}

    d['__doc__'] = '``{}``\n\n{}'.format(msg['format'], msg.get('documentation', ''))
    d['__slots__'] = [name_snake(arg['name']) for arg in msg['arguments'] if 'name' in arg]
    fill_methods(d, msg)
    globals()[clsname] = type(clsname, (Message,), d)
    __all__.append(clsname)
