import pickle as pkl
from getpass import getpass
from nicotoolspy.auth.create_auth_cookies import create_auth_cookies
from nicotoolspy.session import create_session

if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument('--mail_tel', type=str)
  parser.add_argument('--password', type=str)
  parser.add_argument('--cookie_file', type=str, default='cookies.pkl')

  args = parser.parse_args()

  mail_tel = args.mail_tel
  if not mail_tel:
    mail_tel = input('Email or TEL: ')

  password = args.password
  if not password:
    password = getpass()

  cookie_file = args.cookie_file

  session = create_session()

  create_auth_cookies(
    mail_tel=mail_tel,
    password=password,
    session=session,
  )

  with open(cookie_file, 'wb') as fp:
    pkl.dump(session.cookies, fp)
