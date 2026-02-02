#!/usr/bin/with-contenv bashio
set +u

bashio::log.green "Starting Hoymiles DTU Modbus Gateway..."

CONFIG_PATH=/data/options.json

export MQTT_HOST_HA=$(bashio::services mqtt "host")
export MQTT_USER_HA=$(bashio::services mqtt "username")
export MQTT_PASSWORD_HA=$(bashio::services mqtt "password")

exec python3 /app/main.py
