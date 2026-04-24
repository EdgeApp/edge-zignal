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
