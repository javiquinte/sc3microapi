import logging
from abc import ABC
from abc import abstractmethod
from datetime import datetime
from typing import Union
from typing import Literal
from typing import List
from core import NetworkCode
from core import Network
from pydantic import conint
import MySQLdb
from MySQLdb.cursors import DictCursor


class GenericConnection(ABC):
    @abstractmethod
    def getnetworks(self, net: Union[NetworkCode, None], restricted: conint(ge=0, le=1) = None,
                    archive: str = None, netclass: Literal['p', 't'] = None,
                    shared: conint(ge=0, le=1) = None, starttime: str = None, endtime: str = None) -> List[Network]:
        pass


class TestConnection(GenericConnection):
    def getnetworks(self, net: Union[NetworkCode, None], restricted: conint(ge=0, le=1) = None,
                    archive: str = None, netclass: Literal['p', 't'] = None,
                    shared: conint(ge=0, le=1) = None, starttime: datetime = None,
                    endtime: datetime = None) -> List[Network]:
        """Get networks from the DB"""

        query = 'select code, start, end, netClass, archive, restricted, shared from Network'
        fields = ['code', 'start', 'end', 'netClass', 'archive', 'restricted', 'shared']
        # fields.extend(self.extrafields)

        whereclause = []
        variables = []
        if net is not None:
            result = [Network(**{'code': net, 'start': datetime(2020, 1, 1),
                                 'end': None, 'netClass': 'p', 'archive': 'GFZ', 'restricted': 0, 'shared': 1})]
            if net[0] in '0123456789XYZ':
                try:
                    net, year = net.split('_')
                except ValueError:
                    # Send Error 400
                    errmsg = 'Wrong network code (%s). Temporary codes must include the start year (e.g. 4C_2011).'
                    raise Exception(errmsg % net)

                whereclause.append('YEAR(start)=%s')
                variables.append(int(year))

            whereclause.append('code=%s')
            variables.append(net)
        else:
            result = [Network(**{'code': 'GE', 'start': datetime(2020, 1, 1), 'end': None,
                                 'netClass': 'p', 'archive': 'GFZ', 'restricted': 0, 'shared': 1}),
                      Network(**{'code': '4C_2018', 'start': datetime(2018, 1, 1),
                                 'end': datetime(2019, 12, 31), 'netClass': 't', 'archive': 'GFZ',
                                 'restricted': 1, 'shared': 0})]

        if restricted is not None:
            whereclause.append('restricted=%s')
            variables.append(restricted)

        if archive is not None:
            whereclause.append('archive=%s')
            variables.append(archive)

        if netclass is not None:
            whereclause.append('netClass=%s')
            variables.append(netclass)

        if shared is not None:
            whereclause.append('shared=%s')
            variables.append(shared)

        if starttime is not None:
            whereclause.append('start>=%s')
            variables.append(starttime)

        if endtime is not None:
            whereclause.append('end<=%s')
            variables.append(endtime)

        if len(whereclause):
            query = query + ' where ' + ' and '.join(whereclause)

        logging.debug(query % tuple(variables))
        return result


class SC3dbconnection(GenericConnection):
    def __init__(self, host: str, user: str, password: str, db: str = 'seiscomp3'):
        """Constructor of the AccessAPI class.

        If db='test' there will be no real connection to a database, but a simulated connection
        returning random data to be used in tests.
        """
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

    def getnetworks(self, net: Union[NetworkCode, None], restricted: conint(ge=0, le=1) = None,
                    archive: str = None, netclass: Literal['p', 't'] = None,
                    shared: conint(ge=0, le=1) = None, starttime: str = None, endtime: str = None) -> List[Network]:
        pass

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
