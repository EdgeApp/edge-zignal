# Deploying Edge Zignal

Keep deployment addresses, account names, paths, and credentials outside Git.
Copy `.deploy.example.env` to `.deploy.local.env` and populate it from your private
operations records. The local file is gitignored; set its permissions to `0600`.
SSH requires an authorized private key. A DigitalOcean API token is not required.

## Connect

On your computer:

```sh
source .deploy.local.env
ssh "$ZIGNAL_SSH_TARGET"
```

In the remote shell, set `ZIGNAL_APP_DIR`, `ZIGNAL_APP_USER`, and `ZIGNAL_SERVICE`
to the values from the private config (local shell variables are not automatically
forwarded by SSH). Run the following commands in that same remote shell.

## Update the application

Merge approved PRs into `main` in dependency order. Check the server checkout:

```sh
cd "$ZIGNAL_APP_DIR"
sudo -u "$ZIGNAL_APP_USER" git status --short
sudo -u "$ZIGNAL_APP_USER" git branch --show-current
systemctl is-active "$ZIGNAL_SERVICE"
```

Stop if the checkout has unexpected changes or is not on `main`. Preserve local
changes before proceeding. Record the current commit for rollback, fetch, and
review the update:

```sh
zignal_previous_commit=$(sudo -u "$ZIGNAL_APP_USER" git rev-parse HEAD)
sudo -u "$ZIGNAL_APP_USER" git fetch origin
sudo -u "$ZIGNAL_APP_USER" git log --oneline HEAD..origin/main
sudo -u "$ZIGNAL_APP_USER" git diff HEAD origin/main -- requirements.txt systemd signal-cli/docker-compose.yml
```

Handle dependency, service, or container changes separately if present. For a
code-only update:

```sh
sudo -u "$ZIGNAL_APP_USER" git merge --ff-only origin/main &&
sudo -u "$ZIGNAL_APP_USER" venv/bin/python -m unittest discover -s tests -q &&
systemctl restart "$ZIGNAL_SERVICE"
```

Only restart after tests succeed. Check state immediately and again after a
polling interval:

```sh
sudo -u "$ZIGNAL_APP_USER" git rev-parse HEAD
sudo -u "$ZIGNAL_APP_USER" git status --short
systemctl show "$ZIGNAL_SERVICE" -p ActiveState -p SubState -p NRestarts -p ExecMainStartTimestamp
curl --fail --silent --show-error --output /dev/null --write-out 'Signal health HTTP %{http_code}\n' http://localhost:8090/v1/health
```

Expect `active` / `running` and no increasing restart count. Inspect service logs
locally if needed; logs can contain customer identifiers and must not be copied
unredacted into public issues or PRs.

## Intercom authentication

Run from the application directory on the server:

```sh
sudo -u "$ZIGNAL_APP_USER" venv/bin/python - <<'PYTHON'
from dotenv import dotenv_values
import requests

config = dotenv_values('.env')
headers = {'Authorization': 'Bearer ' + config['INTERCOM_ACCESS_TOKEN'],
           'Accept': 'application/json'}
for label, path in (('Authentication', 'me'),
                    ('Configured admin', 'admins/' + config['INTERCOM_ADMIN_ID'])):
    response = requests.get('https://api.intercom.io/' + path,
                            headers=headers, timeout=15)
    print(label, 'HTTP', response.status_code)
    response.raise_for_status()
PYTHON
```

Both should return 200. Check conversation writes with an authorized test account:
create a new conversation, verify the formatted acknowledgment and search hint,
send a follow-up to verify user attribution, and reply from a linked support
device to verify the internal device note.

## Credentials and persistent data

The application `.env` contains `SIGNAL_BRIDGE_NUMBER`, `INTERCOM_ACCESS_TOKEN`,
and `INTERCOM_ADMIN_ID`. Keep it untracked, owner-readable only, and never print
its values. Record shared credential locations in the private deployment config.
Do not assume old local tokens remain valid.

Back up configuration before changing it, outside the repository, using a unique
filename and mode `0600`. Preserve the application's ownership of `.env`.

Preserve the Signal container's mounted account data. Routine application updates
do not require container upgrades, volume deletion, or Signal relinking. Treat
Signal CLI upgrades as a separate maintenance task.

## Rollback

For a code-only update with a clean checkout:

```sh
sudo -u "$ZIGNAL_APP_USER" git switch --detach "$zignal_previous_commit" &&
systemctl restart "$ZIGNAL_SERVICE"
systemctl show "$ZIGNAL_SERVICE" -p ActiveState -p SubState -p NRestarts
```

This intentionally leaves the checkout detached. Review the failed release before
switching back to `main` for another deployment. Code rollback does not restore
configuration or dependencies; restore them separately only when needed. Never
restore a known-expired credential.
