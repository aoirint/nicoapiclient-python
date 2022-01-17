from nicotoolspy.cli.login import login


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument('--mail_tel', type=str)
  parser.add_argument('--password', type=str)
  parser.add_argument('--cookie_file', type=str, default='cookies.pkl')

  args = parser.parse_args()

  mail_tel = args.mail_tel
  password = args.password
  cookie_file = args.cookie_file

  login(
    mail_tel=mail_tel,
    password=password,
    cookie_file=cookie_file,
  )
