import os
import requests
import pickle
from getpass import getpass

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

  def update_session(self):
    cookies = self.http_session.cookies
    session_data = {
      'cookies': cookies,
    }

    with open(self.session_file, 'wb') as fp:
      pickle.dump(session_data, fp)

  def fetch_live_list(self):
    live_list_url = 'https://papi.live.nicovideo.jp/api/relive/notifybox.content?rows=100'

    res = self.http_session.get(live_list_url)
    data = res.json()

    meta = data.get('meta', {})
    status = meta.get('status')

    if status != 200:
      error_code = meta.get('errorCode')
      error_message = meta.get('errorMessage')
      raise Exception(f'Error {error_code}: {error_message}')

    data = data.get('data')
    notifybox_content = data.get('notifybox_content')

    return notifybox_content

def command_login(args):
  session = NiconicoSession(session_file=args.session_file)

  login = args.login
  if not login:
    login = input('Email or TEL: ')

  password = args.password
  if not password:
    password = getpass()

  session.login(
    mail_tel=login,
    password=password,
  )
  print('Logined')

def command_live_list(args):
  session = NiconicoSession(session_file=args.session_file)

  live_list = session.fetch_live_list()
  for live_entry in live_list:
    live_id = live_entry.get('id') # https://live.nicovideo.jp/watch/lv{live_id}
    community_name = live_entry.get('community_name')
    title = live_entry.get('title')
    elapsed_time = live_entry.get('elapsed_time') # seconds

    live_url = f'https://live.nicovideo.jp/watch/lv{live_id}'

    print(f'[{community_name}] {title} (elapsed: {elapsed_time}s): {live_url}')


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument('--session_file', type=str, default='session.pkl')

  subparsers = parser.add_subparsers()

  parser_login = subparsers.add_parser('login')
  parser.add_argument('--login', type=str)
  parser.add_argument('--password', type=str)
  parser_login.set_defaults(handler=command_login)

  parser_live_list = subparsers.add_parser('live_list')
  parser_live_list.set_defaults(handler=command_live_list)

  args = parser.parse_args()
  if hasattr(args, 'handler'):
    args.handler(args)
  else:
    parser.print_help()
