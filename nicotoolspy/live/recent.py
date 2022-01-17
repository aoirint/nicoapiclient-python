from typing import Literal, Optional, List
from pydantic.dataclasses import dataclass
from ..session import create_session
from requests import Session

# 放送中の生放送番組
url = 'https://live.nicovideo.jp/front/api/pages/recent/v1/programs'

all_tab_types = [
  'common', # 一般
  'try', # やってみた
  'live', # ゲーム
  'req', # 動画紹介
  'face', # 顔出し
  'totu', # 凸待ち
]

all_sort_order_type = [
  'recentDesc', # 放送日が近い順
  'recentAsc', # 放送日が遠い順
  'viewCountDesc', # 来場者数が多い順
  'viewCountAsc', # 来場者数が少ない順
  'commentCountDesc', # コメントが多い順
  'commentCountAsc', # コメントが少ない順
  'userLevelDesc', # ユーザーレベルが高い順
  'userLevelAsc', # ユーザーレベルが低い順
]

LiveTabType = Literal[tuple(all_tab_types)]
SortOrderType = Literal[tuple(all_sort_order_type)]

@dataclass
class Meta:
  status: int
  errorCode: str

@dataclass
class ScreenshotThumbnail:
  liveScreenshotThumbnailUrl: Optional[str]
  tsScreenshotThumbnailUrl: Optional[str]

@dataclass
class SocialGroup:
  id: str
  name: str
  thumbnailUrl: str

@dataclass
class ProgramProvider:
  name: str
  icon: str
  iconSmall: str
  id: Optional[str] = None

@dataclass
class Statistics:
  watchCount: int
  commentCount: int
  reservationCount: Optional[int]

@dataclass
class Timeshift:
  isPlayable: bool
  isReservable: bool

@dataclass
class Nicoad:
  userName: str
  totalPoint: int
  decoration: str

@dataclass
class DataItem:
  id: str
  title: str
  thumbnailUrl: Optional[str]
  hugeThumbnailUrl: Optional[str]
  screenshotThumbnail: Optional[ScreenshotThumbnail]
  watchPageUrl: str
  watchPageUrlAtTopPlayer: Optional[str]
  providerType: str
  liveCycle: str
  beginAt: int
  endAt: int
  isFollowerOnly: bool
  socialGroup: SocialGroup
  programProvider: ProgramProvider
  statistics: Statistics
  timeshift: Timeshift
  nicoad: Optional[Nicoad] = None
  isPayProgram: bool = False

@dataclass
class Response:
  meta: Meta
  data: List[DataItem]


def recent_lives(
  tab: LiveTabType = 'common',
  offset: int = 0,
  sort_order: SortOrderType = 'recentDesc',
  session: Session = None,
) -> List[DataItem]:
  if session is None:
    session = create_session()

  params = {
    'tab': tab,
    'sortOrder': sort_order,
  }
  if offset > 0:
    params['offset'] = offset

  res = session.get(url, params=params)
  jsonres = res.json()

  resobj = Response.__pydantic_model__.parse_obj(jsonres)
  if resobj.meta.status != 200:
    raise Exception('not ok')

  return resobj.data
