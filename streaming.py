import os
import json
import base64
import asyncio
import audioop
import logging
from flask import Flask, render_template, request
from flask_sockets import Sockets
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler
from asr_client import ASRClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables or use default values
HTTP_SERVER_PORT = int(os.getenv("HTTP_SERVER_PORT", 8080))


app = Flask(__name__)
sockets = Sockets(app)


@app.route("/twiml", methods=["POST"])
def return_twiml():
    logger.info("Received POST TwiML")
    return render_template("streams.xml")


@sockets.route("/")
def echo(ws):
    logger.info("Connection with media stream accepted.")

    async def process_media(ws, asr_client):
        while not ws.closed:
            message = ws.receive()
            if message is None:
                send_task = asyncio.create_task(
                    asr_client.send_data(json.dumps({"eof": 1}))
                )
                await asyncio.gather(send_task)
                continue

            data = json.loads(message)
            if data["event"] == "connected":
                logger.info("Connected Message received: %s", message)
            if data["event"] == "start":
                logger.info("Start Message received: %s", message)
            if data["event"] == "media":
                if asr_client.websocket and asr_client.websocket.open:
                    media_payload = data["media"]["payload"]
                    ulaw_data = base64.b64decode(media_payload)
                    pcm_data = audioop.ulaw2lin(ulaw_data, 2)
                    send_task = asyncio.create_task(asr_client.send_data(pcm_data))
                    await asyncio.gather(send_task)
                else:
                    logger.warning(
                        "ASR client connection not open. Skipping sending audio data."
                    )

            if data["event"] == "closed":
                logger.info("Closed Message received %s", message)
                send_task = asyncio.create_task(
                    asr_client.send_data(json.dumps({"eof": 1}))
                )
                await asyncio.gather(send_task)
                break

    async def handle_connection(ws):
        asr_client = ASRClient()
        await asr_client.connect()
        media_task = asyncio.create_task(process_media(ws, asr_client))
        recv_task = asyncio.create_task(asr_client.receive_response())
        await asyncio.gather(recv_task, media_task)

    asyncio.run(handle_connection(ws))


if __name__ == "__main__":
    server = pywsgi.WSGIServer(
        ("", HTTP_SERVER_PORT),
        app,
        handler_class=WebSocketHandler,
    )
    logger.info(f"Server listening on: http://localhost:{HTTP_SERVER_PORT}")
    server.serve_forever()
