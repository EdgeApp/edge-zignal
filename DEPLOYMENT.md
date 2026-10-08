# Deploying Edge Zignal

Verified on October 8, 2026. This guide contains operational details, not credentials,
and can be committed to Git. The repository is public: the server IP, service
paths, and SSH username below are operational metadata, not authentication
secrets. SSH still requires an authorized private key. Keep tokens, `.env` files, and Signal account data out
of Git. No DigitalOcean API token is needed for the SSH workflow below.

## Server and services

| Item | Value |
| --- | --- |
| DigitalOcean team / project | Edge Tools |
| Droplet | `zignal` (ID `595176609`, SFO3, Ubuntu 24.04) |
| SSH | `ssh root@147.182.236.162` |
| Application checkout | `/home/edgy/apps/edge-zignal` |
| Repository | `https://github.com/EdgeApp/edge-zignal` |
| Deployment branch | `main` |
| Application service | `edge-zignal.service`, runs as `edgy` |
| Python | `/home/edgy/apps/edge-zignal/venv/bin/python` |
| Signal container | `signal-cli` |
| Signal REST API | `http://localhost:8090` on the droplet |

The existing SSH key on Jared's Mac works for `root`; direct SSH as `edgy` was
rejected. Run repository operations and tests as `edgy` to preserve ownership.
The DigitalOcean CLI credential could not list droplets (403); use SSH, or find
the server under DigitalOcean **Droplets → zignal**. A browser console is also
available on the droplet page if needed.

## Routine application deployment

Merge the approved PRs into `main` first. For stacked PRs, merge dependencies,
retarget/rebase the dependent PRs onto `main`, and check their final diffs before
merging. Do not merge unrelated open PRs.

Connect to the droplet, then run the following in the same shell:

```sh
ssh root@147.182.236.162
```

```sh
cd /home/edgy/apps/edge-zignal
sudo -u edgy git status --short
sudo -u edgy git branch --show-current
sudo -u edgy git rev-parse HEAD
systemctl is-active edge-zignal
docker ps --filter name=signal-cli --format '{{.Names}} {{.Status}}'
```

Stop if the checkout has unexpected changes or is not on `main`; preserve and
resolve them before continuing. Record the current commit for rollback:

```sh
zignal_previous_commit=$(sudo -u edgy git rev-parse HEAD)
sudo -u edgy git fetch origin
sudo -u edgy git log --oneline HEAD..origin/main
sudo -u edgy git diff HEAD origin/main -- requirements.txt systemd signal-cli/docker-compose.yml
```

If dependencies, service definitions, or container configuration changed, review
and handle those changes explicitly. The routine below assumes they did not.
It does not upgrade or restart the Signal container.

```sh
sudo -u edgy git merge --ff-only origin/main &&
sudo -u edgy venv/bin/python -m unittest discover -s tests -q &&
systemctl restart edge-zignal
```

Only restart after tests succeed. Then verify:

```sh
sudo -u edgy git rev-parse HEAD
sudo -u edgy git status --short
systemctl show edge-zignal -p ActiveState -p SubState -p NRestarts -p ExecMainStartTimestamp
curl --fail --silent --show-error --output /dev/null --write-out 'Signal health HTTP %{http_code}\n' http://localhost:8090/v1/health
```

Check service state again after a polling interval. Expect `active` / `running`
and no increasing restart count. If needed, inspect `journalctl -u edge-zignal
--since '5 minutes ago'` locally; logs may contain customer identifiers, so do not
paste raw logs into GitHub or shared documents.

## Check Intercom authentication without printing credentials

Run from the application directory on the server:

```sh
sudo -u edgy venv/bin/python - <<'PY'
from dotenv import dotenv_values
import requests

config = dotenv_values('.env')
headers = {
    'Authorization': 'Bearer ' + config['INTERCOM_ACCESS_TOKEN'],
    'Accept': 'application/json',
}
for label, path in (
    ('Authentication', 'me'),
    ('Configured admin', 'admins/' + config['INTERCOM_ADMIN_ID']),
):
    response = requests.get('https://api.intercom.io/' + path,
                            headers=headers, timeout=15)
    print(label, 'HTTP', response.status_code)
    response.raise_for_status()
PY
```

Both checks should return 200. These checks do not prove conversation write
permissions; finish with an authorized test account. Send a message that creates
a new conversation, verify the formatted Intercom creation/search hint, send a
follow-up and verify user attribution, then reply from a linked support device
and verify the internal device note. Existing conversations do not repeat the
creation hint.

## Credentials and persistent data

- Production configuration is `/home/edgy/apps/edge-zignal/.env`.
- A local `.env` may exist in the checkout and is gitignored. It contains
  `SIGNAL_BRIDGE_NUMBER`, `INTERCOM_ACCESS_TOKEN`, and `INTERCOM_ADMIN_ID`.
  Do not assume its token is current: the earlier local token failed authentication.
- Jared's shared local Intercom credential file is
  `~/.config/intercom/credentials.env`; this is a local source, not a server path.
- Never print token values, include them in command arguments, or commit them.
- Before changing production configuration, back it up outside the checkout in
  `/root/edge-zignal-deploy-backups/`, with a unique filename and mode `0600`.
  Preserve `.env` ownership (`edgy`) and restart the bridge after an intentional
  configuration change.
- Preserve the Signal container's mounted account data. Application deployments
  do not require relinking Signal, deleting containers/volumes, or pulling a new
  `latest` image. Treat Signal CLI upgrades as a separate maintenance task.

## Rollback

For a code-only deployment, with a clean checkout, use the previous commit saved
above (or the recorded known-good full commit if using a new shell):

```sh
sudo -u edgy git switch --detach "$zignal_previous_commit" &&
systemctl restart edge-zignal
systemctl show edge-zignal -p ActiveState -p SubState -p NRestarts
```

This preserves branch history and leaves the checkout detached intentionally.
Before the next deployment, explicitly switch back to `main` after reviewing the
failed release. Code rollback does not revert configuration or dependencies;
restore those separately only if necessary. Do not restore an expired token.

## Verified deployment history

On October 8, 2026, PRs #5–#9 were merged and deployed at commit `2793984`.
All 20 mocked tests passed on the server, the bridge was active with zero
restarts, and Signal device lookup returned 200. The old Intercom token returned
401 and was replaced with the working shared credential; authentication and
configured-admin checks then returned 200. The old configuration backup is
`/root/edge-zignal-deploy-backups/env.pre-deploy-2793984`.

The customer-facing Signal acknowledgment remained unchanged in that deployment.

Later on October 8, 2026, PR #10 deployed the approved customer acknowledgment
formatting at `fe3d70d`. All 21 tests passed on the server; the restarted bridge
was active with zero restarts. Sending now uses `/v2/send` with styled text.
