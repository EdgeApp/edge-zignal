# Zignal

A bridge service for Edge Support to bridge messages in Signal to Zendesk.

It has one main script:

- `main.py` — takes Signal messages and puts them in Zendesk

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

## Run the signal-cli service

1. Build and start the container:
```sh
docker-compose up -d
```

2. Register your phone number using QR login:
```sh
curl http://localhost:8090/v1/qrcodelink?device_name=edge-zignal -o login.png
catimg login.png
```

3. The Signal CLI daemon will be running and accessible at http://localhost:8090

## Run the Zignal service

```sh
source venv/bin/activate
python3 main.py
```
