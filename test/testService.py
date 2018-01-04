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
        req = Request('%s/network/?outformat=WRONGFORMAT' % self.host)
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
            parser.feed(buffer.decode('utf-8'))
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
            json.loads(buffer.decode('utf-8'), encoding='utf-8')
        except Exception as e:
            msg = 'Networks could not be read/parsed!'
            self.assertTrue(False, e)

    def test_network_GE(self):
        """'network' method for GE."""
        if self.host.endswith('/'):
            netmethod = '%snetwork/GE/' % self.host
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
            json.loads(buffer.decode('utf-8'), encoding='utf-8')
        except Exception as e:
            msg = 'Network GE could not be read/parsed!'
            self.assertTrue(False, e)

    def test_network_XX(self):
        """'network' method for an unknown network (XX)."""

        msg = 'The search for network XX should return a 204 error code.'
        if self.host.endswith('/'):
            netmethod = '%snetwork/XX/' % self.host
        else:
            raise Exception('Wrong service URL format. A / is expected as last character.')

        req = Request(netmethod)
        try:
            u = urlopen(req)
            buffer = u.read()
        except HTTPError as e:
            if hasattr(e, 'code'):
                self.assertEqual(e.getcode(), 204, '%s (%s)' % (msg, e.code))
                return

            self.assertTrue(False, '%s (%s)' % (msg, e))
            return

        # Check that the object returned seems to be JSON and containing networks
        try:
            json.loads(buffer.decode('utf-8'), encoding='utf-8')
        except Exception as e:
            msg = 'Network GE could not be read/parsed!'
            self.assertTrue(False, e)

    def test_access_2F_denied(self):
        """access to network 2F for a non-GFZ email account."""

        msg = 'Access to 2F from a non-GFZ account should be denied with a 403 code.'
        if self.host.endswith('/'):
            accmethod = '{}access/?nslc=2F&email=none@none.com&starttime=2013-01-01&endtime=2013-01-01'.format(self.host)
        else:
            raise Exception('Wrong service URL format. A / is expected as last character.')

        req = Request(accmethod)
        try:
            u = urlopen(req)
            buffer = u.read()
        except HTTPError as e:
            if hasattr(e, 'code'):
                self.assertEqual(e.getcode(), 403, '%s (%s)' % (msg, e.code))
                return

            self.assertTrue(False, '%s (%s)' % (msg, e))
            return

        self.assertTrue(False, msg)
        return

    def test_access_2F_allowed(self):
        """access to network 2F for a GFZ email account."""

        msg = 'Access to 2F from a GFZ account should be allowed.'
        if self.host.endswith('/'):
            accmethod = '{}access/?nslc=2F&email=none@gfz-potsdam.de&starttime=2013-01-01&endtime=2013-01-01'.format(self.host)
        else:
            raise Exception('Wrong service URL format. A / is expected as last character.')

        req = Request(accmethod)
        try:
            u = urlopen(req)
            buffer = u.read()
        except HTTPError as e:
                self.assertTrue(False, '%s (%s)' % (msg, e))
                return

        self.assertTrue(True, msg)
        return

    def test_access_GE_allowed(self):
        """access to network GE for any email account."""

        msg = 'Access to GE from any email account should be allowed.'
        if self.host.endswith('/'):
            accmethod = '{}access/?nslc=GE&email=none@none.com&starttime=2013-01-01&endtime=2013-01-01'.format(self.host)
        else:
            raise Exception('Wrong service URL format. A / is expected as last character.')

        req = Request(accmethod)
        try:
            u = urlopen(req)
            buffer = u.read()
        except HTTPError as e:
                self.assertTrue(False, '%s (%s)' % (msg, e))
                return

        self.assertTrue(True, msg)
        return

    def test_access_ZS_allowed(self):
        """access to network ZS_2007 for any email account."""

        msg = 'Access to ZS_2007 from any email account should be allowed.'
        if self.host.endswith('/'):
            accmethod = '{}access/?nslc=ZS&email=none@none.com&starttime=2007-01-01&endtime=2007-01-01'.format(self.host)
        else:
            raise Exception('Wrong service URL format. A / is expected as last character.')

        req = Request(accmethod)
        try:
            u = urlopen(req)
            buffer = u.read()
        except HTTPError as e:
                self.assertTrue(False, '%s (%s)' % (msg, e))
                return

        self.assertTrue(True, msg)
        return

    def test_access_ZS_GFZ_allowed(self):
        """access to network ZS_2017 for a GFZ email account."""

        msg = 'Access to ZS_2017 from a GFZ email account should be allowed.'
        if self.host.endswith('/'):
            accmethod = '{}access/?nslc=ZS&email=yuan@gfz-potsdam.de&starttime=2017-01-01&endtime=2017-01-01'.format(self.host)
        else:
            raise Exception('Wrong service URL format. A / is expected as last character.')

        req = Request(accmethod)
        try:
            u = urlopen(req)
            buffer = u.read()
        except HTTPError as e:
                self.assertTrue(False, '%s (%s)' % (msg, e))
                return

        self.assertTrue(True, msg)
        return

    def test_access_ZS_denied(self):
        """access to network ZS for any email account."""

        msg = 'Access to ZS_2017 from any email account should be denied.'
        if self.host.endswith('/'):
            accmethod = '{}access/?nslc=ZS&email=none@none.com&starttime=2017-01-01&endtime=2017-01-01'.format(self.host)
        else:
            raise Exception('Wrong service URL format. A / is expected as last character.')

        req = Request(accmethod)
        try:
            u = urlopen(req)
            buffer = u.read()
        except HTTPError as e:
            if hasattr(e, 'code'):
                self.assertEqual(e.getcode(), 403, '%s (%s)' % (msg, e.code))
                return

            self.assertTrue(False, '%s (%s)' % (msg, e))
            return

        self.assertTrue(True, msg)
        return


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
