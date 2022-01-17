import os
import requests
from nicotoolspy.session import create_auth_session
from nicotoolspy.cli.login import login
from nicotoolspy.auth.following_lives import following_lives
from nicotoolspy.live.recent import recent_lives


def command_login(args):
  login(
    mail_tel=args.mail_tel,
    password=args.password,
    cookie_file=args.cookie_file,
  )
  print('Logined')

def command_following_lives(args):
  session = create_auth_session(cookie_file=args.cookie_file)
  lives = following_lives(session=session)

  for live_entry in lives:
    live_id = live_entry.id # https://live.nicovideo.jp/watch/lv{live_id}
    community_name = live_entry.community_name
    title = live_entry.title
    elapsed_time = live_entry.elapsed_time # seconds

    live_url = f'https://live.nicovideo.jp/watch/lv{live_id}'

    print(f'[{community_name}] {title} (elapsed: {elapsed_time}s): {live_url}')

def command_recent_lives(args):
  session = create_auth_session(cookie_file=args.cookie_file)
  lives = recent_lives(session=session)

  print(lives)


if __name__ == '__main__':
  import argparse

  parser = argparse.ArgumentParser()
  parser.add_argument('--cookie_file', type=str, default='cookies.pkl')

  subparsers = parser.add_subparsers()

  parser_login = subparsers.add_parser('login')
  parser.add_argument('--mail_tel', type=str)
  parser.add_argument('--password', type=str)
  parser_login.set_defaults(handler=command_login)

  parser_following_lives = subparsers.add_parser('following_lives')
  parser_following_lives.set_defaults(handler=command_following_lives)

  parser_recent_lives = subparsers.add_parser('recent_lives')
  parser_recent_lives.set_defaults(handler=command_recent_lives)

  args = parser.parse_args()
  if hasattr(args, 'handler'):
    args.handler(args)
  else:
    parser.print_help()
