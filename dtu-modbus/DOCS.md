# Hoymiles DTU Modbus Gateway

Reads per-port DC power data from a Hoymiles DTU (e.g. DTU-Pro-S) via Modbus TCP and publishes it to MQTT with Home Assistant auto-discovery.

This gives **per-panel granularity** (individual DC voltage, current, and power per inverter port) that the Hoymiles cloud API cannot provide.

## Requirements

- Hoymiles DTU with Modbus TCP enabled (port 502)
  - Tested with DTU-Pro-S
- MQTT broker (Mosquitto add-on or external)
- Home Assistant with MQTT integration configured

## Configuration

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `DTU_HOST` | string | *required* | IP address of the DTU |
| `DTU_PORT` | int | `502` | Modbus TCP port |
| `External_MQTT_Server` | bool | `false` | Use external MQTT broker instead of HA's |
| `MQTT_Host` | string | from HA | Broker IP (only needed if external) |
| `MQTT_User` | string | from HA | MQTT username (only needed if external) |
| `MQTT_Pass` | string | from HA | MQTT password (only needed if external) |
| `MQTT_TLS` | bool | `false` | Enable TLS for MQTT connection |
| `MQTT_TLS_PORT` | int | `8883` | MQTT TLS port |
| `POLLING_TIME` | int | `35` | Seconds between Modbus reads (minimum 30) |
| `LOG_LEVEL` | list | `INFO` | Log verbosity: DEBUG, INFO, WARNING, ERROR |

## Sensors

### Per Inverter Port

Each microinverter port appears as its own device in Home Assistant. For example, an HMS-1600-4T with 4 ports creates 4 devices, each with:

| Sensor | Unit | Description |
|--------|------|-------------|
| DC Voltage | V | Panel voltage |
| DC Current | A | Panel current |
| DC Power | W | Panel power output |
| Grid Voltage | V | AC grid voltage |
| Grid Frequency | Hz | AC grid frequency |
| Temperature | C | Inverter temperature |
| Today Production | Wh | Energy produced today |
| Total Production | kWh | Lifetime energy produced |
| Operating Status | - | Inverter status code |
| Alarm Code | - | Active alarm code |

### Plant Level

Aggregate sensors for the entire DTU:

| Sensor | Unit | Description |
|--------|------|-------------|
| PV Power | W | Total current PV power |
| Today Production | Wh | Total energy produced today |
| Total Production | kWh | Total lifetime energy produced |

## MQTT Topics

- Discovery: `homeassistant/sensor/hoymiles_dtu/{id}/config`
- Port state: `hoymiles_dtu/{inverter_sn}/port_{N}` (JSON)
- Plant state: `hoymiles_dtu/{dtu_sn}/plant` (JSON)

## Notes

- The DTU firmware enforces a minimum interval of ~30 seconds between Modbus reads. Setting `POLLING_TIME` below 30 will be clamped to 30.
- Discovery messages are republished every 5 minutes to ensure HA picks up entities after restarts.
- `host_network: true` is required so the add-on container can reach the DTU on the local network.

## Local Development

To test outside of Home Assistant, create a `config.json` in the `dtu-modbus` directory with your settings:

```json
{
  "DTU_HOST": "192.168.1.100",
  "DTU_PORT": 502,
  "External_MQTT_Server": true,
  "MQTT_Host": "192.168.1.200",
  "MQTT_User": "mqtt_user",
  "MQTT_Pass": "mqtt_pass",
  "MQTT_TLS": false,
  "POLLING_TIME": 35,
  "LOG_LEVEL": "DEBUG"
}
```

Then run:

```bash
cd dtu-modbus
pip install hoymiles_modbus==0.9.1 paho-mqtt==1.6.1
python3 main.py
```
