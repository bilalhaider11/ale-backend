# Use the base image as a parent image
FROM ecorrouge/rococo-service-host:python-3.11

# Path to oig_verifier
ARG SERVICEPATH=./services/oig_verifier

ENV PYTHONPATH /app

ENV EXECUTION_TYPE=MESSAGING
ENV MESSAGING_TYPE=RabbitMqConnection
ENV PROCESSOR_TYPE=OigVerifierProcessor
ENV PROCESSOR_MODULE=processor

# Install Chrome and dependencies for Selenium
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Create screenshots directory
RUN mkdir -p /app/screenshots

WORKDIR /app

COPY ${SERVICEPATH}/pyproject.toml ${SERVICEPATH}/poetry.lock* ./

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root; fi"

COPY ${SERVICEPATH} ./src

COPY ./common ./src/common

COPY ${SERVICEPATH}/docker-entrypoint.sh ./

RUN chmod +x ./docker-entrypoint.sh

ENTRYPOINT ["./docker-entrypoint.sh"] 