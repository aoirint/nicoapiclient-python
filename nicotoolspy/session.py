import pickle as pkl
from requests import Session

useragent = 'NicotoolspyBot @aoirint'

def create_session() -> Session:
  session = Session()
  session.headers['User-Agent'] = useragent

  return session

def create_auth_session(
  cookie_file: str = 'cookies.pkl',
) -> Session:
  session = create_session()

  with open(cookie_file, 'rb') as fp:
    session.cookies = pickle.load(fp)

  return session
