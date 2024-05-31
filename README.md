# Basic Demo

This is a simple server application that processes audio from Twilio Media Streams and generates real-time transcripts using Bodhi.

---

> Please note: This demo is unidirectional, meaning you won't receive
> any response during the call. However, you'll be able to view live
> transcripts on your console.

---

## Documentation

For detailed configuration and response information, refer to the [Bodhi documentation](https://navana.gitbook.io/bodhi).

## App server setup

### Running the server

1. Create your virtualenv `python3 -m venv venv`.
2. Run `source venv/bin/activate`.
3. Run `pip3 install -r requirements.txt`.
4. Run `python3 streaming.py`.

### Configure using the Console

1. Access the [Twilio console](https://www.twilio.com/console/voice/numbers) to get a `<TWILIO-PHONE-NUMBER>`.
2. Run the server (listening on port 8080).
3. Edit the `streams.xml` file in the `templates` directory and add your tunnel/server URL as `wss://<server url>`.
4. Change webhook URL in incoming config [Twilio phone number config](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming).
