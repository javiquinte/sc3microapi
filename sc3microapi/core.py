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
    restricted: conint(ge=0, le=1)
    shared: conint(ge=0, le=1)
