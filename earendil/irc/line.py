import collections
import re

__all__ = ['Line', 'parse_line', 'unparse_line']

Line = collections.namedtuple('Line', ['source', 'command', 'arguments', 'ctcp'])

class Isomorphism:
    # in the loosest terms...
    @staticmethod
    def simple(forward, backward):
        iso = Isomorphism.__new__(Isomorphism)
        iso.forward = forward
        iso.backward = backward
        return iso

    def compose(self, other):
        def fwd(x):
            return other.forward(self.forward(x))
        def bwd(x):
            return self.backward(other.backward(x))
        return Isomorphism.simple(fwd, bwd)

# forward : friendly -> encoded
# backward: encoded  -> friendly

class Liner(Isomorphism):
    def forward(self, unlined):
        return unlined + b'\r\n'
    def backward(self, lined):
        if not lined.endswith(b'\r\n'):
            raise ValueError("invalid line")
        return lined[:-2]

class Quoter(Isomorphism):
    def __init__(self, quote, codemap):
        self.quote = quote
        self.codemap = codemap
        requote = re.escape(quote)
        self.unquoter = re.compile(requote + b'(.)', re.DOTALL)
    
    def forward(self, unquoted):
        s = unquoted.replace(self.quote, self.quote + self.quote)
        for code, char in self.codemap.items():
            s = s.replace(char, self.quote + code)
        return s

    def backward(self, quoted):
        def replacer(matchobj):
            c = matchobj.group(1)
            return self.codemap.get(c, c)
        return self.unquoter.sub(replacer, quoted)

low_level = Quoter(b'\020', {
    b'0': b'\0',
    b'n': b'\n',
    b'r': b'\r',
})

class Tagger(Isomorphism):
    def __init__(self, delim=b'\001'):
        self.delim = delim
        redelim = re.escape(delim)
        self.untagger = re.compile(redelim + b'(.*?)' + redelim, re.DOTALL)

    def forward(self, tags):
        if not tags:
            raise ValueError("need at least one tag")
        if any(self.delim in t for t in tags):
            raise ValueError("invalid character in tags")
        base = tags[0]
        for t in tags[1:]:
            base += self.delim + t + self.delim
        return base

    def backward(self, base):
        tags = []
        def replacer(matchobj):
            tags.append(matchobj.group(1))
            return b''
        base = self.untagger.sub(replacer, base)
        tags.insert(0, base)
        return tags

class Map(Isomorphism):
    def __init__(self, inner):
        self.inner = inner
    def forward(self, l):
        return [self.inner.forward(x) for x in l]
    def backward(self, l):
        return [self.inner.backward(x) for x in l]

ctcp_level = Quoter(b'\\', {
    b'a': b'\001',
})

class Protocol(Isomorphism):
    def forward(self, line):
        s = b''
        if line.source:
            s = b':' + line.source + b' '
        cmd = line.command
        if type(cmd) == int:
            cmd = '{:03d}'.format(cmd).encode('ascii')
        s += cmd.upper()
        if line.arguments:
            for arg in line.arguments[:-1]:
                if any(c in arg for c in b' \t'):
                    raise ValueError('whitespace in middle argument')
                if not arg:
                    raise ValueError('empty middle argument')
                s += b' ' + arg
            last = line.arguments[-1]
            if any(c in last for c in b' \t') or not last:
                s += b' :'
            else:
                s += b' '
            s += last
        return [s] + line.ctcp

    def backward(self, tags):
        if not tags:
            raise ValueError('need at least one tag')
        line = tags[0].lstrip()

        source = None
        if line.startswith(b':'):
            line = line.split(maxsplit=1)
            if len(line) > 1:
                source, line = line
                source = source[1:]
                line = line.lstrip()
            else:
                line = line[0]
        
        last = None
        if b' :' in line:
            line, last = line.split(b' :', 1)
        elif b'\t:' in line:
            line, last = line.split(b'\t:', 1)
        line = line.rstrip()

        if not line:
            raise ValueError("invalid irc line")
        line = line.split()
        if last is not None:
            line.append(last)
        
        command = line[0]
        try:
            command = int(command)
        except ValueError:
            command = command.upper()
        line = line[1:]

        return Line(source, command, line, tags[1:])

full_stack = Protocol().compose(Map(ctcp_level)).compose(Tagger()).compose(low_level).compose(Liner())

def parse_line(line):
    return full_stack.backward(line)

def unparse_line(line):
    return full_stack.forward(line)
