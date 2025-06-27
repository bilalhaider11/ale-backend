# Use the base image as a parent image
FROM ecorrouge/rococo-service-host:python-3.11

# Path to oig_update_check
ARG SERVICEPATH=./services/oig_update_check

ENV PYTHONPATH /app

ENV EXECUTION_TYPE=CRON
ENV CRON_TIME_AMOUNT=1
ENV CRON_TIME_UNIT=days
ENV CRON_RUN_AT=02:00:00
ENV RUN_AT_STARTUP=true

ENV PROCESSOR_TYPE=OigUpdateCheckProcessor
ENV PROCESSOR_MODULE=processor

WORKDIR /app

COPY ${SERVICEPATH}/pyproject.toml ${SERVICEPATH}/poetry.lock* ./

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root --only main ; fi"

COPY ${SERVICEPATH} ./src

COPY ./common ./src/common

COPY ${SERVICEPATH}/docker-entrypoint.sh ./

RUN chmod +x ./docker-entrypoint.sh

ENTRYPOINT ["./docker-entrypoint.sh"]
