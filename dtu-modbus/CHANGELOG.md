# Changelog

## 0.2.1

- Fix s6-overlay PID 1 conflict: set `init: false` so HA Supervisor doesn't inject tini

## 0.2.0

- Fix s6-overlay v3 compatibility (register as proper longrun service)
- Fix /data mount conflict (code moved to /app)
- Add deterministic entity naming with object_id
- Add local dev config support (options_local.json)
- Clean up config path resolution

## 0.1.0

- Initial release
- Reads per-port DC data from Hoymiles DTU via Modbus TCP
- Publishes to MQTT with Home Assistant auto-discovery
- Supports 10 per-port sensors and 3 plant-level sensors
