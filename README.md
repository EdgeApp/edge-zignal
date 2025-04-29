Two main scripts:
- `main.py` — takes Signal messages and puts them in Zendesk
- `webhook.py` — takes Zendesk replies and sends back through Signal



---

## 🔧 one-time setup

```bash
cd ~/Developer/zignal/bot
python -m venv venv
source venv/bin/activate
pip install requests flask python-dotenv
pip freeze > requirements.txt  # optional but nice to have

# Make sure Docker is running the cli

## Run signal => zendesk bot
cd ~/Developer/zignal/bot
source venv/bin/activate
python main.py

## Run zendesk => signal webhook
cd ~/Developer/zignal/bot
source venv/bin/activate
python webhook.py
# Runs locally @
http://localhost:5000/zendesk-replies


## Command to make webhook public to be reachable by zendesk online
ngrok http 5000
# example response
https://abc1234.ngrok-free.app


## Reinstall or move machines
cd bot
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

