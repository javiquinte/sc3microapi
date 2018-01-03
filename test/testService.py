#!/usr/bin/env python3

"""Tests to check that sc3microapi is working

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
any later version.

   :Copyright:
       2017 Javier Quinteros, GEOFON, GFZ Potsdam <geofon@gfz-potsdam.de>
   :License:
       GPLv3
   :Platform:
       Linux

.. moduleauthor:: Javier Quinteros <javier@gfz-potsdam.de>, GEOFON, GFZ Potsdam
"""

import sys
import os
import datetime
import unittest
from urllib.request import Request
from urllib.request import urlopen
from urllib.request import HTTPError
from urllib.parse import urlparse
import json
from distutils.version import StrictVersion
from xml.dom.minidom import parseString
from html.parser import HTMLParser
from unittestTools import WITestRunner

class SC3MicroApiTests(unittest.TestCase):
    """Test the functionality of sc3microapi.py."""

    @classmethod
    def setUp(cls):
        """Setting up test."""
        cls.host = host

    def test_wrong_parameter(self):
        """Unknown parameter."""
        msg = 'An error code 400 Bad Request is expected for an unknown ' + \
            'parameter'
        req = Request('%s/network/?wrongparam=1' % self.host)
        try:
            u = urlopen(req)
            u.read()
        except HTTPError as e:
            self.assertEqual(e.getcode(), 400, msg)
            return

        self.assertTrue(False, msg)
        return

    def test_wrong_format(self):
        """Wrong format option."""
        req = Request('%s/network/?format=WRONGFORMAT' % self.host)
        msg = 'When a wrong format is specified an error code 400 is expected!'
        try:
            u = urlopen(req)
            u.read()
        except HTTPError as e:
            if hasattr(e, 'code'):
                self.assertEqual(e.getcode(), 400, '%s (%s)' % (msg, e.code))
                return

            self.assertTrue(False, '%s (%s)' % (msg, e))
            return

        self.assertTrue(False, msg)
        return

    def test_version(self):
        """'version' method."""
        if self.host.endswith('/'):
            vermethod = '%sversion' % self.host
        else:
            raise Exception('Wrong service URL format. A / is expected as last character.')

        req = Request(vermethod)
        try:
            u = urlopen(req)
            buffer = u.read()
        except:
            raise Exception('Error retrieving version number')

        # Check that it is a version format supported by distutils.version
        try:
            StrictVersion(buffer.decode('utf-8'))
        except Exception as e:
            msg = 'Version number not supported by distutils.version!'
            self.assertTrue(False, e)

    def test_help(self):
        """Help if no method is defined."""
        if not self.host.endswith('/'):
            raise Exception('Wrong service URL format. A / is expected as last character.')

        req = Request(self.host)
        try:
            u = urlopen(req)
            buffer = u.read()
        except:
            raise Exception('Error retrieving help.')

        # Check that the object returned seems to be an HTML page
        try:
            # instantiate the parser and fed it some HTML
            parser = HTMLParser()
            parser.feed(buffer)
        except Exception as e:
            msg = 'Help format does not seem to be HTML!'
            self.assertTrue(False, e)

    def test_network(self):
        """'network' method."""
        if self.host.endswith('/'):
            netmethod = '%snetwork/' % self.host
        else:
            raise Exception('Wrong service URL format. A / is expected as last character.')

        req = Request(netmethod)
        try:
            u = urlopen(req)
            buffer = u.read()
        except:
            raise Exception('Error retrieving network list.')

        # Check that the object returned seems to be JSON and containing networks
        try:
            json.loads(buffer, encoding='utf-8')
        except Exception as e:
            msg = 'Networks could not be read/parsed!'
            self.assertTrue(False, e)


# ----------------------------------------------------------------------
def usage():
    """Print how to use the service test."""
    print('testService [-h|--help] [-p|--plain] http://server/path')


global host

if __name__ == '__main__':

    # 0=Plain mode (good for printing); 1=Colourful mode
    mode = 1

    # The default host is localhost
    for ind, arg in enumerate(sys.argv):
        if ind == 0:
            continue
        if arg in ('-p', '--plain'):
            del sys.argv[ind]
            mode = 0
        elif arg in ('-h', '--help'):
            usage()
            sys.exit(0)
        else:
            host = arg
            del sys.argv[ind]

    unittest.main(testRunner=WITestRunner(mode=mode))
