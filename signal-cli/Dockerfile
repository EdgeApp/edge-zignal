FROM eclipse-temurin:21-jdk-alpine

# Install required dependencies
RUN apk add --no-cache \
    bash \
    curl \
    git \
    gradle \
    openjdk21-jre

# Clone the signal-cli repository
RUN git clone https://github.com/AsamK/signal-cli.git /signal-cli

# Build signal-cli
WORKDIR /signal-cli
RUN ./gradlew build

# Create a volume for persistent data
VOLUME /root/.local/share/signal-cli

# Expose the JSON-RPC port
EXPOSE 8080

# Set the entrypoint
ENTRYPOINT ["/signal-cli/build/install/signal-cli/bin/signal-cli"]
CMD ["--config", "/root/.local/share/signal-cli", "daemon", "--json-rpc"] 