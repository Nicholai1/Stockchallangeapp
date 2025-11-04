"""Optional Redis-backed pub/sub bridge for websocket broadcasting.

This module provides a small wrapper that can be enabled by setting REDIS_URL.
It's intentionally minimal: it subscribes to a channel and forwards messages into the
existing ws_manager queue. The in-process ws_manager remains the default when
REDIS_URL is not set.
"""
import os
import asyncio
import json
import logging

_logger = logging.getLogger(__name__)

try:
    import aioredis
except Exception:
    aioredis = None


async def start_redis_bridge(loop, ws_enqueue_fn):
    url = os.environ.get('REDIS_URL')
    if not url:
        _logger.info('REDIS_URL not configured; Redis pubsub bridge disabled')
        return None
    if aioredis is None:
        _logger.warning('aioredis not installed; cannot start redis bridge')
        return None

    _logger.info('Starting Redis pubsub bridge to %s', url)
    try:
        r = await aioredis.create_redis_pool(url)
        ch, = await r.subscribe('prices')

        async def reader(channel):
            while await channel.wait_message():
                msg = await channel.get(encoding='utf-8')
                try:
                    j = json.loads(msg)
                except Exception:
                    j = { 'type': 'price_update', 'payload': msg }
                # forward into ws_manager queue
                try:
                    await ws_enqueue_fn(j)
                except Exception:
                    _logger.exception('Failed to enqueue message from redis')

        loop.create_task(reader(ch))
        return r
    except Exception:
        _logger.exception('Failed to start redis bridge')
        return None
