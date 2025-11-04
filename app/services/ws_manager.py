import asyncio
import json
import logging
from typing import Dict, Set

from starlette.websockets import WebSocket

_logger = logging.getLogger(__name__)

# Global state initialized on app startup
_loop: asyncio.AbstractEventLoop | None = None
_queue: asyncio.Queue | None = None
# Map websocket -> set of subscribed symbols (empty set means subscribe to all)
_clients: Dict[WebSocket, Set[str]] = {}


async def init(loop: asyncio.AbstractEventLoop):
    global _loop, _queue
    _loop = loop
    _queue = asyncio.Queue()
    # start broadcaster task
    loop.create_task(_broadcaster())
    _logger.info("ws_manager initialized")


async def _broadcaster():
    global _queue
    if _queue is None:
        _logger.warning("ws_manager broadcaster started without queue")
        return
    while True:
        try:
            msg = await _queue.get()
            # msg is expected to be a dict with at least 'symbol'
            symbol = msg.get('symbol')
            text = json.dumps(msg, default=str)
            # send to all clients whose subscription includes symbol
            to_remove = []
            for ws, subs in list(_clients.items()):
                try:
                    # if subs empty -> subscribed to all
                    if not subs or (symbol and symbol in subs):
                        await ws.send_text(text)
                except Exception:
                    _logger.exception("Removing websocket due to send failure")
                    to_remove.append(ws)
            for ws in to_remove:
                _clients.pop(ws, None)
        except Exception:
            _logger.exception("Error in ws broadcaster loop")


async def handle_connection(ws: WebSocket):
    """Accept a websocket and handle simple subscription messages.

    Protocol (JSON):
      {"type": "subscribe", "symbols": ["AAPL","TSLA"]}
      {"type": "unsubscribe", "symbols": ["AAPL"]}
      If no subscribe message is received, client will receive only broadcasts sent to all (if any).
    """
    await ws.accept()
    _clients[ws] = set()
    try:
        while True:
            data = await ws.receive_text()
            try:
                j = json.loads(data)
            except Exception:
                continue
            t = j.get('type')
            if t == 'subscribe':
                syms = j.get('symbols') or []
                if isinstance(syms, list):
                    _clients[ws] = set([s.upper() for s in syms if isinstance(s, str)])
            elif t == 'unsubscribe':
                syms = j.get('symbols') or []
                if isinstance(syms, list):
                    for s in syms:
                        _clients[ws].discard(s.upper())
            # ignore other messages
    except Exception:
        # websocket disconnect or error
        _clients.pop(ws, None)


def enqueue_message_from_thread(msg: dict):
    """Called from non-async threads (like the price updater) to queue a message for broadcast."""
    global _loop, _queue
    if _loop is None or _queue is None:
        _logger.debug("ws_manager not initialized; dropping message: %s", msg)
        return
    try:
        _loop.call_soon_threadsafe(_queue.put_nowait, msg)
    except Exception:
        _logger.exception("Failed to enqueue websocket message from thread")
