# Signal CLI Docker Setup

This is a Docker setup for running the Signal CLI daemon with JSON-RPC interface.

## Prerequisites

- Docker
- Docker Compose

## Setup

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

4. The Signal CLI daemon will be running and accessible at http://localhost:8080

## Data Persistence

The Signal CLI data is stored in the `./data` directory and is persisted between container restarts.

## Stopping the Container

```bash
docker-compose down
```

## Notes

- The container exposes port 8080 for the JSON-RPC interface
- All Signal CLI data is stored in the `./data` directory
- The container will automatically restart unless explicitly stopped 