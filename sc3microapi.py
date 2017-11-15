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
import json
from typing import Dict, List, Tuple

try:
    import configparser
except ImportError:
    import ConfigParser as configparser


class TemplatesAPI(object):
    """Object dispatching methods related to templates."""

    def __init__(self, directory: str):
        """Constructor of the IngestAPI class."""
        self.directory = directory
        self.extension = 'n3'

    def retrieve(self, template: str, params: dict) -> str:
        """Fill a template with the parameters passed.

        :returns: Complete template in text plain format.
        :rtype: string
        :raises: FileNotFoundError, BadRequest
        """

        prefix: str = 'EUDAT_PARAM'

        with open(self.directory + '/' + template + '.' + self.extension) as fin:
            # Keep the specification in a list
            wholetemp: str = fin.read()
            for key, value in params.items():
                wholetemp = wholetemp.replace('{%s:%s}' % (prefix, key), value)

            # Check that all variables have been replaced

            # Look for opening markup of variable
            startvar: int = wholetemp.find('{%s:' % prefix)
            if startvar >= 0:
                # Look for closing markup of variable
                endvar: int = wholetemp.find('}', startvar)
                if endvar >= startvar:
                    raise Exception('Missing variable: %s' % wholetemp[startvar+len(prefix)+2:endvar])

            return wholetemp

    def list(self) -> str:
        """List available templates in the system.

        :returns: Metadata related to the available templates in JSON format.
        :rtype: string
        :raises: cherrypy.HTTPError
        """
        try:
            templates: List[str] = []
            for (dirpath, dirnames, filenames) in os.walk(self.directory):
                # Filter out files not ending with self.extension
                filenames = [fi[:-len(self.extension)-1] for fi in filenames if fi.endswith('.' + self.extension)]
                templates.extend(filenames)
                break
        except:
            # Send Error 404
            messDict: Dict = {'code': 0,
                              'message': 'Could not read the list of available templates'}
            message: str = json.dumps(messDict)
            cherrypy.log(message, traceback=True)
            cherrypy.response.headers['Content-Type'] = 'application/json'
            raise cherrypy.HTTPError(404, message)

        # Save the templates specification to be returned
        result: List[Dict[str, str]] = list()
        for template in templates:
            # Open template
            with open(self.directory + '/' + template + '.' + self.extension) as fin:
                # Keep the specification in a list
                docstring: List[str] = list()
                for line in fin.readlines():
                    if line.startswith('#'):
                        # Add all lines starting with #
                        docstring.append(line[1:])
                    else:
                        # Break as soon as line doesn't start with #
                        break
                result.append({'name': template, 'doc': '\n'.join(docstring)})

        return json.dumps(result)


class SC3MicroApi(object):
    """Main class including the dispatcher."""

    def __init__(self):
        """Constructor of the Provgen object."""
        config = configparser.RawConfigParser()
        here: str = os.path.dirname(__file__)
        config.read(os.path.join(here, 'sc3microapi.cfg'))

        # Read connection parameters
        self.templatesAPI = TemplatesAPI(config.get('Service', 'templatesdir'))

    @cherrypy.expose
    def index(self) -> str:
        cherrypy.response.header_list = [('Content-Type', 'text/html')]

        # TODO Create an HTML page with a minimum documentation for a user
        try:
            with open('help.html') as fin:
                texthelp: str = fin.read()
        except:
            texthelp: str = """<html>
                                <head>sc3microapi</head>
                                <body>
                                  Default help for the sc3microapi service (GEOFON).
                                </body>
                              </html>"""

        return texthelp

    @cherrypy.expose
    def templates(self, *args: Tuple, **kwargs: Dict) -> str:
        """Get a template in Notation3 format or a list of templates (JSON).

        :returns: Templates available in JSON format or a template with all variables replaced.
        :rtype: string
        """
        if not len(args):
            cherrypy.response.header_list = [('Content-Type', 'application/json')]
            return self.templatesAPI.list()

        cherrypy.response.header_list = [('Content-Type', 'text/n3')]
        try:
            result = self.templatesAPI.retrieve('/'.join(args), kwargs)
            return result
        except FileNotFoundError:
            # Send Error 404
            messDict: Dict = {'code': 0,
                              'message': 'Template %s could not be found.' %
                                         '/'.join(args)}
            message: str = json.dumps(messDict)
            # cherrypy.log(message)
            cherrypy.response.headers['Content-Type'] = 'application/json'
            raise cherrypy.HTTPError(404, message)
        except Exception as e:
            # Send Error 400
            messDict: Dict = {'code': 0,
                              'message': str(e)}
            message: str = json.dumps(messDict)
            # cherrypy.log(message)
            cherrypy.response.headers['Content-Type'] = 'application/json'
            raise cherrypy.HTTPError(400, message)

    @cherrypy.expose
    def features(self) -> str:
        """Read the features of the system and return them in JSON format.

        :returns: System capabilities in JSON format
        :rtype: string
        """
        syscapab: Dict = {
                     "whatever": False,
                   }
        cherrypy.response.header_list = [('Content-Type', 'application/json')]
        return json.dumps(syscapab)

    @cherrypy.expose
    def version(self) -> str:
        """Return the version of this implementation.

        :returns: System capabilities in JSON format
        :rtype: string
        """
        version: str = '0.1a1'
        cherrypy.response.header_list = [('Content-Type', 'text/plain')]
        return version


server_config: Dict[str, Dict] = {
    'global': {
        'tools.proxy.on': True,
    	'server.socket_host': '127.0.0.1',
    	'server.socket_port': 8080,
    	'engine.autoreload_on': False
    }
}
cherrypy.tree.mount(SC3MicroApi(), '/sc3microapi', server_config)

if __name__ == "__main__":
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()