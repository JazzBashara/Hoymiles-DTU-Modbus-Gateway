"""Constants and sensor definitions for Hoymiles DTU Modbus Gateway."""

MQTT_DISCOVERY_PREFIX = "homeassistant"
MQTT_BASE_TOPIC = "hoymiles_dtu"
SHORT_NAME = "hmdtu"

DISCOVERY_INTERVAL = 300  # Republish discovery every 5 minutes

# Per-port sensor definitions: (key, name, device_class, unit, state_class, icon)
PORT_SENSORS = [
    ("dc_voltage", "DC Voltage", "voltage", "V", "measurement", "mdi:solar-panel"),
    ("dc_current", "DC Current", "current", "A", "measurement", "mdi:current-dc"),
    ("dc_power", "DC Power", "power", "W", "measurement", "mdi:solar-power"),
    ("grid_voltage", "Grid Voltage", "voltage", "V", "measurement", "mdi:flash-triangle"),
    ("grid_frequency", "Grid Frequency", "frequency", "Hz", "measurement", "mdi:sine-wave"),
    ("temperature", "Temperature", "temperature", "\u00b0C", "measurement", "mdi:thermometer"),
    ("today_production", "Today Production", "energy", "Wh", "total_increasing", "mdi:solar-power-variant"),
    ("total_production", "Total Production", "energy", "kWh", "total_increasing", "mdi:counter"),
    ("operating_status", "Operating Status", None, None, None, "mdi:information-outline"),
    ("alarm_code", "Alarm Code", None, None, None, "mdi:alert-circle-outline"),
]

# Plant-level sensor definitions
PLANT_SENSORS = [
    ("pv_power", "PV Power", "power", "W", "measurement", "mdi:solar-power"),
    ("today_production", "Today Production", "energy", "Wh", "total_increasing", "mdi:solar-power-variant"),
    ("total_production", "Total Production", "energy", "kWh", "total_increasing", "mdi:counter"),
]


def build_discovery_payload(sensor, uniq_id, state_topic, value_key, device_info, expire_after, object_id=None):
    """Build a single HA MQTT discovery payload dict."""
    key, name, device_class, unit, state_class, icon = sensor
    payload = {
        "name": name,
        "unique_id": uniq_id,
        "object_id": object_id or uniq_id,
        "state_topic": state_topic,
        "value_template": "{{ value_json." + value_key + " }}",
        "icon": icon,
        "device": device_info,
    }
    if device_class:
        payload["device_class"] = device_class
    if unit:
        payload["unit_of_measurement"] = unit
    if state_class:
        payload["state_class"] = state_class
    if expire_after:
        payload["expire_after"] = expire_after
    return payload


def build_device_info(name, identifiers, model=None, manufacturer="Hoymiles", via_device=None):
    """Build HA device info dict."""
    info = {
        "name": name,
        "identifiers": [identifiers],
        "manufacturer": manufacturer,
    }
    if model:
        info["model"] = model
    if via_device:
        info["via_device"] = via_device
    return info
