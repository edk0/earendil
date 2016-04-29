import unittest
from ..irc import line
from .. import irc

def tiso(key, a, b):
    def tester(self):
        iso = getattr(self, key)
        x = iso.forward(a)
        self.assertEqual(x, b)
        x = iso.backward(b)
        self.assertEqual(a, x)
    return tester

class TestIRCLine(unittest.TestCase):
    def setUp(self):
        self.li = line.Liner()
        self.ll = line.low_level
        self.tag = line.Tagger()
        self.ctcp = line.ctcp_level
        self.prot = line.Protocol()
        self.all = line.full_stack

    test_li = tiso('li', b'blah', b'blah\r\n')
    def test_li_ends(self):
        with self.assertRaises(ValueError):
            self.li.backward(b'plain \r')
        with self.assertRaises(ValueError):
            self.li.backward(b'plain ')
    
    test_ll_plain = tiso('ll', b'plain \t\010', b'plain \t\010')
    test_ll_quote = tiso('ll', b'this\020', b'this\020\020')
    test_ll_many  = tiso('ll', b'a\020b\n\r', b'a\020\020b\020n\020r')
    def test_ll_unknown(self):
        self.assertEqual(self.ll.backward(b'\020a'), b'a')


    test_tag_plain = tiso('tag', [b'plain'], b'plain')
    test_tag_compound = tiso('tag', [b'one', b'two', b'three'], b'one\001two\001\001three\001')
    def test_tag_mixed(self):
        self.assertEqual(self.tag.backward(b'on\001two\001e'), [b'one', b'two'])
    def test_tag_invalid(self):
        with self.assertRaises(ValueError):
            self.tag.forward([b'one', b'tw\001o'])

    test_ctcp_plain = tiso('ctcp', b'plain', b'plain')
    test_ctcp_quote = tiso('ctcp', b'plain\\', b'plain\\\\')
    test_ctcp_mani  = tiso('ctcp', b'a\001b\\', b'a\\ab\\\\')

    test_prot_noarg_nosrc = tiso('prot', irc.Line(None, b'PING', [], []), [b'PING'])
    test_prot_arg_nosrc = tiso('prot', irc.Line(None, b'PING', [b'arg1', b'arg2'], []), [b'PING arg1 arg2'])
    test_prot_arg_src = tiso('prot', irc.Line(b'src', b'PING', [b'arg1'], []), [b':src PING arg1'])
    test_prot_larg_nosrc = tiso('prot', irc.Line(None, b'PRIVMSG', [b'nick', b'message here'], []), [b'PRIVMSG nick :message here'])
    test_prot_colon = tiso('prot', irc.Line(None, b'PRIVMSG', [b'nick', b'message : this'], []), [b'PRIVMSG nick :message : this'])
    test_prot_tags = tiso('prot', irc.Line(None, b'PING', [b'arg'], [b'tag1', b'tag2']), [b'PING arg', b'tag1', b'tag2'])
    test_prot_empty = tiso('prot', irc.Line(None, b'PING', [b''], []), [b'PING :'])
    test_prot_num = tiso('prot', irc.Line(None, 56, [b'arg1'], []), [b'056 arg1'])
    def test_prot_bad_whitespace_empty(self):
        with self.assertRaises(ValueError):
            self.prot.forward(irc.Line(None, b'PRIVMSG', [b'nick name', b'b'], []))
        with self.assertRaises(ValueError):
            self.prot.forward(irc.Line(None, b'PRIVMSG', [b'', b'b'], []))
    def test_prot_notags(self):
        with self.assertRaises(ValueError):
            self.prot.backward([])
    def test_prot_invalid(self):
        with self.assertRaises(ValueError):
            self.prot.backward([b'   '])
    def test_prot_whitespace(self):
        self.assertEqual(self.prot.backward([b'  :src\tPING\t  \t:arg  ']), irc.Line(b'src', b'PING', [b'arg  '], []))

    # examples from
    # http://www.irchelp.org/irchelp/rfc/ctcpspec.html
    test_all_1 = tiso('all', irc.Line(b'actor', b'PRIVMSG', [b'victim', b'Hi there!\nHow are you? \\K?'], []), b':actor PRIVMSG victim :Hi there!\020nHow are you? \\\\K?\r\n')
    test_all_2 = tiso('all', irc.Line(b'actor', b'PRIVMSG', [b'victim', b''], [b'SED \n\t\big\020\001\000\\:']), b':actor PRIVMSG victim :\001SED \020n\t\big\020\020\\a\0200\\\\:\001\r\n')
    test_all_3a = tiso('all', irc.Line(b'actor', b'PRIVMSG', [b'victim', b'Say hi to Ron\n\t/actor'], [b'USERINFO']), b':actor PRIVMSG victim :Say hi to Ron\020n\t/actor\001USERINFO\001\r\n')
    test_all_3b = tiso('all', irc.Line(b'victim', b'NOTICE', [b'actor', b''], [b'USERINFO :CS student\n\001test\001']), b':victim NOTICE actor :\001USERINFO :CS student\020n\\atest\\a\001\r\n')
