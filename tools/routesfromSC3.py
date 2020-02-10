#!/usr/bin/env python3
#
# sc3microapi WS - prototype
#
# (c) 2017-2020 Javier Quinteros, GEOFON team
# <javier@gfz-potsdam.de>
#
# ----------------------------------------------------------------------

"""sc3microapi WS - prototype

   :Platform:
       Linux
   :Copyright:
       GEOFON, GFZ Potsdam <geofon@gfz-potsdam.de>
   :License:
       GNU General Public License v3

.. moduleauthor:: Javier Quinteros <javier@gfz-potsdam.de>, GEOFON, GFZ Potsdam
"""

##################################################################
#
# First all the imports
#
##################################################################

import sys
import argparse
import requests
import xml.etree.cElementTree as ET
import configparser


def main():
    # Call the sc3microapi method "networks"
    urlbase = 'http://st27dmz.gfz-potsdam.de/sc3microapi'

    msg = 'Generate an XML file with routes to be used in a Routing Service.'
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument('-o', '--output', default='routing.xml',
                        help='File to save the list of available routes.')
    parser.add_argument('-r', '--rules', default=None,
                        help='File with rules to generate the output.')
    parser.add_argument('-u', '--url',
                        help='URL pointing to an instance of sc3microapi.',
                        default=urlbase)
    parser.add_argument('-a', '--archive', type=str, default=None,
                        help='Filter networks by its "archive" attribute. For instance, "GFZ".')
    parser.add_argument('-s', '--shared', type=int, default=None, choices=[0, 1],
                        help='Filter networks by its "shared" attribute')
    parser.add_argument('-l', '--loglevel',
                        help='Verbosity in the output.',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO',
                                 'DEBUG'])
    args = parser.parse_args()

    # Call the sc3microapi method "networks"
    url = '%s/network/' % args.url

    # Build query, read result and save to a file
    headers = {
        'User-Agent': 'routesfromSC3 python-requests/' + requests.__version__,
    }

    params = dict()
    # Request in XML format ready to get ingested in a Routing Service
    params['outformat'] = 'xml'

    if args.shared is not None:
        params['shared'] = args.shared

    if args.archive is not None:
        params['archive'] = args.archive

    r = requests.get(url, params, headers=headers)

    if r.status_code != 200:
        print('Error reading from %s with parameters: %s' % (url, params))
        sys.exit(2)

    # Filter and modify result based in file with rules

    # Read networks to skip from a file with rules
    if args.rules is not None:
        config = configparser.RawConfigParser()
        with open(args.rules, encoding='utf-8') as c:
            config.read_file(c)

        if config.has_section('Networks') and 'skip' in config.options('Networks'):
            nets2skip = [x.strip() for x in config.get('Networks', 'skip').split(',')]

    elem = ET.fromstring(r.content)
    print('Before')
    for net in elem:
        print(net.attrib)
        if net.get('networkCode') in nets2skip:
            # FIXME This seems to modify the sequence while reading. Change!
            elem.remove(net)
            # print('Borro %s' % net.get('networkCode'))

    print('After')
    for net in elem:
        print(net.attrib)

    with open(args.output, 'wb') as fout:
        fout.write(r.content)



if __name__ == '__main__':
    main()
