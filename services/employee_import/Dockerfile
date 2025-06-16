# Use the base image as a parent image
FROM ecorrouge/rococo-service-host:python-3.10

# Path to employee_import
ARG SERVICEPATH=./services/employee_import

ENV PYTHONPATH /app

# Set execution type to MESSAGING
ENV EXECUTION_TYPE=MESSAGING
ENV MESSAGING_TYPE=SqsConnection
ENV PROCESSOR_TYPE=EmployeeImportProcessor
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
