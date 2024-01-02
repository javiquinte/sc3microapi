from pydantic import BaseModel
from pydantic import constr
from pydantic import conint
from typing import Union
from typing import Literal
from datetime import datetime

# Define formally parts of the NSLC code
NetworkCode = constr(strip_whitespace=True, to_upper=True, min_length=2, max_length=7)
StationCode = constr(strip_whitespace=True, to_upper=True, min_length=1, max_length=5, pattern=r'[A-Z][A-Z1-9]{0,4}')
LocationCode = constr(strip_whitespace=True, to_upper=True, max_length=2, pattern=r'[A-Z0-9]{0,2}')
ChannelCode = constr(strip_whitespace=True, to_upper=True, min_length=3, max_length=3, pattern=r'[A-Z0-9]{3}')


class Network(BaseModel):
    code: NetworkCode
    start: datetime
    end: Union[datetime, None]
    netClass: Literal['p', 't']
    archive: str
    restricted: Literal[0, 1]
    shared: Literal[0, 1]


class Station(BaseModel):
    network: NetworkCode
    code: StationCode
    latitude: float
    longitude: float
    elevation: float
    place: str
    country: str
    start: datetime
    end: Union[datetime, None]
    restricted: Literal[0, 1]
    shared: Literal[0, 1]


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
        result = datetime(*map(int, dateparts))
    except Exception:
        raise ValueError('{} could not be parsed as datetime.'.format(dateiso))

    return result
