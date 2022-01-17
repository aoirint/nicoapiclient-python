from nicotoolspy.auth.following_lives import following_lives
from nicotoolspy.session import create_auth_session


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument('--cookie_file', type=str, default='cookies.pkl')

  args = parser.parse_args()

  cookie_file = args.cookie_file

  session = create_auth_session(cookie_file=cookie_file)

  print(
    following_lives(session)
  )
