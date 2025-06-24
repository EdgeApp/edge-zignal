# Signal CLI Docker Setup

This is a Docker setup for running the Signal CLI daemon with JSON-RPC interface.

## Prerequisites

```sh
sudo apt install docker-compose
sudo apt install catimg
```

## Setup

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

## Stopping the Container

```sh
docker-compose down
```

## Notes

- The container exposes port 8090 for the JSON-RPC interface
- All Signal CLI data is stored in the `./data` directory
- The container will automatically restart unless explicitly stopped 