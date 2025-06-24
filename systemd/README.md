# Auto-start via SystemD

For the app:

```sh
sudo cp edge-zignal.service /etc/systemd/system/
sudo systemctl daemon-reexec
sudo systemctl enable --now edge-zignal
```

For the docker image:

```sh
sudo cp signal-cli.service /etc/systemd/system/
sudo systemctl daemon-reexec
sudo systemctl enable --now signal-cli
```
