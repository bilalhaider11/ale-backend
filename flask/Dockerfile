FROM python:3.11-bullseye

WORKDIR /api

ENV PIP_ROOT_USER_ACTION=ignore

RUN python -m pip install --upgrade pip

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | POETRY_HOME=/opt/poetry python && \
    cd /usr/local/bin && \
    ln -s /opt/poetry/bin/poetry && \
    poetry config virtualenvs.create false

RUN poetry --version

COPY ./flask/pyproject.toml ./flask/poetry.lock ./

# Allow installing dev dependencies to run tests
ARG INSTALL_DEV=false
RUN bash -c "if [ $INSTALL_DEV == 'true' ] ; then poetry install --no-root ; else poetry install --no-root ; fi"

COPY ./flask /api

COPY ./common /api/common

ENV PYTHONPATH /api

RUN chmod +x /api/docker-entrypoint.sh

# Run app.py when the container launches
ENV FLASK_APP app.py

ENTRYPOINT ["./docker-entrypoint.sh"]
