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
pip3 install -r requirements.txt
python3 -m venv venv
```

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

2. Register your phone number (replace +1234567890 with your number):
```bash
docker exec -it signal-cli signal-cli -a +1234567890 register
```

3. Verify your number with the code received via SMS:
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
pip install -r requirements.txt

