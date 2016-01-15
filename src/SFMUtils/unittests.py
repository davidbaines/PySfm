import unittest
import io
from SfmToolsJC import *

#Note: some of the following strings will be cast as streams so the readers
#can treat them like files.

str01 = '''some header
\\lx blah
'''
str01h = 'some header\n'

str02 = '''\\_sh v3.0  400  MDF 4.0
\\_DateStampHasFourDigitYear 

\\lx
\\zx  zz

\\lx blah
\\ge gloss
\\de This is a long-winded
multi-line
definition.
\\xv v
\\xe e
\\xn n
\\xv v
\\xe e
\\xn n
'''
str02f = ["lx","\n"]
str02f2 = ["zx", " zz\n\n"]


class TestFieldReader(unittest.TestCase):
    def test_header(self):
        
        r = SFMFieldReader(io.StringIO(str01))
        self.assertEqual(r.header, str01h)

    def test_breaks(self):
        r = SFMFieldReader(io.StringIO(str02))
        f = break_field(r.__next__())
        self.assertEqual(f, str02f)
        f = break_field(r.__next__())
        self.assertEqual(f, str02f2)


class TestCaseRf(unittest.TestCase):

    def test_rf_insert(self):
        raise RuntimeError('desc')
        self.assertEqual(1,2)
        
    
    def test_rf_move_up(self):
        self.assertEqual(1,2)
'''

'''
