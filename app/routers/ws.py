from fastapi import APIRouter, WebSocket
from app.services import ws_manager

router = APIRouter()


@router.websocket('/ws/prices')
async def websocket_prices(ws: WebSocket):
    await ws_manager.handle_connection(ws)
