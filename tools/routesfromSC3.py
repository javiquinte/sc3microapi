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

import argparse
import urllib.request as ul


def main():
    msg = 'Generate an XML file with routes to be used in a Routing Service.'
    parser = argparse.ArgumentParser(description=msg)
    parser.add_argument('-l', '--loglevel',
                        help='Verbosity in the output.',
                        choices=['CRITICAL', 'ERROR', 'WARNING', 'INFO',
                                 'DEBUG'])
    parser.add_argument('-c', '--config',
                        help='Config file to use.',
                        default='../routing.cfg')
    parser.add_argument('-a', '--archive', type=str, default=None,
                        help='Filter networks by its "archive" attribute. For instance, "GFZ".')
    parser.add_argument('-s', '--shared', type=int, default=None, choices=[0, 1],
                        help='Filter networks by its "shared" attribute')
    args = parser.parse_args()

    # Call the sc3microapi method "networks"
    url = 'http://st27dmz.gfz-potsdam.de/sc3microapi/network/'

    # TODO Build query, read result and save to a file
    # TODO Filter and modify result based in cfg file (e.g. station routes instead of network routes)


if __name__ == '__main__':
    main()
