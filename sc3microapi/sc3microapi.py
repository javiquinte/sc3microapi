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


import os
import io
from pydantic import constr
from typing import Union
from typing import Literal
# from sc3microapi import __version__
import csv
import json
import MySQLdb
from MySQLdb.cursors import DictCursor
import logging
import logging.config
from datetime import datetime
import configparser
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from fastapi.responses import HTMLResponse


# Define formally parts of the NSLC code
NetworkCode = constr(strip_whitespace=True, to_upper=True, min_length=2, max_length=2, pattern=r'[A-Z1-9]{2}')
StationCode = constr(strip_whitespace=True, to_upper=True, min_length=1, max_length=5, pattern=r'[A-Z][A-Z1-9]{0,4}')
LocationCode = constr(strip_whitespace=True, to_upper=True, max_length=2, pattern=r'[A-Z0-9]{0,2}')
ChannelCode = constr(strip_whitespace=True, to_upper=True, min_length=3, max_length=3, pattern=r'[A-Z0-9]{3}')

__version__ = '0.4a1'


def str2date(dateiso: constr(min_length=4, strip_whitespace=True, to_upper=True)) -> Union[datetime, None]:
    """Transform a string to a datetime.

    :param dateiso: A datetime in ISO format.
    :type dateiso: string
    :return: A datetime represented the converted input.
    :rtype: datetime
    """
    # In case of empty string
    if not len(dateiso):
        return None

    try:
        dateparts = dateiso.replace('-', ' ').replace('T', ' ')
        dateparts = dateparts.replace(':', ' ').replace('.', ' ')
        dateparts = dateparts.replace('Z', '').split()
        result = datetime.datetime(*map(int, dateparts))
    except Exception:
        raise ValueError('{} could not be parsed as datetime.'.format(dateiso))

    return result


class SC3dbconnection(object):
    def __init__(self, host: str, user: str, password: str, db: str = 'seiscomp3'):
        """Constructor of the AccessAPI class."""
        self.host = host
        self.user = user
        self.password = password
        self.db = db
        self.conn = None
        self.cursor = None
        # Save connection
        self.connect()
        self.log = logging.getLogger('SC3dbconnection')

    def connect(self):
        # Save connection
        self.conn = MySQLdb.connect(self.host, self.user, self.password,
                                    self.db, cursorclass=DictCursor)

    def fetchone(self):
        if self.cursor is None:
            raise Exception('Cursor has not been created!')

        return self.cursor.fetchone()

    def fetchall(self):
        if self.cursor is None:
            raise Exception('Cursor has not been created!')

        return self.cursor.fetchall()

    def execute(self, query, variables):
        try:
            self.cursor = self.conn.cursor()
            self.cursor.execute(query, variables)
        except MySQLdb.OperationalError:
            self.log.error('OperationalError exception. Trying to reconnect.')
            self.connect()
            self.cursor = self.conn.cursor()
            self.cursor.execute(query, variables)
            self.log.warning('Reconnection successful: {}.'.format(self.conn))

        return


app = FastAPI()


@app.get('/', response_class=HTMLResponse)
def getroot():
    # TODO Create an HTML page with a minimum documentation for a user
    try:
        with open('help.html') as fin:
            texthelp = fin.read()
    except FileNotFoundError:
        texthelp = """<html>
                        <head>sc3microapi</head>
                        <body>
                          Default help for the sc3microapi service (GEOFON).
                        </body>
                      </html>"""
    return texthelp.encode('utf-8')


@app.get('/version', response_class=PlainTextResponse)
def version():
    """Return the version of this implementation.

    :returns: Version of the system
    :rtype: string
    """
    return __version__.encode('utf-8')


# @cherrypy.expose
# class AccessAPI(object):
#     """Object dispatching methods related to access to streams."""
#
#     def __init__(self, host: str, user: str, password: str, db: str):
#         """Constructor of the AccessAPI class."""
#         # Save connection
#         self.conn = SC3dbconnection(host, user, password, db)
#         self.log = logging.getLogger('AccessAPI')
#
#     def __access(self, email: str, net: NetworkCode = '', sta: StationCode = '', loc: LocationCode = '',
#                  cha: ChannelCode = '', starttime: str = None, endtime: str = None):
#         # Check network access
#         # self.cursor = self.conn.cursor()
#         whereclause = ['networkCode=%s',
#                        'stationCode=%s',
#                        'locationCode=%s',
#                        'streamCode=%s',
#                        '%s LIKE concat("%%", user, "%%")']
#         variables = [net, sta, loc, cha, email]
#
#         if starttime is not None:
#             whereclause.append('start<=%s')
#             variables.append(starttime)
#
#         if endtime is not None:
#             whereclause.append('(end>=%s or end is NULL)')
#             variables.append(endtime)
#
#         query = 'select count(*) as howmany from Access where ' + ' and '.join(whereclause)
#         self.conn.execute(query, variables)
#         result = self.conn.fetchone()
#
#         if result is not None:
#             return result['howmany']
#
#         raise Exception('No result querying the DB ({})'.format(query % variables))
#
#     @cherrypy.expose
#     def index(self, nslc: constr(strip_whitespace=True, to_upper=True),
#               # pattern=r'[A-Z][A-Z1-9]\.[A-Z][A-Z1-9]{0,4}\.[A-Z0-9]{0,2}\.[A-Z0-9]{3}'),
#               email: constr(strip_whitespace=True), starttime: str = None, endtime: str = None) -> bytes:
#         """Check if the user has access to a stream.
#
#         The output should be empty, because the error code is the real output.
#         200 to indicate that a user has access and 403 when it does not.
#
#         :param nslc: Network.Station.Location.Channel
#         :type nslc: str
#         :param email: Email address from the user
#         :type email: str
#         :param starttime: Start time of the time window to access
#         :type starttime: str
#         :param endtime: End time of the time window to access
#         :type endtime: str
#         :returns: Empty string
#         :rtype: utf-8 encoded string
#         :raises: cherrypy.HTTPError
#         """
#
#         # Check parameters
#         try:
#             auxnslc = nslc.split('.')
#             nslc2 = [auxnslc[pos] if len(auxnslc) > pos else '' for pos in range(4)]
#             if len(nslc2) != 4:
#                 raise Exception
#         except Exception:
#             # Send Error 400
#             messdict = {'code': 0,
#                         'message': 'Wrong formatted NSLC code (%s).' % nslc}
#             message = json.dumps(messdict)
#             self.log.error(message)
#             cherrypy.response.headers['Content-Type'] = 'application/json'
#             raise cherrypy.HTTPError(400, message)
#
#         if starttime is not None:
#             try:
#                 str2date(starttime)
#             except Exception:
#                 # Send Error 400
#                 messdict = {'code': 0,
#                             'message': 'Error converting the "starttime" parameter (%s).' % starttime}
#                 message = json.dumps(messdict)
#                 self.log.error(message)
#                 cherrypy.response.headers['Content-Type'] = 'application/json'
#                 raise cherrypy.HTTPError(400, message)
#
#         if endtime is not None:
#             try:
#                 str2date(endtime)
#             except Exception:
#                 # Send Error 400
#                 messdict = {'code': 0,
#                             'message': 'Error converting the "endtime" parameter (%s).' % endtime}
#                 message = json.dumps(messdict)
#                 self.log.error(message)
#                 cherrypy.response.headers['Content-Type'] = 'application/json'
#                 raise cherrypy.HTTPError(400, message)
#
#         # Check if network is restricted
#         whereclause = ['code=%s']
#         variables = [nslc2[0]]
#
#         if starttime is not None:
#             whereclause.append('start<=%s')
#             variables.append(starttime)
#
#         if endtime is not None:
#             whereclause.append('(end>=%s or end is NULL)')
#             variables.append(endtime)
#
#         # self.cursor = self.conn.cursor()
#         query = 'select distinct restricted from Network where '
#         query = query + ' and '.join(whereclause)
#
#         self.conn.execute(query, variables)
#         result = self.conn.fetchall()
#
#         if len(result) != 1:
#             if len(result):
#                 mess = 'Restricted and non-restricted streams found. More filters are needed.'
#             else:
#                 mess = 'Network not found!'
#             # Send Error 400
#             messdict = {'code': 0,
#                         'message': mess}
#             message = json.dumps(messdict)
#             self.log.error(message)
#             cherrypy.response.headers['Content-Type'] = 'application/json'
#             raise cherrypy.HTTPError(400, message)
#
#         if (result[0] is not None) and (result[0]['restricted'] == 0):
#             cherrypy.response.headers['Content-Type'] = 'text/plain'
#             return ''.encode('utf-8')
#
#         # Check network access
#         if self.__access(email, net=nslc2[0], starttime=starttime, endtime=endtime):
#             cherrypy.response.headers['Content-Type'] = 'text/plain'
#             return ''.encode('utf-8')
#
#         # Check station access
#         if len(nslc2[1]) and self.__access(email, net=nslc2[0], sta=nslc2[1], starttime=starttime, endtime=endtime):
#             cherrypy.response.headers['Content-Type'] = 'text/plain'
#             return ''.encode('utf-8')
#
#         # Check channel access
#         if len(nslc2[3]) and self.__access(email, net=nslc2[0], sta=nslc2[1], loc=nslc2[2], cha=nslc2[3],
#                                            starttime=starttime, endtime=endtime):
#             cherrypy.response.headers['Content-Type'] = 'text/plain'
#             return ''.encode('utf-8')
#
#         # Send Error 403
#         messdict = {'code': 0,
#                     'message': 'Access to {} denied for {}.'.format(nslc, email)}
#         message = json.dumps(messdict)
#         self.log.error(message)
#         cherrypy.response.headers['Content-Type'] = 'application/json'
#         raise cherrypy.HTTPError(403, message)
#
#
# @cherrypy.expose
# @cherrypy.popargs('net', 'sta')
# class StationsAPI(object):
#     """Object dispatching methods related to stations."""
#
#     def __init__(self, host: str, user: str, password: str, db: str):
#         """Constructor of the StationsAPI class."""
#         # Save connection
#         self.conn = SC3dbconnection(host, user, password, db)
#         self.log = logging.getLogger('StationsAPI')
#
#         # Get extra fields from the cfg file
#         cfgfile = configparser.RawConfigParser()
#         cfgfile.read('sc3microapi.cfg')
#
#         # extrafields = cfgfile.get('Service', 'station', fallback='')
#         # self.extrafields = extrafields.split(',') if len(extrafields) else []
#         # self.stasuppl = configparser.RawConfigParser()
#         # self.stasuppl.read('stations.cfg')
#
#     @cherrypy.expose
#     def index(self, net: NetworkCode = None, sta: StationCode = None,
#               outformat: Literal['json', 'text', 'xml'] = 'json', restricted: Literal['0', '1'] = None,
#               archive: str = None, shared: Literal['0', '1'] = None, starttime: str = None, endtime: str = None,
#               **kwargs) -> bytes:
#         """List available stations in the system.
#
#         :param net: Network code
#         :type net: str
#         :param sta: Station code
#         :type sta: str
#         :param outformat: Output format (json, text, xml)
#         :type outformat: str
#         :param restricted: Restricted status of the Station ('0' or '1')
#         :type restricted: str
#         :param archive: Institution archiving the station
#         :type archive: str
#         :param shared: Is the network shared with EIDA? ('0' or '1')
#         :type shared: str
#         :param starttime: Start time in isoformat
#         :type starttime: str
#         :param endtime: End time in isoformat
#         :type endtime: str
#         :returns: Data related to the available stations.
#         :rtype: utf-8 encoded string
#         :raises: cherrypy.HTTPError
#         """
#
#         if len(kwargs):
#             # Send Error 400
#             messdict = {'code': 0,
#                         'message': 'Unknown parameter(s) "{}".'.format(kwargs.items())}
#             message = json.dumps(messdict)
#             self.log.error(message)
#             raise cherrypy.HTTPError(400, message)
#
#         # Check parameters
#         if restricted is not None:
#             restricted = int(restricted)
#             # except Exception:
#             #     # Send Error 400
#             #     messdict = {'code': 0,
#             #                 'message': 'Restricted does not seem to be 0 or 1.'}
#             #     message = json.dumps(messdict)
#             #     self.log.error(message)
#             #     raise cherrypy.HTTPError(400, message)
#
#         # Check parameters
#         if shared is not None:
#             shared = int(shared)
#             # except Exception:
#             #     # Send Error 400
#             #     messdict = {'code': 0,
#             #                 'message': 'Shared does not seem to be 0 or 1.'}
#             #     message = json.dumps(messdict)
#             #     self.log.error(message)
#             #     raise cherrypy.HTTPError(400, message)
#
#         # if outformat not in ['json', 'text', 'xml']:
#         #     # Send Error 400
#         #     messdict = {'code': 0,
#         #                 'message': 'Wrong value in the "outformat" parameter.'}
#         #     message = json.dumps(messdict)
#         #     self.log.error(message)
#         #     raise cherrypy.HTTPError(400, message)
#
#         if starttime is not None:
#             try:
#                 str2date(starttime)
#             except Exception:
#                 # Send Error 400
#                 messdict = {'code': 0,
#                             'message': 'Error converting the "starttime" parameter (%s).' % starttime}
#                 message = json.dumps(messdict)
#                 self.log.error(message)
#                 raise cherrypy.HTTPError(400, message)
#
#         if endtime is not None:
#             try:
#                 str2date(endtime)
#             except Exception:
#                 # Send Error 400
#                 messdict = {'code': 0,
#                             'message': 'Error converting the "endtime" parameter (%s).' % endtime}
#                 message = json.dumps(messdict)
#                 self.log.error(message)
#                 raise cherrypy.HTTPError(400, message)
#
#         # try:
#         query = ('select N.code as network, S.code as code, latitude, longitude, '
#                  'elevation, place, country, S.start, S.end, S.restricted, S.shared '
#                  'from Station as S join Network as N')
#         fields = ['network', 'code', 'latitude', 'longitude', 'elevation',
#                   'place', 'country', 'start', 'end', 'restricted', 'shared']
#         # fields.extend(self.extrafields)
#
#         whereclause = ['S._parent_oid=N._oid']
#         variables = []
#         if net is not None:
#             if net[0] in '0123456789XYZ':
#                 try:
#                     net, year = net.split('_')
#                 except ValueError:
#                     # Send Error 400
#                     messdict = {'code': 0,
#                                 'message': 'Wrong network code (%s). Temporary codes must include the start year (e.g. 4C_2011).' % net}
#                     message = json.dumps(messdict)
#                     self.log.error(message)
#                     raise cherrypy.HTTPError(400, message)
#
#                 whereclause.append('YEAR(N.start)=%s')
#                 variables.append(int(year))
#
#             whereclause.append('N.code=%s')
#             variables.append(net)
#
#         if sta is not None:
#             whereclause.append('S.code=%s')
#             variables.append(sta)
#
#         if restricted is not None:
#             whereclause.append('S.restricted=%s')
#             variables.append(restricted)
#
#         if archive is not None:
#             whereclause.append('S.archive=%s')
#             variables.append(archive)
#
#         if shared is not None:
#             whereclause.append('S.shared=%s')
#             variables.append(shared)
#
#         if starttime is not None:
#             whereclause.append('S.start>=%s')
#             variables.append(starttime)
#
#         if endtime is not None:
#             whereclause.append('S.end<=%s')
#             variables.append(endtime)
#
#         if len(whereclause):
#             query = query + ' where ' + ' and '.join(whereclause)
#
#         # self.cursor = self.conn.cursor()
#         self.conn.execute(query, variables)
#
#         # Complete SC3 data with local data
#         result = self.conn.fetchall()
#         # cursta = self.conn.fetchall()
#
#         if outformat == 'json':
#             cherrypy.response.headers['Content-Type'] = 'application/json'
#
#             return json.dumps(result, default=datetime.datetime.isoformat).encode('utf-8')
#         elif outformat == 'text':
#             cherrypy.response.headers['Content-Type'] = 'text/plain'
#
#             fout = io.StringIO("")
#             writer = csv.DictWriter(fout, fieldnames=fields, delimiter='|')
#             writer.writeheader()
#             writer.writerows(result)
#             fout.seek(0)
#             cherrypy.response.headers['Content-Type'] = 'text/plain'
#             return fout.read().encode('utf-8')
#         elif outformat == 'xml':
#             cherrypy.response.headers['Content-Type'] = 'application/xml'
#
#             header = """<?xml version="1.0" encoding="utf-8"?>
#   <ns0:routing xmlns:ns0="http://geofon.gfz-potsdam.de/ns/Routing/1.0/">
#             """
#             footer = """</ns0:routing>"""
#
#             outxml = [header]
#             for sta in result:
#                 routetext = """
#  <ns0:route networkCode="{netcode}" stationCode="{stacode}" locationCode="*" streamCode="*">
#   <ns0:station address="https://geofon.gfz-potsdam.de/fdsnws/station/1/query" priority="1" start="{stastart}" end="{staend}" />
#   <ns0:wfcatalog address="https://geofon.gfz-potsdam.de/eidaws/wfcatalog/1/query" priority="1" start="{stastart}" end="{staend}" />
#   <ns0:dataselect address="https://geofon.gfz-potsdam.de/fdsnws/dataselect/1/query" priority="1" start="{stastart}" end="{staend}" />
#   <ns0:availability address="https://geofon.gfz-potsdam.de/fdsnws/availability/1/query" priority="1" start="{stastart}" end="{staend}" />
#  </ns0:route>
#  """
#                 nc = sta['network']
#                 sc = sta['code']
#                 ss = sta['start'].isoformat()
#                 se = sta['end'].isoformat() if sta['end'] is not None else ''
#                 outxml.append(routetext.format(netcode=nc, stacode=sc, stastart=ss, staend=se))
#             outxml.append(footer)
#             return ''.join(outxml).encode('utf-8')
#
#
# @cherrypy.expose
# @cherrypy.popargs('net')
# class NetworksAPI(object):
#     """Object dispatching methods related to networks."""
#
#     def __init__(self, host: str, user: str, password: str, db: str):
#         """Constructor of the NetworksAPI class."""
#         # Save connection
#         self.conn = SC3dbconnection(host, user, password, db)
#         self.log = logging.getLogger('NetworksAPI')
#
#         # Get extra fields from the cfg file
#         cfgfile = configparser.RawConfigParser()
#         cfgfile.read('sc3microapi.cfg')
#
#         extrafields = cfgfile.get('Service', 'network', fallback='')
#         self.extrafields = extrafields.split(',') if len(extrafields) else []
#         self.netsuppl = configparser.RawConfigParser()
#         self.netsuppl.read('networks.cfg')
#
#     @cherrypy.expose
#     def index(self, net: NetworkCode = None, outformat: Literal['text', 'json', 'xml'] = 'json',
#               restricted: Literal['0', '1'] = None, archive: str = None, netclass: Literal['p', 't'] = None,
#               shared: Literal['0', '1'] = None, starttime: str = None, endtime: str = None, **kwargs) -> bytes:
#         """List available networks in the system.
#
#         :param net: Network code
#         :type net: str
#         :param outformat: Output format (json, text, xml)
#         :type outformat: str
#         :param restricted: Restricted status of the Network ('0' or '1')
#         :type restricted: str
#         :param archive: Institution archiving the network
#         :type archive: str
#         :param netclass: Tpye of network (permanent 'p' or temporary 't')
#         :type netclass: str
#         :param shared: Is the network shared with EIDA? ('0' or '1')
#         :type shared: str
#         :param starttime: Start time in isoformat
#         :type starttime: str
#         :param endtime: End time in isoformat
#         :type endtime: str
#         :returns: Data related to the available networks.
#         :rtype: utf-8 encoded string
#         :raises: cherrypy.HTTPError
#         """
#
#         if len(kwargs):
#             # Send Error 400
#             messdict = {'code': 0,
#                         'message': 'Unknown parameter(s) "{}".'.format(kwargs.items())}
#             message = json.dumps(messdict)
#             self.log.error(message)
#             raise cherrypy.HTTPError(400, message)
#
#         # Check parameters
#         if restricted is not None:
#             restricted = int(restricted)
#             # except Exception:
#             #     # Send Error 400
#             #     messdict = {'code': 0,
#             #                 'message': 'Restricted does not seem to be 0 or 1.'}
#             #     message = json.dumps(messdict)
#             #     self.log.error(message)
#             #     raise cherrypy.HTTPError(400, message)
#
#         # Check parameters
#         if shared is not None:
#             shared = int(shared)
#             # except Exception:
#             #     # Send Error 400
#             #     messdict = {'code': 0,
#             #                 'message': 'Shared does not seem to be 0 or 1.'}
#             #     message = json.dumps(messdict)
#             #     self.log.error(message)
#             #     raise cherrypy.HTTPError(400, message)
#
#         # if outformat not in ['json', 'text', 'xml']:
#         #     # Send Error 400
#         #     messdict = {'code': 0,
#         #                 'message': 'Wrong value in the "outformat" parameter.'}
#         #     message = json.dumps(messdict)
#         #     self.log.error(message)
#         #     raise cherrypy.HTTPError(400, message)
#
#         if starttime is not None:
#             try:
#                 str2date(starttime)
#             except Exception:
#                 # Send Error 400
#                 messdict = {'code': 0,
#                             'message': 'Error converting the "starttime" parameter (%s).' % starttime}
#                 message = json.dumps(messdict)
#                 self.log.error(message)
#                 raise cherrypy.HTTPError(400, message)
#
#         if endtime is not None:
#             try:
#                 str2date(endtime)
#             except Exception:
#                 # Send Error 400
#                 messdict = {'code': 0,
#                             'message': 'Error converting the "endtime" parameter (%s).' % endtime}
#                 message = json.dumps(messdict)
#                 self.log.error(message)
#                 raise cherrypy.HTTPError(400, message)
#
#         # try:
#         query = 'select code, start, end, netClass, archive, restricted, shared from Network'
#         fields = ['code', 'start', 'end', 'netClass', 'archive', 'restricted', 'shared']
#         fields.extend(self.extrafields)
#
#         whereclause = []
#         variables = []
#         if net is not None:
#             if net[0] in '0123456789XYZ':
#                 try:
#                     net, year = net.split('_')
#                 except ValueError:
#                     # Send Error 400
#                     messdict = {'code': 0,
#                                 'message': 'Wrong network code (%s). Temporary codes must include the start year (e.g. 4C_2011).' % net}
#                     message = json.dumps(messdict)
#                     self.log.error(message)
#                     raise cherrypy.HTTPError(400, message)
#
#                 whereclause.append('YEAR(start)=%s')
#                 variables.append(int(year))
#
#             whereclause.append('code=%s')
#             variables.append(net)
#
#         if restricted is not None:
#             whereclause.append('restricted=%s')
#             variables.append(restricted)
#
#         if archive is not None:
#             whereclause.append('archive=%s')
#             variables.append(archive)
#
#         if netclass is not None:
#             whereclause.append('netClass=%s')
#             variables.append(netclass)
#
#         if shared is not None:
#             whereclause.append('shared=%s')
#             variables.append(shared)
#
#         if starttime is not None:
#             whereclause.append('start>=%s')
#             variables.append(starttime)
#
#         if endtime is not None:
#             whereclause.append('end<=%s')
#             variables.append(endtime)
#
#         if len(whereclause):
#             query = query + ' where ' + ' and '.join(whereclause)
#
#         # self.cursor = self.conn.cursor()
#         self.conn.execute(query, variables)
#
#         # Complete SC3 data with local data
#         result = []
#         curnet = self.conn.fetchone()
#         while curnet:
#             for field in self.extrafields:
#                 curnet[field] = self.netsuppl.get(curnet['code'] + '-' + str(curnet['start'].year),
#                                                   field, fallback=None)
#             result.append(curnet)
#             curnet = self.conn.fetchone()
#
#         if outformat == 'json':
#             cherrypy.response.headers['Content-Type'] = 'application/json'
#
#             return json.dumps(result, default=datetime.datetime.isoformat).encode('utf-8')
#         elif outformat == 'text':
#             cherrypy.response.headers['Content-Type'] = 'text/plain'
#
#             fout = io.StringIO("")
#             writer = csv.DictWriter(fout, fieldnames=fields, delimiter='|')
#             writer.writeheader()
#             writer.writerows(result)
#             fout.seek(0)
#             cherrypy.response.headers['Content-Type'] = 'text/plain'
#             return fout.read().encode('utf-8')
#         elif outformat == 'xml':
#             cherrypy.response.headers['Content-Type'] = 'application/xml'
#
#             header = """<?xml version="1.0" encoding="utf-8"?>
#   <ns0:routing xmlns:ns0="http://geofon.gfz-potsdam.de/ns/Routing/1.0/">
#             """
#             footer = """</ns0:routing>"""
#
#             outxml = [header]
#             for net in result:
#                 routetext = """
#  <ns0:route networkCode="{netcode}" stationCode="*" locationCode="*" streamCode="*">
#   <ns0:station address="https://geofon.gfz-potsdam.de/fdsnws/station/1/query" priority="1" start="{netstart}" end="{netend}" />
#   <ns0:wfcatalog address="https://geofon.gfz-potsdam.de/eidaws/wfcatalog/1/query" priority="1" start="{netstart}" end="{netend}" />
#   <ns0:dataselect address="https://geofon.gfz-potsdam.de/fdsnws/dataselect/1/query" priority="1" start="{netstart}" end="{netend}" />
#   <ns0:availability address="https://geofon.gfz-potsdam.de/fdsnws/availability/1/query" priority="1" start="{netstart}" end="{netend}" />
#  </ns0:route>
#  """
#                 nc = net['code']
#                 ns = net['start'].isoformat()
#                 ne = net['end'].isoformat() if net['end'] is not None else ''
#                 outxml.append(routetext.format(netcode=nc, netstart=ns, netend=ne))
#             outxml.append(footer)
#             return ''.join(outxml).encode('utf-8')
#
#         # except:
#         #     # Send Error 404
#         #     messDict = {'code': 0,
#         #                 'message': 'Could not query the available networks'}
#         #     message = json.dumps(messDict)
#         #     self.log.error(message)
#         #     raise cherrypy.HTTPError(404, message)
#
#
# @cherrypy.expose
# @cherrypy.popargs('net')
# class VirtualNetsAPI(object):
#     """Object dispatching methods related to virtual networks."""
#
#     def __init__(self, host: str, user: str, password: str, db: str):
#         """Constructor of the NetworksAPI class."""
#         # Save connection
#         self.conn = SC3dbconnection(host, user, password, db)
#         self.log = logging.getLogger('VirtualNetAPI')
#
#         # Get extra fields from the cfg file
#         cfgfile = configparser.RawConfigParser()
#         cfgfile.read('sc3microapi.cfg')
#
#     @cherrypy.expose
#     def index(self, net: NetworkCode = None, outformat: Literal['text', 'json', 'xml'] = 'json',
#               typevn: str = None, starttime: str = None, endtime: str = None, **kwargs) -> bytes:
#         """List available networks in the system.
#
#         :param net: Network code
#         :type net: str
#         :param outformat: Output format (json, text)
#         :type outformat: str
#         :param typevn: Type of virtual network
#         :type typevn: str
#         :param starttime: Start time in isoformat
#         :type starttime: str
#         :param endtime: End time in isoformat
#         :type endtime: str
#         :returns: Data related to the available networks.
#         :rtype: utf-8 encoded string
#         :raises: cherrypy.HTTPError
#         """
#
#         if len(kwargs):
#             # Send Error 400
#             messdict = {'code': 0,
#                         'message': 'Unknown parameter(s) "{}".'.format(kwargs.items())}
#             message = json.dumps(messdict)
#             self.log.error(message)
#             raise cherrypy.HTTPError(400, message)
#
#         cherrypy.response.headers['Content-Type'] = 'application/json'
#
#         # try:
#         #     if outformat not in ['json', 'text', 'xml']:
#         #         raise Exception
#         # except Exception:
#         #     # Send Error 400
#         #     messdict = {'code': 0,
#         #                 'message': 'Wrong value in the "outformat" parameter.'}
#         #     message = json.dumps(messdict)
#         #     self.log.error(message)
#         #     raise cherrypy.HTTPError(400, message)
#
#         if starttime is not None:
#             try:
#                 str2date(starttime)
#             except Exception:
#                 # Send Error 400
#                 messdict = {'code': 0,
#                             'message': 'Error converting the "starttime" parameter (%s).' % starttime}
#                 message = json.dumps(messdict)
#                 self.log.error(message)
#                 raise cherrypy.HTTPError(400, message)
#
#         if endtime is not None:
#             try:
#                 str2date(endtime)
#             except Exception:
#                 # Send Error 400
#                 messdict = {'code': 0,
#                             'message': 'Error converting the "endtime" parameter (%s).' % endtime}
#                 message = json.dumps(messdict)
#                 self.log.error(message)
#                 raise cherrypy.HTTPError(400, message)
#
#         # try:
#         query = 'select code, start, end, type from StationGroup'
#         fields = ['code', 'start', 'end', 'type']
#
#         whereclause = []
#         variables = []
#         if net is not None:
#             whereclause.append('code=%s')
#             variables.append(net)
#
#         if typevn is not None:
#             whereclause.append('type=%s')
#             variables.append(typevn)
#
#         if starttime is not None:
#             whereclause.append('start>=%s')
#             variables.append(starttime)
#
#         if endtime is not None:
#             whereclause.append('end<=%s')
#             variables.append(endtime)
#
#         if len(whereclause):
#             query = query + ' where ' + ' and '.join(whereclause)
#
#         # self.cursor = self.conn.cursor()
#         self.conn.execute(query, variables)
#
#         # Retrieve all virtual networks
#         result = self.conn.fetchall()
#
#         if outformat == 'json':
#             return json.dumps(result,
#                               default=datetime.datetime.isoformat).encode('utf-8')
#         elif outformat == 'text':
#             fout = io.StringIO("")
#             writer = csv.DictWriter(fout, fieldnames=fields, delimiter='|')
#             writer.writeheader()
#             writer.writerows(result)
#             fout.seek(0)
#             cherrypy.response.headers['Content-Type'] = 'text/plain'
#             return fout.read().encode('utf-8')
#         elif outformat == 'xml':
#             cherrypy.response.headers['Content-Type'] = 'application/xml'
#
#             header = """<?xml version="1.0" encoding="utf-8"?>
#      <ns0:routing xmlns:ns0="http://geofon.gfz-potsdam.de/ns/Routing/1.0/">
#                """
#             footer = """</ns0:routing>"""
#
#             outxml = [header]
#             for vn in result:
#                 routetext = """
#     <ns0:vnetwork networkCode="{vncode}">
#     </ns0:vnetwork>
#     """
#                 vncode = vn['code']
#                 outxml.append(routetext.format(vncode=vncode))
#             outxml.append(footer)
#             return ''.join(outxml).encode('utf-8')
#
#     @cherrypy.expose
#     def stations(self, net: NetworkCode, outformat: Literal['text', 'json', 'xml'] = 'json', **kwargs) -> bytes:
#         """List available networks in the system.
#
#         :param net: Network code
#         :type net: str
#         :param outformat: Output format (json, text, xml)
#         :type outformat: str
#         :returns: List of stations in the virtual network.
#         :rtype: utf-8 encoded string
#         :raises: cherrypy.HTTPError
#         """
#
#         if len(kwargs):
#             # Send Error 400
#             messdict = {'code': 0,
#                         'message': 'Unknown parameter(s) "{}".'.format(kwargs.items())}
#             message = json.dumps(messdict)
#             self.log.error(message)
#             raise cherrypy.HTTPError(400, message)
#
#         cherrypy.response.headers['Content-Type'] = 'application/json'
#
#         # try:
#         #     if outformat not in ['json', 'text', 'xml']:
#         #         raise Exception
#         # except Exception:
#         #     # Send Error 400
#         #     messdict = {'code': 0,
#         #                 'message': 'Wrong value in the "outformat" parameter.'}
#         #     message = json.dumps(messdict)
#         #     self.log.error(message)
#         #     raise cherrypy.HTTPError(400, message)
#
#         # try:
#         query = 'select ne.code as network, st.code as station, st.start as start, st.end as end ' + \
#             'from StationGroup as sg join StationReference as sr join PublicObject as po ' + \
#             'join Station as st join  Network as ne'
#
#         fields = ['network', 'station', 'start', 'end']
#
#         whereclause = ['sg._oid = sr._parent_oid',
#                        'po.publicID = sr.stationID',
#                        'st._oid = po._oid',
#                        'st._parent_oid = ne._oid']
#         variables = []
#         whereclause.append('sg.code=%s')
#         variables.append(net)
#
#         if len(whereclause):
#             query = query + ' where ' + ' and '.join(whereclause)
#
#         # self.cursor = self.conn.cursor()
#         self.conn.execute(query, variables)
#
#         # Retrieve all VNs
#         result = self.conn.fetchall()
#
#         if outformat == 'json':
#             return json.dumps(result,
#                               default=datetime.datetime.isoformat).encode('utf-8')
#         elif outformat == 'text':
#             fout = io.StringIO("")
#             writer = csv.DictWriter(fout, fieldnames=fields, delimiter='|')
#             writer.writeheader()
#             writer.writerows(result)
#             fout.seek(0)
#             cherrypy.response.headers['Content-Type'] = 'text/plain'
#             return fout.read().encode('utf-8')
#         elif outformat == 'xml':
#             cherrypy.response.headers['Content-Type'] = 'application/xml'
#
#             header = """<?xml version="1.0" encoding="utf-8"?>
#      <ns0:routing xmlns:ns0="http://geofon.gfz-potsdam.de/ns/Routing/1.0/">
#      <ns0:vnetwork networkCode="%s">
#                """
#             footer = """</ns0:vnetwork>\n</ns0:routing>"""
#
#             outxml = [header % net]
#             for stream in result:
#                 streamtext = '<ns0:stream networkCode="{netcode}" stationCode="{stacode}" locationCode="*" streamCode="*" start="{starttime}" end="{endtime}" />\n'
#                 netcode = stream['network']
#                 stacode = stream['station']
#                 starttime = stream['start']
#                 try:
#                     str2date(stream['end'])
#                     endtime = stream['end']
#                 except Exception:
#                     endtime = ''
#                 outxml.append(streamtext.format(netcode=netcode, stacode=stacode, starttime=starttime, endtime=endtime))
#             outxml.append(footer)
#             return ''.join(outxml).encode('utf-8')
#
#
# class SC3MicroApi(object):
#     """Main class including the dispatcher."""
#
#     def __init__(self, host: str, user: str, password: str, db: str):
#         """Constructor of the SC3MicroApi object."""
#         # config = configparser.RawConfigParser()
#         # here = os.path.dirname(__file__)
#         # config.read(os.path.join(here, 'sc3microapi.cfg'))
#
#         self.network = NetworksAPI(host, user, password, db)
#         self.station = StationsAPI(host, user, password, db)
#         self.virtualnet = VirtualNetsAPI(host, user, password, db)
#         self.access = AccessAPI(host, user, password, db)
#         self.log = logging.getLogger('SC3MicroAPI')
#
#     @cherrypy.expose
#     def index(self) -> bytes:
#         cherrypy.response.headers['Content-Type'] = 'text/html'
#
#         # TODO Create an HTML page with a minimum documentation for a user
#         try:
#             with open('help.html') as fin:
#                 texthelp = fin.read()
#         except FileNotFoundError:
#             texthelp = """<html>
#                             <head>sc3microapi</head>
#                             <body>
#                               Default help for the sc3microapi service (GEOFON).
#                             </body>
#                           </html>"""
#         return texthelp.encode('utf-8')
#
#     @cherrypy.expose
#     def version(self) -> bytes:
#         """Return the version of this implementation.
#
#         :returns: Version of the system
#         :rtype: string
#         """
#         version = __version__
#         cherrypy.response.headers['Content-Type'] = 'text/plain'
#         return version.encode('utf-8')


# def main():
#     """Establishing the connection to the DB."""
#     config = configparser.RawConfigParser()
#     here = os.path.dirname(__file__)
#     config.read(os.path.join(here, 'sc3microapi.cfg'))
#
#     # Read connection parameters
#     host = config.get('mysql', 'host')
#     user = config.get('mysql', 'user')
#     password = config.get('mysql', 'password')
#     db = config.get('mysql', 'db')
#
#     server_config = {
#         'global': {
#             'tools.proxy.on': True,
#             'server.socket_host': 'localhost',
#             'server.socket_port': 7000,
#             'engine.autoreload_on': False
#         }
#     }
#     # Update the global CherryPy configuration
#     cherrypy.config.update(server_config)
#     cherrypy.tree.mount(SC3MicroApi(host, user, password, db), '/sc3microapi')
#
#     plugins.Daemonizer(cherrypy.engine).subscribe()
#     if hasattr(cherrypy.engine, 'signal_handler'):
#         cherrypy.engine.signal_handler.subscribe()
#     if hasattr(cherrypy.engine, 'console_control_handler'):
#         cherrypy.engine.console_control_handler.subscribe()
#
#     # Always start the engine; this will start all other services
#     try:
#         cherrypy.engine.start()
#     except Exception:
#         # Assume the error has been logged already via bus.log.
#         raise
#     else:
#         cherrypy.engine.block()
