import collections
import re
from typing import TypeVar, Generic, Callable, Dict, List, Union, Any

class Line:
    __slots__ = ['source', 'command', 'arguments', 'ctcp']

    def __init__(self, source: bytes, command: Union[bytes, int], arguments: List[bytes] = [], ctcp: List[bytes] = []) -> None:
        self.source = source
        self.command = command
        self.arguments = arguments
        self.ctcp = ctcp

    def __repr__(self) -> str:
        return "Line(source={}, command={}, arguments={}, ctcp={})".format(repr(self.source), repr(self.command), repr(self.arguments), repr(self.ctcp))

    def __eq__(self, other: Any) -> bool:
        return self.source == other.source and self.command == other.command and self.arguments == other.arguments and self.ctcp == other.ctcp

    def to_raw(self) -> bytes:
        return full_stack.forward(self)

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')
D = TypeVar('D')

class Isomorphism(Generic[A, B]):
    def forward(self, x: A) -> B:
        raise NotImplementedError("forward")

    def backward(self, x: B) -> A:
        raise NotImplementedError("backward")
    
    def compose(self, other: 'Isomorphism[B, C]') -> 'Isomorphism[A, C]':
        return Composed(self, other)

class Composed(Isomorphism[A, C], Generic[A, C]):
    def __init__(self, a: Isomorphism[A, B], b: Isomorphism[B, C]) -> None:
        self.a = a
        self.b = b

    def forward(self, x: A) -> C:
        return self.b.forward(self.a.forward(x))

    def backward(self, x: C) -> A:
        return self.a.backward(self.b.backward(x))

# forward : friendly -> encoded
# backward: encoded  -> friendly

class Liner(Isomorphism[bytes, bytes]):
    def forward(self, unlined: bytes) -> bytes:
        return unlined + b'\r\n'
    def backward(self, lined: bytes) -> bytes:
        if not lined.endswith(b'\r\n'):
            raise ValueError("invalid line")
        return lined[:-2]

class Quoter(Isomorphism[bytes, bytes]):
    def __init__(self, quote: bytes, codemap: Dict[bytes, bytes]) -> None:
        self.quote = quote
        self.codemap = codemap
        requote = re.escape(quote)
        self.unquoter = re.compile(requote + b'(.)', re.DOTALL)
    
    def forward(self, unquoted: bytes) -> bytes:
        s = unquoted.replace(self.quote, self.quote + self.quote)
        for code, char in self.codemap.items():
            s = s.replace(char, self.quote + code)
        return s

    def backward(self, quoted: bytes) -> bytes:
        def replacer(matchobj: 're.Match') -> bytes:
            c = matchobj.group(1)
            return self.codemap.get(c, c)
        return self.unquoter.sub(replacer, quoted)

low_level = Quoter(b'\020', {
    b'0': b'\0',
    b'n': b'\n',
    b'r': b'\r',
})

class Tagger(Isomorphism[List[bytes], bytes]):
    def __init__(self, delim: bytes = b'\001') -> None:
        self.delim = delim
        redelim = re.escape(delim)
        self.untagger = re.compile(redelim + b'(.*?)' + redelim, re.DOTALL)

    def forward(self, tags: List[bytes]) -> bytes:
        if not tags:
            raise ValueError("need at least one tag")
        if any(self.delim in t for t in tags):
            raise ValueError("invalid character in tags")
        base = tags[0]
        for t in tags[1:]:
            base += self.delim + t + self.delim
        return base

    def backward(self, base: bytes) -> List[bytes]:
        tags = []
        def replacer(matchobj: 're.Match') -> bytes:
            tags.append(matchobj.group(1))
            return b''
        base = self.untagger.sub(replacer, base)
        tags.insert(0, base)
        return tags

class Lift(Isomorphism[A, B], Generic[A, B]):
    def __init__(self, inner: Isomorphism[C, D], up: Callable[[Callable[[C], D], A], B], down: Callable[[Callable[[D], C], B], A]) -> None:
        self.inner = inner
        self.up = up
        self.down = down
    def forward(self, l: A) -> B:
        return self.up(self.inner.forward, l)
    def backward(self, l: B) -> A:
        return self.down(self.inner.backward, l)

ctcp_level = Quoter(b'\\', {
    b'a': b'\001',
})

class Protocol(Isomorphism[Line, List[bytes]]):
    def forward(self, line: Line) -> List[bytes]:
        s = b''
        if line.source:
            s = b':' + line.source + b' '
        cmd = line.command
        if isinstance(cmd, int):
            cmd = '{:03d}'.format(cmd).encode('ascii')
        elif isinstance(cmd, bytes):
            cmd = cmd.upper()
        s += cmd
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

    def backward(self, tags: List[bytes]) -> Line:
        if not tags:
            raise ValueError('need at least one tag')
        line = tags[0].lstrip()

        source = None
        if line.startswith(b':'):
            lineparts = line.split(maxsplit=1)
            if len(line) > 1:
                source, line = lineparts
                source = source[1:]
                line = line.lstrip()
            else:
                line = lineparts[0]
        
        last = None
        if b' :' in line:
            line, last = line.split(b' :', 1)
        elif b'\t:' in line:
            line, last = line.split(b'\t:', 1)
        line = line.rstrip()

        if not line:
            raise ValueError("invalid irc line")
        lineparts = line.split()
        if last is not None:
            lineparts.append(last)
        
        command = lineparts[0] # type: Union[bytes, int]
        try:
            command = int(command)
        except ValueError:
            if isinstance(command, bytes):
                command = command.upper()
        lineparts = lineparts[1:]

        return Line(source, command, lineparts, tags[1:])

full_stack = Protocol().compose(Lift(ctcp_level, lambda f, l: list(map(f, l)), lambda f, l: list(map(f, l)))).compose(Tagger()).compose(low_level).compose(Liner())

def parse_line(line: bytes) -> Line:
    return full_stack.backward(line)
