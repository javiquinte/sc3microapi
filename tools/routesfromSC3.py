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
import xml.etree.ElementTree as ET
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

    # Filter and modify result based in file with rules

    # Read networks to skip and stations to add individually from a file with rules
    nets2skip = list()
    stations2add = list()

    if args.rules is not None:
        config = configparser.RawConfigParser()
        with open(args.rules, encoding='utf-8') as c:
            config.read_file(c)

        if config.has_section('Networks') and 'skip' in config.options('Networks'):
            nets2skip = [x.strip() for x in config.get('Networks', 'skip').split(',')]

        if config.has_section('Stations') and 'include' in config.options('Stations'):
            stations2add = [x.strip() for x in config.get('Stations', 'include').split(',')]

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

    # Create the XML for the networks
    elem = ET.fromstring(r.content)
    
    if len(nets2skip):
        for net in reversed(elem):
            # Check the case of permanent networks
            if net.get('networkCode') in nets2skip:
                elem.remove(net)
                continue

            # And temporary networks
            net_start = '%s_%s' % (net.get('networkCode'), net[0].get('start')[:4])
            if net_start in nets2skip:
                elem.remove(net)

    for netsta in stations2add:
        net, sta = netsta.split('.')

        # Call the sc3microapi method "stations"
        if sta == '*':
            url = '%s/station/%s' % (args.url, net)
        else:
            url = '%s/station/%s/%s' % (args.url, net, sta)

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

    # Create the XML for the networks
    elem2 = ET.fromstring(r.content)

    for stationroute in elem2:
        elem.append(stationroute)

    with open(args.output, 'wb') as fout:
        fout.write(ET.tostring(elem))


if __name__ == '__main__':
    main()
