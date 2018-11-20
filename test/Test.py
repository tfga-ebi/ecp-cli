# encoding: utf-8

import unittest
from ecp import argParser, DEV_URL, PROD_URL
import argparse


class Test(unittest.TestCase):

    parser = argParser()
    

    def test_dev(self):
        
        def assertDev(o, expectedDev):

            print o.dev
            self.assertEquals(o.dev, expectedDev)
        
        assertDev(self.parser.parse_args(['login', '--dev', 'localhost']), 'localhost' )
        assertDev(self.parser.parse_args(['login', '--dev'])             , DEV_URL     )
        assertDev(self.parser.parse_args(['login'])                      , PROD_URL    )

    
    def test_foo(self):
        '''
        >>> parser = argparse.ArgumentParser()
        >>> parser.add_argument('--foo', nargs='?', const='c', default='d')
        >>> parser.add_argument('bar', nargs='?', default='d')
        >>> parser.parse_args(['XX', '--foo', 'YY'])
        Namespace(bar='XX', foo='YY')
        >>> parser.parse_args(['XX', '--foo'])
        Namespace(bar='XX', foo='c')
        >>> parser.parse_args([])
        Namespace(bar='d', foo='d')
        '''

        parser = argparse.ArgumentParser()                             
        parser.add_argument('--foo', nargs='?', const='c', default='d')
        
        print parser.parse_args(['--foo', 'YY'])
        print parser.parse_args(['--foo'])
        print parser.parse_args([])
        
        
        
        


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
