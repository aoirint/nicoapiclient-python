from requests import Session
from requests.cookies import RequestsCookieJar
from .session import create_session

login_url = 'https://account.nicovideo.jp/login/redirector'


def create_auth_cookies(
  mail_tel: str,
  password: str,
  session: Session = None,
) -> RequestsCookieJar:
  if session is None:
    session = create_session()

  login_data = {
    'mail_tel': mail_tel,
    'password': password,
    'auth_id': '1687808797',
  }

  session.post(login_url, data=login_data, allow_redirects=False)

  if not session.cookies.get('user_session'):
    raise Exception('Login failed')

  return session.cookies
