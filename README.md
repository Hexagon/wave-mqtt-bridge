# Airthings Wave MQTT Bridge

Based on wave-reader by Airthings, https://github.com/Airthings/wave-reader.

Dockerized client that reads airthings wave, and sends the result to a MQTT broker at a selected interval.

# Development setup

1. First, setup docker and bluez on the host computer.

2. Get the code.

```bash
git checkout https://github.com/Hexagon/wave-mqtt-bridge.git
cd wave-mqtt-bridge.git
```

3. Build docker image

```bash
docker build -q . --tag="wave-mqtt-bridge"
```

4. Create docker container

wave-mqtt-bridge is configured by passing environment variables to the docker container. AW_SERIAL (Airthings wave 10-digit serial number) and MQTT_HOST and at leasy one of MQTT_TOPIC_RADON_* is mandatory for a working setup.

## Available environment varhiables

Variable | Default
--- | ---
AW_SEIRAL | -
AW_INTERVAL_S | 60
MQTT_HOST | -
MQTT_PORT | -
MQTT_USER | -
MQTT_PASS | -
MQTT_TOPIC_RADON_LT | -
MQTT_TOPIC_RADON_ST | -
MQTT_TOPIC_RADON_TEMPERATURE | -
MQTT_TOPIC_RADON_HOMIDITY | -

Example container setup

```bash
docker run \
	-d \
	--net=host \
	--restart=always \
	-e AW_SERIAL=0000000000 \
	-e MQTT_HOST=X.Y.Z.N \
	-e MQTT_TOPIC_RADON_ST="sensor/radon/st" \
	-e MQTT_TOPIC_RADON_TEMPERATURE="sensor/radon/temp" \
	-e MQTT_TOPIC_RADON_HUMIDITY="sensor/radon/humidity" \
	--privileged \
	--name="wave-monitor" \
	wave-mqtt-bridge
```

5. Check logs

```bash
docker logs wave-monitor
```