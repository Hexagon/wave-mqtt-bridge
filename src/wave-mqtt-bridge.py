# MIT License
#
# Copyright (c) 2019 Hexagon <Hexagon@GitHub>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.


import wave
import waveplus

from datetime import datetime
import paho.mqtt.publish as publish
import logging
import os
import sys
import time

# Read environment
mqtt_host = os.getenv('MQTT_HOST')
mqtt_port = os.getenv('MQTT_PORT', 1883)
mqtt_user = os.getenv('MQTT_USER')
mqtt_pass = os.getenv('MQTT_PASS')
mqtt_topic_lt = os.getenv('MQTT_TOPIC_RADON_LT')
mqtt_topic_st = os.getenv('MQTT_TOPIC_RADON_ST')
mqtt_topic_t = os.getenv('MQTT_TOPIC_TEMPERATURE')
mqtt_topic_h = os.getenv('MQTT_TOPIC_HUMIDITY')
mqtt_topic_p = os.getenv('MQTT_TOPIC_PRESSURE')
mqtt_topic_c = os.getenv('MQTT_TOPIC_CO2')
mqtt_topic_v = os.getenv('MQTT_TOPIC_VOC')
aw_serial = os.getenv('AW_SERIAL')
aw_type = os.getenv('AW_TYPE')
wavemon_logfile = os.getenv('WM_LOGFILE')
wavemon_interval_s = os.getenv('VM_INTERVAL_S')

# Set up logging
if wavemon_logfile != "None":
    logging.basicConfig(level=logging.DEBUG, filename=wavemon_logfile, filemode='w', format='%(name)s - %(asctime)s - %(levelname)s - %(message)s')
else:
    logging.basicConfig(level=logging.DEBUG)

# Log environment
logging.info("Config: MQTT_HOST resolved to %s", mqtt_host)
logging.info("Config: WM_LOGFILE resolved to %s", wavemon_logfile)
logging.info("Config: WM_INTERVAL_S resolved to %s", wavemon_interval_s)

# Check environment variables
if wavemon_interval_s == None:
    logging.info("AW_INTERVAL_S defaulted to 300s (5m)");
    wavemon_interval_s = "300"

if wavemon_interval_s.isdigit() is not True:
    logging.info("AW_INTERVAL_S must be numerical");
    sys.exit(1)
else:
    wavemon_interval_s = int(wavemon_interval_s)

if wavemon_interval_s < 30:
    logging.info("AW_INTERVAL_S cannot be lower than 30s");
    sys.exit(1)

if aw_serial == None:
    logging.info("Missing AW_SERIAL");
    sys.exit(1)

if len(aw_serial) < 3:
    logging.info("Missing AW_SERIAL");
    sys.exit(1)

if aw_serial.isdigit() is not True or len(aw_serial) != 10:
    logging.info("AW_SERIAL has invalid format");
    sys.exit(1)

if aw_type != "WAVE" and aw_type != "WAVEPLUS":
    logging.error("AW_TYPE defaulting to WAVE")
    aw_TYPE = "WAVE"

if mqtt_host != None:
    logging.info("MQTT publishing enabled")

    # Log extended environment for MQTT
    logging.info("Config: MQTT_PORT resolved to %s", mqtt_port)
    logging.info("Config: MQTT_USER resolved to %s", mqtt_user)
    # logging.info("Config: MQTT_PASS resolved to ", mqtt_pass)
    logging.info("Config: MQTT_TOPIC_RADON_LT resolved to %s", mqtt_topic_lt)
    logging.info("Config: MQTT_TOPIC_RADON_ST resolved to %s", mqtt_topic_st)
    logging.info("Config: MQTT_TOPIC_TEMPERATURE resolved to %s", mqtt_topic_t)
    logging.info("Config: MQTT_TOPIC_HUMIDITY resolved to %s", mqtt_topic_h)
    logging.info("Config: MQTT_TOPIC_PRESSURE resolved to %s", mqtt_topic_p)
    logging.info("Config: MQTT_TOPIC_CO2 resolved to %s", mqtt_topic_c)
    logging.info("Config: MQTT_TOPIC_VOC resolved to %s", mqtt_topic_v)

def publish_mqtt(w_st,w_lt,w_temp,w_humidity,w_pressure,w_co2,w_voc):
    
    mqtt_msgs = []
    mqtt_auth = None
    if mqtt_user != None:
        mqtt_auth = {'username':mqtt_user, 'password':mqtt_pass}
    if mqtt_topic_lt != None:
        mqtt_msgs.append((mqtt_topic_lt,w_lt,1,False))
    if mqtt_topic_st != None:
        mqtt_msgs.append((mqtt_topic_st,w_st,1,False))
    if mqtt_topic_t != None:
        mqtt_msgs.append((mqtt_topic_t,w_temp,1,False))
    if mqtt_topic_h != None:
        mqtt_msgs.append((mqtt_topic_h,w_humidity,1,False))
    if mqtt_topic_p != None:
        mqtt_msgs.append((mqtt_topic_p,w_pressure,1,False))
    if mqtt_topic_c != None:
        mqtt_msgs.append((mqtt_topic_c,w_co2,1,False))
    if mqtt_topic_v != None:
        mqtt_msgs.append((mqtt_topic_v,w_voc,1,False))
    try:
        publish.multiple(mqtt_msgs, hostname=mqtt_host, port=mqtt_port, client_id="wavemqttbridge", auth=mqtt_auth, tls=None)
    except Exception as ex:
        logging.error('Exception while publishing to MQTT broker: {}'.format(ex))

while True:
    
    start = datetime.now()

    # Use regular Wave
    if aw_type == "WAVE":
        try:
            w = wave.Wave(aw_serial)
            w.connect()

            date_time    = w.read(wave.SENSOR_IDX_DATETIME)
            humidity     = w.read(wave.SENSOR_IDX_HUMIDITY)
            temperature  = w.read(wave.SENSOR_IDX_TEMPERATURE)
            radon_st_avg = w.read(wave.SENSOR_IDX_RADON_ST_AVG)
            radon_lt_avg = w.read(wave.SENSOR_IDX_RADON_LT_AVG)

            if mqtt_host != None:
                publish_mqtt(radon_st_avg,radon_lt_avg,temperature,humidity,None,None,None)

        except Exception as ex:
            logging.error('Exception while communicating with wave: {}'.format(ex))

        finally:
            w.disconnect()


    # User Wave Plus
    if aw_type == "WAVEPLUS": 
        try:
            wp = waveplus.WavePlus(SerialNumber)
                
            wp.connect()
            
            # read values
            sensors = wp.read()
            
            # extract
            date_time    = datetime.now()
            humidity     = sensors.getValue(waveplus.SENSOR_IDX_HUMIDITY)
            radon_st_avg = sensors.getValue(waveplus.SENSOR_IDX_RADON_SHORT_TERM_AVG)
            radon_lt_avg = sensors.getValue(waveplus.SENSOR_IDX_RADON_LONG_TERM_AVG)
            temperature  = sensors.getValue(waveplus.SENSOR_IDX_TEMPERATURE)
            pressure     = sensors.getValue(waveplus.SENSOR_IDX_REL_ATM_PRESSURE)
            CO2_lvl      = sensors.getValue(waveplus.SENSOR_IDX_CO2_LVL)
            VOC_lvl      = sensors.getValue(waveplus.SENSOR_IDX_VOC_LVL)
            
            # Print data
            if mqtt_host != None:
                publish_mqtt(radon_st_avg,radon_lt_avg,temperature,humidity,pressure,CO2_lvl,VOC_lvl)
                publish_mqtt(radon_st_avg,radon_lt_avg,temperature,humidity,pressure,CO2_lvl,VOC_lvl)

        except Exception as ex:
            logging.error('Exception while communicating with wave plus: {}'.format(ex))
                        
        finally:
            wp.disconnect()


    # Calculate how long time to wait until next round
    diff = datetime.now() - start
    elapsed_ms = (diff.days * 86400000) + (diff.seconds * 1000) + (diff.microseconds / 1000)
    sleep_s = (wavemon_interval_s)-(elapsed_ms/1000)

    # Never sleep less than 10 seconds between rounds
    if sleep_s < 10:
        sleep_s = 10

    logging.info('Round done, sleeping %fs until next interval.', sleep_s) 
    time.sleep( sleep_s )

