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
import json


def istemporary(net):
    return net[0] in '0123456789XYZ'


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
    parser.add_argument('--vnets', action='store_true', default=False,
                        help='Include information of virtual networks')
    parser.add_argument('-l', '--loglevel',
                        help='Verbosity in the output.',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO',
                                 'DEBUG'])
    args = parser.parse_args()

    # Filter and modify result based in file with rules

    # Read networks to skip and stations to add individually from a file with rules
    nets2skip = list()
    priority2 = list()
    stations2add = list()
    vnets2skip = list()

    if args.rules is not None:
        config = configparser.RawConfigParser()
        with open(args.rules, encoding='utf-8') as c:
            config.read_file(c)

        if config.has_section('Networks') and 'skip' in config.options('Networks'):
            nets2skip = [x.strip() for x in config.get('Networks', 'skip').split(',')]

        if config.has_section('Networks') and 'priority2' in config.options('Networks'):
            priority2 = [x.strip() for x in config.get('Networks', 'priority2').split(',')]

        if config.has_section('Stations') and 'include' in config.options('Stations'):
            stations2add = [x.strip() for x in config.get('Stations', 'include').split(',')]

        if config.has_section('Virtualnets') and 'skip' in config.options('Virtualnets'):
            vnets2skip = [x.strip() for x in config.get('Virtualnets', 'skip').split(',')]

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
            if not istemporary(net.get('networkCode')):
                if net.get('networkCode') in nets2skip:
                    elem.remove(net)
                    continue

                # Check if priority should be set to 2
                if net.get('networkCode') in priority2:
                    for route in net:
                        route.set('priority', "2")

            # And temporary networks
            if istemporary(net.get('networkCode')):
                net_start = '%s_%s' % (net.get('networkCode'), net[0].get('start')[:4])
                if net_start in nets2skip:
                    elem.remove(net)

                # Check if priority should be set to 2
                if net_start in priority2:
                    for route in net:
                        route.set('priority', "2")

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

    if args.vnets:
        # Create the XML output for virtual networks
        # http://st27dmz.gfz-potsdam.de/sc3microapi/virtualnet/stations/_GEALL/
        url = '%s/virtualnet/' % args.url
        r = requests.get(url)

        vns = json.loads(r.content.decode('utf-8'))
        for vn in vns:
            # Check if the Virtual Netowork must be skipped
            if vn['code'] in vnets2skip:
                continue
            # Retrieve stations in VN
            r = requests.get(args.url + '/virtualnet/stations/%s/?outformat=xml' % vn['code'])
            vnxml = ET.fromstring(r.content.decode('utf-8'))
            elem.append(vnxml[0])

    with open(args.output, 'wb') as fout:
        fout.write(ET.tostring(elem))


if __name__ == '__main__':
    main()
