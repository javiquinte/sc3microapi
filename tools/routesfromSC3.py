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


def main():
    # Call the sc3microapi method "networks"
    urlbase = 'http://st27dmz.gfz-potsdam.de/sc3microapi'

    msg = 'Generate an XML file with routes to be used in a Routing Service.'
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument('-o', '--output', default='routing.xml',
                        help='File to save the list of available routes.')
    parser.add_argument('-r', '--rules',
                        help='File with rules to generate the output.',
                        default='rules.cfg')
    parser.add_argument('-u', '--url',
                        help='URL pointing to an instance of sc3microapi.',
                        default=urlbase)
    parser.add_argument('-a', '--archive', type=str, default=None,
                        help='Filter networks by its "archive" attribute. For instance, "GFZ".')
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
    url = '%s/network/'

    # TODO Build query, read result and save to a file

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

    r = requests.get(url, params)

    if r.status_code != 200:
        print('Error reading from %s with parameters: %s' % (url, params))
        sys.exit(2)

    with open(args.output, 'wb') as fout:
        fout.write(r.content)

    # TODO Filter and modify result based in cfg file (e.g. station routes instead of network routes)


if __name__ == '__main__':
    main()
