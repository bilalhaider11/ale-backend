#!/bin/sh

# Create Rabbitmq user
( rabbitmqctl wait --timeout 60 "$RABBITMQ_PID_FILE" ; \
rabbitmqctl add_user "$RABBITMQ_USER" "$RABBITMQ_PASSWORD" 2>/dev/null ; \
rabbitmqctl set_user_tags "$RABBITMQ_USER" administrator ; \
rabbitmqctl add_vhost "$RABBITMQ_VIRTUAL_HOST" ; \
rabbitmqctl set_permissions -p "$RABBITMQ_VIRTUAL_HOST" "$RABBITMQ_USER"  ".*" ".*" ".*" ; \
echo "*** User '$RABBITMQ_USER' with password '$RABBITMQ_PASSWORD' completed. ***") &

# Set the RabbitMQ configuration file
RABBITMQ_CONFIG_FILE="/etc/rabbitmq/rabbitmq.conf"

# Create a custom RabbitMQ configuration file
echo "listeners.tcp.default = ${RABBITMQ_PORT}" > "${RABBITMQ_CONFIG_FILE}"

# $@ is used to pass arguments to the rabbitmq-server command.
# For example: docker run -d rabbitmq arg1 arg2,
# it will be same as running in the container rabbitmq-server arg1 arg2
rabbitmq-server "$@"
