import pickle
from getpass import getpass
from nicotoolspy.login import create_auth_cookies
from nicotoolspy.session import create_session


def create_auth_cookies(
  mail_tel: str = None,
  password: str = None,
  cookie_file: str = None,
):
  if not mail_tel:
    mail_tel = input('Email or TEL: ')

  if not password:
    password = getpass()

  session = create_session()

  create_auth_cookies(
    mail_tel=mail_tel,
    password=password,
    session=session,
  )

  with open(cookie_file, 'wb') as fp:
    pickle.dump(session.cookies, fp)
