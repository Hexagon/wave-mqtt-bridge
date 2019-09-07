# Airthings Wave/Wave Plus MQTT Bridge

Based on wave-reader and wave-plus-reader by Airthings, https://github.com/Airthings/wave-reader, https://github.com/Airthings/waveplus-reader.

Dockerized client that reads airthings wave/wave plus, and sends the result to a MQTT broker at a selected interval.

NOTE! Wave Plus is untested, please test and report back whether it works or not.

# Quick start

You'll need your airthings wave serial number (written on the device itself), IP address of a running mqtt broker and a working docker environment. Then you're good to go.

```bash
docker run \
	-d \
	--net=host \
	--restart=always \
	-e AW_TYPE="WAVE" \
	-e AW_SERIAL=0000000000 \
	-e MQTT_HOST=X.Y.Z.N \
	-e MQTT_TOPIC_RADON_ST="sensor/radon/st" \
	-e MQTT_TOPIC_TEMPERATURE="sensor/radon/temp" \
	-e MQTT_TOPIC_HUMIDITY="sensor/radon/humidity" \
	--privileged \
	--name="wave-monitor" \
	hexagon/wave-mqtt-bridge
```

These environment variables can be changed to customize your setup 

Variable | Default
--- | ---
AW_SEIRAL | -
AW_INTERVAL_S | 300
AW_TYPE | WAVE
MQTT_HOST | -
MQTT_PORT | -
MQTT_USER | -
MQTT_PASS | -
MQTT_TOPIC_RADON_LT | -
MQTT_TOPIC_RADON_ST | -
MQTT_TOPIC_TEMPERATURE | -
MQTT_TOPIC_HUMIDITY | -
MQTT_TOPIC_PRESSURE | -
MQTT_TOPIC_CO2 | -
MQTT_TOPIC_VOC | -

## Debugging

This assumes you've named your container "wave-monitor"

```bash
docker logs wave-monitor
```

# Development setup

Setup docker and bluez on the host computer, detailed walk through available at https://github.com/Airthings/wave-reader.

Get the code.

```bash
git checkout https://github.com/Hexagon/wave-mqtt-bridge.git
cd wave-mqtt-bridge
```

Build docker image

```bash
docker build -q . --tag="wave-mqtt-bridge"
```

Create docker container

wave-mqtt-bridge is configured by passing environment variables to the docker container. AW_TYPE (WAVE or WAVEPLUS), AW_SERIAL (Airthings wave 10-digit serial number), MQTT_HOST and at leasy one of MQTT_TOPIC_* is mandatory for a working setup.

Example container setup

```bash
docker run \
	-d \
	--net=host \
	--restart=always \
	-e AW_TYPE="WAVE" \
	-e AW_SERIAL=0000000000 \
	-e MQTT_HOST=X.Y.Z.N \
	-e MQTT_TOPIC_RADON_ST="sensor/radon/st" \
	-e MQTT_TOPIC_TEMPERATURE="sensor/radon/temp" \
	-e MQTT_TOPIC_HUMIDITY="sensor/radon/humidity" \
	--privileged \
	--name="wave-monitor" \
	wave-mqtt-bridge
```

