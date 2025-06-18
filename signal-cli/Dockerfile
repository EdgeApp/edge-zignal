FROM eclipse-temurin:21-jre

# Install required dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Download and install prebuilt signal-cli
RUN curl -L -o /tmp/signal-cli.tar.gz https://github.com/AsamK/signal-cli/releases/latest/download/signal-cli-$(curl -s https://api.github.com/repos/AsamK/signal-cli/releases/latest | grep tag_name | cut -d '"' -f 4 | sed 's/v//').tar.gz \
    && tar -xzf /tmp/signal-cli.tar.gz -C /opt \
    && mv /opt/signal-cli-* /opt/signal-cli \
    && rm /tmp/signal-cli.tar.gz

# Download prebuilt libsignal-client native library for ARM64 Linux  
RUN curl -L -o /tmp/libsignal_jni.so.gz https://media.projektzentrisch.de/temp/signal-cli/libsignal_jni_so0732_ubuntu2004_arm64.gz \
    && gunzip /tmp/libsignal_jni.so.gz \
    && chmod +x /tmp/libsignal_jni.so \
    && mkdir -p /usr/local/lib \
    && mv /tmp/libsignal_jni.so /usr/local/lib/libsignal_jni.so

# Add signal-cli to PATH and set Java library path
ENV PATH="/opt/signal-cli/bin:${PATH}"
ENV JAVA_TOOL_OPTIONS="-Djava.library.path=/usr/local/lib"

# Create a volume for persistent data
VOLUME /root/.local/share/signal-cli

# Expose the JSON-RPC port
EXPOSE 8080

# Set the entrypoint
ENTRYPOINT ["sh", "-c"]
CMD ["signal-cli --config /root/.local/share/signal-cli daemon --http 0.0.0.0:8080"]
