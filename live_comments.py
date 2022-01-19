import asyncio
import websockets
import json
from typing import Any, Awaitable, Callable, Optional
from dataclasses import dataclass
from nicotoolspy.session import create_session
from bs4 import BeautifulSoup

@dataclass
class WebSocketJsonMessageListener:
  on_connect: Callable
  on_message: Callable[[dict[str, Any]], Awaitable[None]]
  on_close: Callable

async def listen_websocket_json_message(
  ws: websockets.WebSocketClientProtocol,
  listener: WebSocketJsonMessageListener,
  on_socket_closed: Callable,
  on_task_cancel: Callable,
):
  async def _recv() -> dict[str, Any]:
    data_string = await ws.recv()
    # print('⬇', data_string)
    data = json.loads(data_string)
    return data

  try:
    while True:
      message = await _recv()
      await listener.on_message(message)
  except websockets.ConnectionClosed:
    on_socket_closed()
  except asyncio.CancelledError:
    on_task_cancel()
  except Exception as err:
    import traceback
    traceback.print_exc()
    raise err
  finally:
    print('exit websocket recv loop')

@dataclass
class WebSocketJsonMessageClient:
  url: str
  listener: WebSocketJsonMessageListener
  task: Optional[asyncio.Task] = None
  ws: Optional[websockets.WebSocketClientProtocol] = None

  async def connect(self):
    url = self.url
    listener = self.listener

    ws = await websockets.connect(url)
    listener.on_connect()

    self.task = asyncio.create_task(
      coro=listen_websocket_json_message(
        ws=ws,
        listener=listener,
        on_socket_closed=lambda: print('socket closed during recv'),
        on_task_cancel=lambda: print('task canceled'),
      ),
    )

    self.ws = ws

  async def sendEmpty(self):
    ws = self.ws
    # print('⬆')
    await ws.send('')

  async def send(self, 
    data: dict[str, Any],
  ):
    ws = self.ws

    data_string = json.dumps(data)
    # print('⬆', data_string)
    await ws.send(data_string)

  async def close(self):
    listener = self.listener

    task = self.task
    if task:
      task.cancel()

    ws = self.ws
    if ws:
      await ws.close()

    listener.on_close()

@dataclass
class MessageServer:
  type: str
  uri: str

@dataclass
class Room:
  is_first: bool
  message_server: MessageServer
  name: str
  thread_id: str
  vpos_base_time: str
  waybackkey: str
  your_postKey: str

@dataclass
class WatchClientListener:
  on_connect: Callable
  on_room_message: Callable[[Room], Awaitable[None]]
  on_close: Callable

@dataclass
class WatchClient:
  live_id: str
  watch_listener: WatchClientListener
  watch_client: Optional[WebSocketJsonMessageClient] = None

  async def connect(self):
    live_id = self.live_id
    watch_listener = self.watch_listener

    session = create_session()
    res = session.get(f'https://live.nicovideo.jp/watch/{live_id}')
    assert res.status_code == 200

    res_text = res.text
    bs = BeautifulSoup(res_text, 'html5lib')

    embedded_data = bs.select_one('#embedded-data')
    props_string = embedded_data.attrs.get('data-props')
    
    props_obj = json.loads(props_string)
    site = props_obj.get('site')
    relive = site.get('relive')
    watch_websocket_url = relive.get('webSocketUrl')

    websocket_listener = WebSocketJsonMessageListener(
      on_connect=lambda: watch_listener.on_connect(),
      on_message=self.on_message,
      on_close=lambda: watch_listener.on_close(),
    )

    client = WebSocketJsonMessageClient(
      url=watch_websocket_url,
      listener=websocket_listener,
    )
    self.watch_client = client

    await client.connect()

    await client.send({
      'type': 'startWatching',
      'data': {
        'reconnect': False,
        'room': {
          'protocol': 'webSocket',
          'commentable': True,
        },
      },
    })

  async def on_message(self, message: dict[str, Any]):
    watch_listener = self.watch_listener

    client = self.watch_client
    assert client is not None

    type = message.get('type')
    if type == 'ping':
      await client.send({
        'type': 'pong',
      })
      await client.send({
        'type': 'keepSeat',
      })
    elif type == 'room':
      data_obj = message.get('data', {})
      message_server_obj = data_obj.get('messageServer', {})
      message_server = MessageServer(
        type=message_server_obj.get('type', {}),
        uri=message_server_obj.get('uri', {}),
      )
      room = Room(
        is_first=data_obj.get('isFirst'),
        message_server=message_server,
        name=data_obj.get('name'),
        thread_id=data_obj.get('threadId'),
        vpos_base_time=data_obj.get('vposBaseTime'),
        waybackkey=data_obj.get('waybackkey'),
        your_postKey=data_obj.get('yourPostkey'),
      )
      await watch_listener.on_room_message(room)

  async def close(self):
    client = self.watch_client
    if client:
      await client.close()


async def start_keepalive_loop(
  client: WebSocketJsonMessageClient,
  on_socket_closed: Callable,
  on_task_cancel: Callable,
):
  try:
    while True:
      await client.sendEmpty()
      await asyncio.sleep(60)
  except websockets.ConnectionClosed:
    on_socket_closed()
  except asyncio.CancelledError:
    on_task_cancel()
  except Exception as err:
    import traceback
    traceback.print_exc()
    raise err
  finally:
    print('exit keepalive loop')

@dataclass
class Comment:
  anonymity: int
  content: str
  date: int
  date_usec: int
  mail: str
  no: int
  thread: str
  user_id: str
  vpos: int
  premium: int

@dataclass
class CommentClientListener:
  on_connect: Callable
  on_comment_message: Callable[[Comment], None]
  on_close: Callable

@dataclass
class CommentClient:
  live_id: str
  comment_listener: CommentClientListener
  watch_client: Optional[WatchClient] = None
  comment_client: Optional[WebSocketJsonMessageClient] = None

  keepalive_task: Optional[asyncio.Task] = None

  async def connect(self):
    live_id = self.live_id

    watch_listener = WatchClientListener(
      on_connect=lambda: print(f'[{live_id}] watch client connected'),
      on_room_message=self.on_room_message,
      on_close=lambda: print(f'[{live_id}] watch client closed'),
    )

    watch_client = WatchClient(live_id=live_id, watch_listener=watch_listener)
    self.watch_client = watch_client

    await watch_client.connect()
  
  async def on_room_message(self, room: Room):
    comment_listener = self.comment_listener

    thread = room.thread_id
    threadkey = room.your_postKey
    assert thread is not None

    comment_websocket_url = 'wss://msgd.live2.nicovideo.jp/websocket'

    websocket_listener = WebSocketJsonMessageListener(
      on_connect=lambda: comment_listener.on_connect(),
      on_message=self.on_message,
      on_close=lambda: comment_listener.on_close(),
    )

    comment_client = WebSocketJsonMessageClient(
      url=comment_websocket_url,
      listener=websocket_listener,
    )
    self.comment_client = comment_client

    await comment_client.connect()

    thread_obj = {
      'nicoru': 0,
      'res_from': -150,
      'scores': 1,
      'thread': thread,
      'user_id': 'guest',
      'version': '20061206',
      'with_global': 1,
    }

    # if authenticated
    if threadkey is not None:
      # thread_obj['user_id'] = user_id
      thread_obj['threadkey'] = threadkey

    await comment_client.send([
      {'ping': {'content': 'rs:0'}},
      {'ping': {'content': 'ps:0'}},
      {'thread': thread_obj},
      {'ping': {'content': 'pf:0'}},
      {'ping': {'content': 'rf:0'}},
    ])

    # keepalive
    keepalive_task = asyncio.create_task(
      coro=start_keepalive_loop(
        client=comment_client,
        on_socket_closed=lambda: print(f'[{thread}] keepalive socket closed'),
        on_task_cancel=lambda: print(f'[{thread}] keepalive task canceled'),
      ),
    )
    self.keepalive_task = keepalive_task

  async def on_message(self, message: dict[str, Any]):
    comment_listener = self.comment_listener

    if 'chat' in message:
      chat_obj = message.get('chat', {})
      comment = Comment(
        anonymity=chat_obj.get('anonymity'),
        content=chat_obj.get('content'),
        date=chat_obj.get('date'),
        date_usec=chat_obj.get('date_usec'),
        mail=chat_obj.get('mail'),
        no=chat_obj.get('no'),
        thread=chat_obj.get('thread'),
        user_id=chat_obj.get('user_id'),
        vpos=chat_obj.get('vpos'),
        premium=chat_obj.get('premium'),
      )
      comment_listener.on_comment_message(comment)

  async def close(self):
    watch_client = self.watch_client
    if watch_client:
      await watch_client.close()

    keepalive_task = self.keepalive_task
    if keepalive_task:
      keepalive_task.cancel()

    comment_client = self.comment_client
    if comment_client:
      await comment_client.close()


async def main(live_id: str):
  comment_listener = CommentClientListener(
    on_connect=lambda: print(f'[{live_id}] comment client connected'),
    on_comment_message=lambda comment: print(f'[{live_id}][{comment.user_id}] {comment.content}'),
    on_close=lambda: print(f'[{live_id}] comment client closed'),
  )

  client = CommentClient(live_id=live_id, comment_listener=comment_listener)

  try:
    await client.connect()

    while True:
      await asyncio.sleep(0.01)
  finally:
    await client.close()

if __name__ == '__main__':
  import argparse
  parser = argparse.ArgumentParser()
  parser.add_argument('--live_id', type=str)
  args = parser.parse_args()

  live_id = args.live_id

  asyncio.run(main(live_id=live_id))
