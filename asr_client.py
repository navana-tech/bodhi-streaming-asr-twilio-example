import os
import json
import uuid
import websockets
import ssl
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Get environment variables or use default values
ASR_SERVER_URL = os.getenv("ASR_SERVER_URL", "wss://bodhi.navana.ai")
API_KEY = os.getenv("API_KEY")
CUSTOMER_ID = os.getenv("CUSTOMER_ID")


if not API_KEY or not ASR_SERVER_URL:
    print("Please set API key and customer ID in environment variables.")
    exit(1)


class ASRClient:
    def __init__(self):
        self.websocket = None
        self.complete_sentences = []

    async def connect(self):
        try:
            logger.info("Connecting to ASR server...")
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            self.websocket = await websockets.connect(
                ASR_SERVER_URL,
                extra_headers={
                    "x-api-key": API_KEY,
                    "x-customer-id": CUSTOMER_ID,
                },
                ssl=ssl_context,
            )
            await self.websocket.send(
                json.dumps(
                    {
                        "config": {
                            "sample_rate": 8000,
                            "transaction_id": str(uuid.uuid4()),
                            "model": "hi-general-v2-8khz",
                        }
                    }
                )
            )
            logger.info("Connected to ASR server.")

        except Exception as e:
            logger.error(f"Error connecting to ASR server: {e}")

    async def send_data(self, pcm_data):
        try:
            await self.websocket.send(pcm_data)

        except Exception as e:
            logger.error(f"Error communicating with ASR server: {e}")

    async def receive_response(self):
        try:
            while True:
                asr_response = await self.websocket.recv()

                try:
                    response_data = json.loads(asr_response)

                    call_id = response_data["call_id"]
                    segment_id = response_data["segment_id"]
                    transcript_type = response_data["type"]
                    transcript_text = response_data["text"]
                    end_of_stream = response_data["eos"]

                    if transcript_type == "complete" and transcript_text != "":
                        self.complete_sentences.append(response_data["text"])

                    logger.info(
                        f"Received data: Call_id={call_id}, "
                        f"Segment_id={segment_id}, "
                        f"EOS={end_of_stream}, "
                        f"Type={transcript_type}, "
                        f"Text={transcript_text}"
                    )

                    if response_data["eos"]:
                        logger.info(
                            "Complete transcript: %s",
                            ", ".join(self.complete_sentences),
                        )
                        break
                except json.JSONDecodeError:
                    logger.error(f"Received a non-JSON response: {asr_response}")

        except websockets.exceptions.ConnectionClosed as e:
            logger.error(f"Connection to ASR server closed: {e}")
        except Exception as e:
            logger.error(f"Error receiving ASR response: {e}")
