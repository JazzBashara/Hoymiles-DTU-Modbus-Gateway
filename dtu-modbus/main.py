"""Hoymiles DTU Modbus Gateway - reads per-port data via Modbus TCP, publishes to MQTT."""

__version__ = "0.1.0"

import json
import logging
import os
import ssl
import time

import paho.mqtt.client as mqtt
from hoymiles_modbus.client import HoymilesModbusTCP

from const import (
    DISCOVERY_INTERVAL,
    MQTT_BASE_TOPIC,
    MQTT_DISCOVERY_PREFIX,
    PLANT_SENSORS,
    PORT_SENSORS,
    SHORT_NAME,
    build_device_info,
    build_discovery_payload,
)

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("HoymilesDTU")


def get_config() -> dict:
    """Load configuration from /data/options.json (HA add-on) or ./config.json (local dev)."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    for path in ["/data/options.json", os.path.join(script_dir, "options_local.json"), os.path.join(script_dir, "config.json")]:
        if os.path.isfile(path):
            with open(path) as f:
                cfg = json.load(f)
            # config.json is the HA manifest; extract nested "options" for local dev
            if "options" in cfg and "DTU_HOST" not in cfg:
                cfg = cfg["options"]
            # When running inside HA, pull MQTT creds from bashio env vars
            if not cfg.get("External_MQTT_Server"):
                cfg["MQTT_Host"] = os.environ.get("MQTT_HOST_HA", cfg.get("MQTT_Host", ""))
                cfg["MQTT_User"] = os.environ.get("MQTT_USER_HA", cfg.get("MQTT_User", ""))
                cfg["MQTT_Pass"] = os.environ.get("MQTT_PASSWORD_HA", cfg.get("MQTT_Pass", ""))
            logger.info("Loaded config from %s", path)
            return cfg
    raise FileNotFoundError("No config file found at /data/options.json or ./config.json")


def read_dtu(host: str, port: int = 502):
    """Read plant data from DTU via Modbus TCP."""
    hm = HoymilesModbusTCP(host, port)
    return hm.plant_data


def connect_mqtt(cfg: dict) -> mqtt.Client:
    """Create, configure, and connect the MQTT client."""
    client = mqtt.Client(client_id="hoymiles_dtu_modbus", clean_session=True, protocol=mqtt.MQTTv31)
    client.username_pw_set(cfg["MQTT_User"], cfg["MQTT_Pass"])

    if cfg.get("MQTT_TLS"):
        context = ssl.SSLContext(protocol=ssl.PROTOCOL_TLSv1_2)
        client.tls_set_context(context)
        broker_port = int(cfg.get("MQTT_TLS_PORT", 8883))
    else:
        broker_port = 1883

    client.on_connect = lambda c, u, f, rc: logger.info("MQTT connected (rc=%s)", rc)
    client.on_disconnect = lambda c, u, rc: logger.warning("MQTT disconnected (rc=%s)", rc)

    client.connect(cfg["MQTT_Host"], broker_port, keepalive=60)
    client.loop_start()
    return client


def publish_discovery(client: mqtt.Client, plant_data, expire_after: int):
    """Publish HA MQTT auto-discovery configs for all ports and plant-level sensors."""
    dtu_sn = str(plant_data.dtu)
    dtu_device = build_device_info(f"Hoymiles DTU {dtu_sn[-4:]}", dtu_sn, model="DTU-Pro-S")

    # Plant-level sensors
    dtu_short = dtu_sn[-4:]
    plant_topic = f"{MQTT_BASE_TOPIC}/{dtu_sn}/plant"
    for sensor in PLANT_SENSORS:
        key = sensor[0]
        uniq_id = f"{SHORT_NAME}_{dtu_sn}_{key}"
        obj_id = f"dtu_{dtu_short}_{key}"
        disco_topic = f"{MQTT_DISCOVERY_PREFIX}/sensor/{MQTT_BASE_TOPIC}/{uniq_id}/config"
        payload = build_discovery_payload(sensor, uniq_id, plant_topic, key, dtu_device, expire_after, obj_id)
        client.publish(disco_topic, json.dumps(payload), retain=True)

    # Per-port sensors
    for inv in plant_data.inverters:
        sn = str(inv.serial_number)
        sn_short = sn[-4:]
        port_num = inv.port_number
        port_id = f"{sn}_port{port_num}"
        state_topic = f"{MQTT_BASE_TOPIC}/{sn}/port_{port_num}"

        port_device = build_device_info(
            f"Inverter {sn_short} Port {port_num}",
            port_id,
            via_device=dtu_sn,
        )

        for sensor in PORT_SENSORS:
            key = sensor[0]
            uniq_id = f"{SHORT_NAME}_{port_id}_{key}"
            obj_id = f"inverter_{sn_short}_port_{port_num}_{key}"
            disco_topic = f"{MQTT_DISCOVERY_PREFIX}/sensor/{MQTT_BASE_TOPIC}/{uniq_id}/config"
            payload = build_discovery_payload(sensor, uniq_id, state_topic, key, port_device, expire_after, obj_id)
            client.publish(disco_topic, json.dumps(payload), retain=True)

    logger.debug("Discovery published for DTU %s with %d ports", dtu_sn, len(plant_data.inverters))


def publish_data(client: mqtt.Client, plant_data):
    """Publish current sensor values as JSON to state topics."""
    dtu_sn = str(plant_data.dtu)

    # Plant-level
    plant_payload = {
        "pv_power": float(plant_data.pv_power),
        "today_production": int(plant_data.today_production),
        "total_production": round(int(plant_data.total_production) / 1000, 2),
    }
    client.publish(f"{MQTT_BASE_TOPIC}/{dtu_sn}/plant", json.dumps(plant_payload))

    # Per-port
    for inv in plant_data.inverters:
        sn = str(inv.serial_number)
        port_payload = {
            "dc_voltage": float(inv.pv_voltage),
            "dc_current": float(inv.pv_current),
            "dc_power": float(inv.pv_power),
            "grid_voltage": float(inv.grid_voltage),
            "grid_frequency": float(inv.grid_frequency),
            "temperature": float(inv.temperature),
            "today_production": int(inv.today_production),
            "total_production": round(int(inv.total_production) / 1000, 2),
            "operating_status": int(inv.operating_status),
            "alarm_code": int(inv.alarm_code),
        }
        client.publish(f"{MQTT_BASE_TOPIC}/{sn}/port_{inv.port_number}", json.dumps(port_payload))

    logger.info(
        "Published data: PV=%.1fW, ports=%d",
        float(plant_data.pv_power),
        len(plant_data.inverters),
    )


def main():
    cfg = get_config()
    logger.setLevel(cfg.get("LOG_LEVEL", "INFO"))
    logger.info("Hoymiles DTU Modbus Gateway v%s starting", __version__)

    dtu_host = cfg["DTU_HOST"]
    dtu_port = int(cfg.get("DTU_PORT", 502))
    poll_interval = max(int(cfg.get("POLLING_TIME", 35)), 30)
    expire_after = int(poll_interval * 3)

    mqtt_client = connect_mqtt(cfg)
    time.sleep(1)  # Allow MQTT connection to establish

    last_discovery = 0

    while True:
        try:
            plant_data = read_dtu(dtu_host, dtu_port)

            now = time.time()
            if now - last_discovery >= DISCOVERY_INTERVAL:
                publish_discovery(mqtt_client, plant_data, expire_after)
                last_discovery = now

            publish_data(mqtt_client, plant_data)

        except Exception:
            logger.exception("Error reading DTU or publishing data")

        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
