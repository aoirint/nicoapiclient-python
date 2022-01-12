import os
import pydantic
from pydantic import BaseModel
from typing import Dict
import requests
from requests.cookies import RequestsCookieJar
import pickle
from dataclasses import dataclass, Field

class NiconicoSession:
  def __init__(self,
    session_file: str,
  ):
    self.session_file = session_file
    self.load_session()

  def load_session(self):
    http_session = requests.Session()
    http_session.headers['User-Agent'] = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36'

    session_file = self.session_file

    self.http_session = http_session

    if not os.path.exists(session_file):
      return

    with open(session_file, 'rb') as fp:
      session_data = pickle.load(fp)

    http_session.cookies = session_data['cookies']

  def has_login_session(self) -> bool:
    return self.http_session.cookies.get('user_session')

  def check_login_session_alive(self) -> bool:
    login_history_url = 'https://account.nicovideo.jp/my/history/login'

    response = self.http_session.get(login_history_url, allow_redirects=False)
    status_code = response.status_code

    return status_code == 200

  def login(self,
    mail_tel: str,
    password: str,
  ) -> bool:
    login_url = 'https://account.nicovideo.jp/login/redirector'

    login_data = {
      'mail_tel': mail_tel,
      'password': password,
      'auth_id': '1687808797',
    }

    self.http_session.post(login_url, data=login_data, allow_redirects=False)
    if not self.has_login_session():
      raise Exception('Login failed')

    self.update_session()

  def smart_login(self, *args, **kwargs):
    if not self.check_login_session_alive():
      self.login(*args, **kwargs)

  def update_session(self):
    cookies = self.http_session.cookies
    session_data = {
      'cookies': cookies,
    }

    with open(self.session_file, 'wb') as fp:
      pickle.dump(session_data, fp)


if __name__ == '__main__':
  from dotenv import load_dotenv
  load_dotenv()

  import os

  session = NiconicoSession(session_file='session.pkl')
  session.smart_login(
    mail_tel=os.environ['MAIL_TEL'],
    password=os.environ['PASSWORD'],
  )
