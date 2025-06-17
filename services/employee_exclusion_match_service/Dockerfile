# Use the base image as a parent image
FROM ecorrouge/rococo-service-host:latest

# Path to employee_exclusion_match_service
ARG SERVICEPATH=./services/employee_exclusion_match_service

ENV PYTHONPATH /app

# ENV EXECUTION_TYPE can be either `MESSAGING` or `CRON`
ENV EXECUTION_TYPE=MESSAGING
# ENV MESSAGING_TYPE is required, which should be either `SqsConnection` or `RabbitMqConnection`.
ENV MESSAGING_TYPE=RabbitMqConnection

ENV PROCESSOR_TYPE=EmployeeExclusionMatchProcessor
ENV PROCESSOR_MODULE=processor

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
