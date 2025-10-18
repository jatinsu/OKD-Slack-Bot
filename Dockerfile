# Stage 1: Get goose binary
FROM ghcr.io/block/goose:main-35c3f69 AS goose

# Stage 2: Build application image
FROM fedora:latest

# Copy goose from the first stage
COPY --from=goose /usr/local/bin/goose /usr/local/bin/goose

# Install Python and other dependencies including X11/xcb libraries for goose
RUN dnf install -y python3 python3-pip curl ca-certificates libxcb && dnf clean all

# Set working directory
WORKDIR /app

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY app.py .
COPY custom-prompt.txt .

# Create output directory
RUN mkdir -p /app/output

# Set environment variables (will be overridden by OpenShift secrets)
ENV SLACK_BOT_TOKEN=""
ENV SLACK_APP_TOKEN=""
ENV SLACK_CHANNEL_ID=""
ENV GOOGLE_API_KEY="" 

# Create goose config directory and copy config file
# Goose looks for config in ~/.config/goose/config.yaml (user's home directory)
RUN mkdir -p /root/.config/goose
COPY goose-config.yaml /root/.config/goose/config.yaml

# Expose port (not strictly necessary for socket mode, but good practice)
EXPOSE 3000


# Run the application
CMD ["goose", "run", "-t", "Hello, world!"]
# CMD ["goose", "--version"]