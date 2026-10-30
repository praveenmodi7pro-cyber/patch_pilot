FROM python:3.12-slim

# Hardened unprivileged sandbox user
RUN useradd -u 1000 -m -s /bin/bash sandbox

WORKDIR /workspace

# Install common testing runtimes
RUN pip install --no-cache-dir \
    pytest>=8.0.0 \
    ruff>=0.5.0

# Drop to unprivileged sandbox user
USER sandbox

CMD ["pytest", "-v"]

