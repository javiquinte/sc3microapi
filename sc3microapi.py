#!/usr/bin/env python3
#
# sc3microapi WS - prototype
#
# (c) 2017 Javier Quinteros, GEOFON team
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


import cherrypy
import os
import io
import csv
import json
import MySQLdb
from MySQLdb.cursors import DictCursor
import logging
import logging.config
import datetime

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

# Logging configuration (hardcoded!)
LOG_CONF = {
    'version': 1,

    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'sc3microapilog': {
            'level':'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': os.path.join(os.path.expanduser('~'), '.sc3microapi', 'sc3microapi.log'),
            'maxBytes': 10485760,
            'backupCount': 20,
            'encoding': 'utf8'
        },
        'cherrypyAccess': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'standard',
            'filename': os.path.join(os.path.expanduser('~'), '.sc3microapi', 'access.log'),
            'maxBytes': 10485760,
            'backupCount': 20,
            'encoding': 'utf8'
        },
    },
    'loggers': {
        'main': {
            'handlers': ['sc3microapilog'],
            'level': 'INFO'
        },
        'AccessAPI': {
            'handlers': ['sc3microapilog'],
            'level': 'INFO' ,
            'propagate': False
        },
        'NetworksAPI': {
            'handlers': ['sc3microapilog'],
            'level': 'INFO',
            'propagate': False
        },
        'SC3MicroAPI': {
            'handlers': ['sc3microapilog'],
            'level': 'INFO',
            'propagate': False
        },
        'cherrypy.access': {
            'handlers': ['cherrypyAccess'],
            'level': 'INFO',
            'propagate': False
        },
    }
}


def str2date(dStr):
    """Transform a string to a datetime.

    :param dStr: A datetime in ISO format.
    :type dStr: string
    :return: A datetime represented the converted input.
    :rtype: datetime
    """
    # In case of empty string
    if not len(dStr):
        return None

    dateParts = dStr.replace('-', ' ').replace('T', ' ')
    dateParts = dateParts.replace(':', ' ').replace('.', ' ')
    dateParts = dateParts.replace('Z', '').split()
    return datetime.datetime(*map(int, dateParts))


@cherrypy.expose
class AccessAPI(object):
    """Object dispatching methods related to access to streams."""

    def __init__(self, conn):
        """Constructor of the AccessAPI class."""
        self.conn = conn
        self.log = logging.getLogger('AccessAPI')

    def __access(self, email, net='', sta='', loc='', cha='', starttime=None, endtime=None):
        # Check network access
        self.cursor = self.conn.cursor()
        whereclause = ['networkCode=%s',
                       'stationCode=%s',
                       'locationCode=%s',
                       'streamCode=%s',
                       '%s LIKE concat("%%", user, "%%")']
        variables = [net, sta, loc, cha, email]

        if (starttime is not None):
            whereclause.append('start<=%s')
            variables.append(starttime)

        if (endtime is not None):
            whereclause.append('(end>=%s or end is NULL)')
            variables.append(endtime)

        query = 'select count(*) from Access where ' + ' and '.join(whereclause)
        self.cursor.execute(query, variables)
        result = self.cursor.fetchone()

        if (result is not None):
            return result[0]

        raise Exception('No result querying the DB ({})'.format(query % variables))

    @cherrypy.expose
    def index(self, nslc, email, starttime=None, endtime=None):
        """Check if the user has access to a stream.

        :param nslc: Network.Station.Location.Channel
        :param type: str
        :returns: Data related to the available networks.
        :rtype: utf-8 encoded string
        :raises: cherrypy.HTTPError
        """

        # Check parameters
        try:
            auxnslc = nslc.split('.')
            nslc2 = [auxnslc[pos] if len(auxnslc) > pos else '' for pos in range(4)]
            if len(nslc2) != 4:
                raise Exception
        except:
            # Send Error 400
            messDict = {'code': 0,
                        'message': 'Wrong formatted NSLC code (%s).' % nslc}
            message = json.dumps(messDict)
            self.log.error(message)
            cherrypy.response.headers['Content-Type'] = 'application/json'
            raise cherrypy.HTTPError(400, message)

        if starttime is not None:
            try:
                startt = str2date(starttime)
            except:
                # Send Error 400
                messDict = {'code': 0,
                            'message': 'Error converting the "starttime" parameter (%s).' % starttime}
                message = json.dumps(messDict)
                self.log.error(message)
                cherrypy.response.headers['Content-Type'] = 'application/json'
                raise cherrypy.HTTPError(400, message)

        if endtime is not None:
            try:
                endt = str2date(endtime)
            except:
                # Send Error 400
                messDict = {'code': 0,
                            'message': 'Error converting the "endtime" parameter (%s).' % endtime}
                message = json.dumps(messDict)
                self.log.error(message)
                cherrypy.response.headers['Content-Type'] = 'application/json'
                raise cherrypy.HTTPError(400, message)

        # Check if network is restricted
        whereclause = ['code=%s']
        variables = [nslc2[0]]

        if starttime is not None:
            whereclause.append('start<=%s')
            variables.append(starttime)

        if endtime is not None:
            whereclause.append('(end>=%s or end is NULL)')
            variables.append(endtime)

        self.cursor = self.conn.cursor()
        query = 'select distinct restricted from Network where '
        query = query + ' and '.join(whereclause)

        self.cursor.execute(query, variables)
        result = self.cursor.fetchall()
        if len(result) != 1:
            if len(result):
                mess = 'Restricted and non-restricted streams found. More filters are needed.'
            else:
                mess = 'Network not found!'
            # Send Error 400
            messDict = {'code': 0,
                        'message': mess}
            message = json.dumps(messDict)
            self.log.error(message)
            cherrypy.response.headers['Content-Type'] = 'application/json'
            raise cherrypy.HTTPError(400, message)

        if (result[0] is not None) and (result[0][0] == 0):
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            return ''.encode('utf-8')

        # Check network access
        if self.__access(email, net=nslc2[0], starttime=starttime, endtime=endtime) :
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            return ''.encode('utf-8')

        # Check station access
        if len(nslc2[1]) and self.__access(email, net=nslc2[0], sta=nslc2[1], starttime=starttime, endtime=endtime):
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            return ''.encode('utf-8')

        # Check channel access
        if len(nslc2[3]) and self.__access(email, net=nslc2[0], sta=nslc2[1], loc=nslc2[2], cha=nslc2[3],
                         starttime=starttime, endtime=endtime) :
            cherrypy.response.headers['Content-Type'] = 'text/plain'
            return ''.encode('utf-8')

        # Send Error 403
        messDict = {'code': 0,
                    'message': 'Access to {} denied for {}.'.format(nslc, email)}
        message = json.dumps(messDict)
        self.log.error(message)
        cherrypy.response.headers['Content-Type'] = 'application/json'
        raise cherrypy.HTTPError(403, message)


@cherrypy.expose
@cherrypy.popargs('net')
class NetworksAPI(object):
    """Object dispatching methods related to networks."""

    def __init__(self, conn):
        """Constructor of the IngestAPI class."""
        self.conn = conn
        self.log = logging.getLogger('NetworksAPI')

        # Get extra fields from the cfg file
        cfgfile = configparser.RawConfigParser()
        cfgfile.read('sc3microapi.cfg')

        extrafields = cfgfile.get('Service', 'network', fallback='')
        self.extrafields = extrafields.split(',') if len(extrafields) else []
        self.netsuppl = configparser.RawConfigParser()
        self.netsuppl.read('networks.cfg')

    @cherrypy.expose
    def index(self, net=None, outformat='json', restricted=None, archive=None,
              netclass=None, starttime=None, endtime=None, **kwargs):
        """List available networks in the system.

        :param net: Network code
        :type net: str
        :param outformat: Output format (json, text)
        :type outformat: str
        :param restricted: Restricted status of the Network ('0' or '1')
        :type restricted: str
        :param archive: Institution archiving the network
        :type archive: str
        :param netclass: Tpye of network (permanent 'p' or temporary 't')
        :type netclass: str
        :param starttime: Start time in isoformat
        :type starttime: str
        :param endtime: End time in isoformat
        :type endtime: str
        :returns: Data related to the available networks.
        :rtype: utf-8 encoded string
        :raises: cherrypy.HTTPError
        """

        if len(kwargs):
            # Send Error 400
            messDict = {'code': 0,
                        'message': 'Unknown parameter(s) "{}".'.format(kwargs.items())}
            message = json.dumps(messDict)
            self.log.error(message)
            raise cherrypy.HTTPError(400, message)

        cherrypy.response.headers['Content-Type'] = 'application/json'

        # Check parameters
        if restricted is not None:
            try:
                restricted = int(restricted)
                if restricted not in [0, 1]:
                    raise Exception
            except:
                # Send Error 400
                messDict = {'code': 0,
                            'message': 'Restricted does not seem to be 0 or 1.'}
                message = json.dumps(messDict)
                self.log.error(message)
                raise cherrypy.HTTPError(400, message)

        try:
            if outformat not in ['json', 'text']:
                raise Exception
        except:
            # Send Error 400
            messDict = {'code': 0,
                        'message': 'Wrong value in the "format" parameter.'}
            message = json.dumps(messDict)
            self.log.error(message)
            raise cherrypy.HTTPError(400, message)

        if starttime is not None:
            try:
                startt = str2date(starttime)
            except:
                # Send Error 400
                messDict = {'code': 0,
                            'message': 'Error converting the "starttime" parameter (%s).' % starttime}
                message = json.dumps(messDict)
                self.log.error(message)
                raise cherrypy.HTTPError(400, message)

        if endtime is not None:
            try:
                endt = str2date(endtime)
            except:
                # Send Error 400
                messDict = {'code': 0,
                            'message': 'Error converting the "endtime" parameter (%s).' % endtime}
                message = json.dumps(messDict)
                self.log.error(message)
                raise cherrypy.HTTPError(400, message)

        try:
            self.cursor = self.conn.cursor()
            query = 'select code, start, end, netClass, archive, restricted from Network'
            fields = ['code', 'start', 'end', 'netClass', 'archive', 'restricted']
            fields.extend(self.extrafields)

            whereclause = []
            variables = []
            if net is not None:
                whereclause.append('code=%s')
                variables.append(net)

            if restricted is not None:
                whereclause.append('restricted=%d')
                variables.append(restricted)

            if archive is not None:
                whereclause.append('archive=%s')
                variables.append(archive)

            if netclass is not None:
                whereclause.append('netClass=%s')
                variables.append(netclass)

            if starttime is not None:
                whereclause.append('start>=%s')
                variables.append(starttime)

            if endtime is not None:
                whereclause.append('end<=%s')
                variables.append(endtime)

            if len(whereclause):
                query = query + ' where ' + ' and '.join(whereclause)

            self.cursor.execute(query, variables)

            # Complete SC3 data with local data
            result = []
            curnet = self.cursor.fetchone()
            if outformat == 'json':
                while curnet:
                    for field in self.extrafields:
                        curnet[field] = self.netsuppl.get(curnet['code'] + '-' + str(curnet['start'].year),
                                                          field, fallback=None)
                    result.append(curnet)
                    curnet = self.cursor.fetchone()

                return json.dumps(result, default=datetime.datetime.isoformat).encode('utf-8')
            elif outformat == 'text':
                fout = io.StringIO("")
                writer = csv.DictWriter(fout, fieldnames=fields, delimiter='|')
                writer.writeheader()

                while curnet:
                    for exfield in self.extrafields:
                        curnet[exfield] = self.netsuppl.get(curnet['code'] + '-' + str(curnet['start'].year),
                                                            exfield, fallback=None)
                    result.append(curnet)
                    curnet = self.cursor.fetchone()

                writer.writerows(result)
                fout.seek(0)
                cherrypy.response.headers['Content-Type'] = 'text/plain'
                return fout.read().encode('utf-8')
        except:
            # Send Error 404
            messDict = {'code': 0,
                        'message': 'Could not query the available networks'}
            message = json.dumps(messDict)
            self.log.error(message)
            raise cherrypy.HTTPError(404, message)


class SC3MicroApi(object):
    """Main class including the dispatcher."""

    def __init__(self, conn):
        """Constructor of the SC3MicroApi object."""
        # config = configparser.RawConfigParser()
        # here = os.path.dirname(__file__)
        # config.read(os.path.join(here, 'sc3microapi.cfg'))

        # Save connection
        self.conn = conn
        self.network = NetworksAPI(conn)
        self.access = AccessAPI(conn)
        self.log = logging.getLogger('SC3MicroAPI')

    @cherrypy.expose
    def index(self):
        cherrypy.response.headers['Content-Type'] = 'text/html'

        # TODO Create an HTML page with a minimum documentation for a user
        try:
            with open('help.html') as fin:
                texthelp = fin.read()
        except:
            texthelp = """<html>
                            <head>sc3microapi</head>
                            <body>
                              Default help for the sc3microapi service (GEOFON).
                            </body>
                          </html>"""

        return texthelp.encode('utf-8')

    @cherrypy.expose
    def version(self):
        """Return the version of this implementation.

        :returns: Version of the system
        :rtype: string
        """
        version = '0.1a1'
        cherrypy.response.headers['Content-Type'] = 'text/plain'
        return version.encode('utf-8')


def main():
    """Establishing the connection to the DB."""
    config = configparser.RawConfigParser()
    here = os.path.dirname(__file__)
    config.read(os.path.join(here, 'sc3microapi.cfg'))
    
    # Logging configuration
    for modname in ['main', 'NetworksAPI', 'AccessAPI', 'SC3MicroAPI']:
        verbo = config.get('Logging', modname) if config.has_option('Logging', modname) else 'INFO'
        verboNum = getattr(logging, verbo.upper(), 30)
        LOG_CONF['loggers'][modname]['level'] = verboNum

    logging.config.dictConfig(LOG_CONF)
    loclog = logging.getLogger('main')

    # Read connection parameters
    host = config.get('mysql', 'host')
    user = config.get('mysql', 'user')
    password = config.get('mysql', 'password')
    db = config.get('mysql', 'db')
    
    conn = MySQLdb.connect(host, user, password, db, cursorclass=DictCursor)
    
    server_config = {
        'global': {
            'tools.proxy.on': True,
            'server.socket_host': 'st27dmz.gfz-potsdam.de',
            'server.socket_port': 7000,
            'engine.autoreload_on': False
        }
    }
    # Update the global CherryPy configuration
    cherrypy.config.update(server_config)
    cherrypy.tree.mount(SC3MicroApi(conn), '/sc3microapi')
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()

if __name__ == "__main__":
    main()
    # cherrypy.engine.signals.subscribe()
    # cherrypy.engine.start()
    # cherrypy.engine.block()
