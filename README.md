# Zignal

A bridge service for Edge Support to bridge messages in Signal to Intercom.

It has one main script:

- `main.py` — takes Signal messages and puts them in Intercom

---

## Setup

Install the necessary environment dependencies:

1. Install Python3
2. Install pip

For Ubuntu, installation script is the following:

```sh
sudo apt update
sudo apt install python3
sudo apt install python3-pip
sudo apt install python3.12-venv
```

Install the package dependencies:

```sh
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```
> Must activate virtual environment for pip install to work

Copy the `.env.sample` to `.env` and edit `.env` with the appropriate the ENV configuration.

```
cp .env.sample .env
```

You'll need:
- **INTERCOM_ACCESS_TOKEN** — from the Intercom Developer Hub (Configure > Authentication)
- **INTERCOM_ADMIN_ID** — the admin ID the bridge will act as (find via Intercom dashboard or `GET https://api.intercom.io/admins`)

## Run the signal-cli service

1. Build and start the container:
```sh
docker-compose up -d
```

2. Connect phone number to Signal

**Option A — QR code login (easiest):**
```sh
curl http://localhost:8090/v1/qrcodelink?device_name=edge-zignal -o login.png
catimg login.png
```

**Option B — Link existing Signal account with another device:**
```bash
docker exec -it signal-cli signal-cli link -n "DEVICE_NICKNAME"
```
> Copy the generated `sgnl://` link and paste into a QR generator to scan with a device that is already logged in.
> Generator: https://www.the-qrcode-generator.com/

**Option C — Register a new phone number:**
```bash
docker exec -it signal-cli signal-cli -a +1234567890 register --captcha "CAPTCHA"
```
> Captcha instructions: https://github.com/AsamK/signal-cli/wiki/Registration-with-captcha
> **Note:** You can use the `--voice` flag to register with a phone call instead of SMS but must try the SMS first

Verify your number with the code received via SMS:
```bash
docker exec -it signal-cli signal-cli -a +1234567890 verify CODE
```

3. The Signal CLI daemon will be running and accessible at http://localhost:8090

## Run the Zignal service

```sh
source venv/bin/activate
python3 main.py
```

## Incoming Signal messages

The first incoming message creates a conversation from the Signal contact.
Follow-up messages on an existing open conversation add a user reply from that
same contact saying "New Signal message received". Only these generic
notifications are stored in Intercom, never the Signal message contents.

Run the mocked regression test with `python3 -m unittest discover -s tests -v`.

## Agent reply notes

Direct replies sent from another device linked to the support Signal account add
an internal note to the recipient's most recently updated existing Intercom
conversation (including a closed conversation):

> Response sent in Signal by device "jared-mac".

The bridge reads `syncMessage.sentMessage` and resolves `sourceDevice` using a
fresh `GET /v1/devices/{number}` lookup. No permanent device mapping is required.
Use descriptive names in Signal's linked-device list when linking or relinking.
If the name cannot be resolved, or the current device was linked after the reply
was sent (possible ID reuse), the note says "unknown device".

Notes use `INTERCOM_ADMIN_ID` as their author. Set this to a dedicated bridge
teammate's admin ID if desired; the access token authenticates API requests.
Reply text and attachments are not copied to Intercom or dumped into bridge logs.
Group messages, Note to Self, receipts and reactions do not create reply notes.
No contact or conversation is created solely because an agent sent a reply.

Repeated sync events are suppressed for the last 10,000 successful notes in the
running process. This is not a durable delivery queue: restarting clears that
history, and failed Intercom writes are logged but are not automatically retried
unless the sync event is received again. A live smoke test should confirm the
installed REST API version returns device names and creation timestamps.

Run the mocked regression tests (no live Signal or Intercom calls):

```sh
python3 -m unittest discover -s tests -v
```
