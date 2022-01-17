from typing import Literal, Optional, List
from pydantic.dataclasses import dataclass
from requests import Session
from requests.cookies import RequestsCookieJar

live_list_url = 'https://papi.live.nicovideo.jp/api/relive/notifybox.content?rows=100'

@dataclass
class Meta:
  status: int
  errorCode: Optional[str] = None
  errorMessage: Optional[str] = None

@dataclass
class NotifyboxContent:
  id: str
  title: str
  thumbnail_url: str
  thumbnail_link_url: str
  community_name: str
  elapsed_time: int
  provider_type: str

@dataclass
class ResponseData:
  notifybox_content: List[NotifyboxContent]
  total_page: int

@dataclass
class Response:
  meta: Meta
  data: ResponseData


def following_lives(
  session: Session,
) -> List[NotifyboxContent]:
  res = session.get(live_list_url)
  jsonres = res.json()

  resobj = Response.__pydantic_model__.parse_obj(jsonres)

  meta = resobj.meta
  status = meta.status
  if status != 200:
    error_code = meta.errorCode
    error_message = meta.errorMessage
    raise Exception(f'Error {error_code}: {error_message}')

  return resobj.data.notifybox_content
