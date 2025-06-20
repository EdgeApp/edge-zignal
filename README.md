# Zignal

A bridge service for Edge Support to bridge messages in Signal to Zendesk.

It has two main scripts:
- `main.py` — takes Signal messages and puts them in Zendesk
- `webhook.py` — takes Zendesk replies and sends back through Signal

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
```

Install the package dependencies:

```sh
python -m venv venv
source venv/bin/activate 
python -m pip install -r requirements.txt
```
> Must activate virtual environment for pip install to work

Copy the `.env.sample` to `.env` and edit `.env` with the appropriate the ENV configuration.

```
cp .env.sample .env
```

## Run the signal-cli service

Run the signal-cli docker container:

1. Build and start the container:
```bash
docker-compose up -d
```

2. Connect phone number to Signal

Option A:
# Link existing Signal account with another device
```bash
docker exec -it signal-cli signal-cli link -n "DEVICE_NICKNAME"
```
Example Result: sgnl://linkdevice?uuid=dz5j4uXnkytQoPIRTe8sUw%3D%3D&pub_key=BdtMo5308wXyGY72XBN8YgYJv8ju9hsf4SW%2BCXwE6rZW
> Copy generated code from command line and paste into QR generator to scan with a device that is already logged in
> Generator: https://www.the-qrcode-generator.com/


Option B:
Register your phone number (replace +1234567890 with your number):
```bash
docker exec -it signal-cli signal-cli -a +1234567890 register --captcha "CAPTCHA"
```
> Captcha intructions: https://github.com/AsamK/signal-cli/wiki/Registration-with-captcha
> **Note:** You can use the `--voice` flag to register with a phone call instead of SMS but must try the SMS first

Verify your number with the code received via SMS:
```bash
docker exec -it signal-cli signal-cli -a +1234567890 verify CODE
```

4. The Signal CLI daemon will be running and accessible at http://localhost:8090

## Run the Zignal service


```sh
source venv/bin/activate
python3 main.py
```

## 🔧 one-time setup (OLD DOCUMENTATION)

```bash
cd ~/Developer/zignal/edge-zignal
python -m venv venv
source venv/bin/activate
pip install requests flask python-dotenv
pip freeze > requirements.txt  # optional but nice to have

# Make sure Docker is running the cli

## Run signal => zendesk bot
cd ~/Developer/zignal/edge-zignal
source venv/bin/activate
python main.py

## Run zendesk => signal webhook
cd ~/Developer/zignal/edge-zignal
source venv/bin/activate
python webhook.py
# Runs locally @
http://localhost:5000/zendesk-replies


## Command to make webhook public to be reachable by zendesk online
ngrok http 5000
# example response
https://abc1234.ngrok-free.app


## Reinstall or move machines
cd edge-zignal
python -m venv venv
source venv/bin/activate
python3 -m pip install -r requirements.txt

