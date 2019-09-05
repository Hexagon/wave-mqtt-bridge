# MIT License
#
# Copyright (c) 2018 Airthings AS
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
#
# https://airthings.com

# ===============================
# Module import dependencies
# ===============================

from bluepy.btle import UUID, Peripheral, Scanner, DefaultDelegate
import sys
from datetime import datetime
import time
import struct
import json
import paho.mqtt.publish as publish
import logging
import os

# Read environment
mqtt_host = os.getenv('MQTT_HOST')
mqtt_port = os.getenv('MQTT_PORT', 1883)
mqtt_user = os.getenv('MQTT_USER')
mqtt_pass = os.getenv('MQTT_PASS')
mqtt_topic_lt = os.getenv('MQTT_TOPIC_RADON_LT')
mqtt_topic_st = os.getenv('MQTT_TOPIC_RADON_ST')
mqtt_topic_t = os.getenv('MQTT_TOPIC_RADON_TEMPERATURE')
mqtt_topic_h = os.getenv('MQTT_TOPIC_RADON_HUMIDITY')
mqtt_topic_l = os.getenv('MQTT_TOPIC_RADON_LIGHT')
aw_serial = os.getenv('AW_SERIAL')
json_file = os.getenv('JSON_PATH')

wavemon_logfile = os.getenv('WM_LOGFILE')

# Set up logging
if wavemon_logfile != "None":
    logging.basicConfig(level=logging.DEBUG, filename=wavemon_logfile, filemode='w', format='%(name)s - %(asctime)s - %(levelname)s - %(message)s')
else:
    logging.basicConfig(level=logging.DEBUG)

# Log environment
logging.info("Config: MQTT_HOST resolved to %s", mqtt_host)
logging.info("Config: JSON_FILE resolved to %s", wavemon_logfile)
logging.info("Config: WM_LOGFILE resolved to %s", wavemon_logfile)

# Use mqtt ?
def publish_mqtt(w_st,w_lt,w_temp,w_humidity,w_light):
    logging.info("MQTT publishing enabled")

    # Log extended environment for MQTT
    logging.info("Config: MQTT_PORT resolved to %s", mqtt_port)
    logging.info("Config: MQTT_USER resolved to %s", mqtt_user)
    # logging.info("Config: MQTT_PASS resolved to ", mqtt_pass)
    logging.info("Config: MQTT_TOPIC_RADON_LT resolved to %s", mqtt_topic_lt)
    logging.info("Config: MQTT_TOPIC_RADON_ST resolved to %s", mqtt_topic_st)
    logging.info("Config: MQTT_TOPIC_RADON_TEMPERATURE resolved to %s", mqtt_topic_t)
    logging.info("Config: MQTT_TOPIC_RADON_HUMIDITY resolved to %s", mqtt_topic_h)
    logging.info("Config: MQTT_TOPIC_RADON_LIGHT resolved to %s", mqtt_topic_l)
    
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
    try:
        publish.multiple(mqtt_msgs, hostname=mqtt_host, port=mqtt_port, client_id="wavemon", auth=mqtt_auth, tls=None)
    except Exception as ex:
        logging.error('Exception while publishing to MQTT broker: {}'.format(ex))

# Use json-file ?
# if json_path != None:
#     logging.info("JSON-file publishing enabled")



# ===============================
# Script guards for correct usage
# ===============================

if aw_serial == None:
    logging.info("Missing AW_SERIAL");
    sys.exit(1)

if len(aw_serial) < 3:
    logging.info("Missing AW_SERIAL");
    sys.exit(1)

if aw_serial.isdigit() is not True or len(aw_serial) != 10:
    logging.info("AW_SERIAL has invalid format");
    sys.exit(1)

def parseSerialNumber(ManuDataHexStr):
    if (ManuDataHexStr == "None"):
        SN = "Unknown"
    else:
        ManuData = bytearray.fromhex(ManuDataHexStr)

        if (((ManuData[1] << 8) | ManuData[0]) == 0x0334):
            SN  =  ManuData[2]
            SN |= (ManuData[3] << 8)
            SN |= (ManuData[4] << 16)
            SN |= (ManuData[5] << 24)
        else:
            SN = "Unknown"
    return SN

# ===================================
# Sensor index definitions
# ===================================

SENSOR_IDX_DATETIME      = 0
SENSOR_IDX_HUMIDITY      = 1
SENSOR_IDX_TEMPERATURE   = 2
SENSOR_IDX_RADON_ST_AVG  = 3
SENSOR_IDX_RADON_LT_AVG  = 4

# ===============================
# Class WavePlus
# ===============================

class Wave():

    UUID_DATETIME     = UUID(0x2A08)
    UUID_HUMIDITY     = UUID(0x2A6F)
    UUID_TEMPERATURE  = UUID(0x2A6E)
    UUID_RADON_ST_AVG = UUID("b42e01aa-ade7-11e4-89d3-123b93f75cba")
    UUID_RADON_LT_AVG = UUID("b42e0a4c-ade7-11e4-89d3-123b93f75cba")

    def __init__(self, SerialNumber):
        self.periph            = None
        self.datetime_char     = None
        self.humidity_char     = None
        self.temperature_char  = None
        self.radon_st_avg_char = None
        self.radon_lt_avg_char = None

    def connect(self):
        scanner     = Scanner().withDelegate(DefaultDelegate())
        deviceFound = False
        searchCount = 0
        while deviceFound is False and searchCount < 50:
            devices      = scanner.scan(0.1) # 0.1 seconds scan period
            searchCount += 1
            for dev in devices:
                ManuData = dev.getValueText(255)
                SN = parseSerialNumber(ManuData)
                if (SN == int(aw_serial)):
                    MacAddr = dev.addr
                    deviceFound  = True # exits the while loop on next conditional check
                    break # exit for loop

        if (deviceFound is not True):
            print "ERROR: Could not find device."
            print "GUIDE: (1) Please verify the serial number. (2) Ensure that the device is advertising. (3) Retry connection."
            sys.exit(1)
        else:
            self.periph = Peripheral(MacAddr)
            self.datetime_char     = self.periph.getCharacteristics(uuid=self.UUID_DATETIME)[0]
            self.humidity_char     = self.periph.getCharacteristics(uuid=self.UUID_HUMIDITY)[0]
            self.temperature_char  = self.periph.getCharacteristics(uuid=self.UUID_TEMPERATURE)[0]
            self.radon_st_avg_char = self.periph.getCharacteristics(uuid=self.UUID_RADON_ST_AVG)[0]
            self.radon_lt_avg_char = self.periph.getCharacteristics(uuid=self.UUID_RADON_LT_AVG)[0]
            
    def read(self, sensor_idx):
        if (sensor_idx==SENSOR_IDX_DATETIME and self.datetime_char!=None):
                rawdata = self.datetime_char.read()
                rawdata = struct.unpack('HBBBBB', rawdata)
                data    = datetime(rawdata[0], rawdata[1], rawdata[2], rawdata[3], rawdata[4], rawdata[5])
                unit    = " "
        elif (sensor_idx==SENSOR_IDX_HUMIDITY and self.humidity_char!=None):
                rawdata = self.humidity_char.read()
                data    = struct.unpack('H', rawdata)[0] * 1.0/100.0
                unit    = " %rH"
        elif (sensor_idx==SENSOR_IDX_TEMPERATURE and self.temperature_char!=None):
                rawdata = self.temperature_char.read()
                data    = struct.unpack('h', rawdata)[0] * 1.0/100.0
                unit    = " degC"
        elif (sensor_idx==SENSOR_IDX_RADON_ST_AVG and self.radon_st_avg_char!=None):
                rawdata = self.radon_st_avg_char.read()
                data    = struct.unpack('H', rawdata)[0] * 1.0
                unit    = " Bq/m3"
        elif (sensor_idx==SENSOR_IDX_RADON_LT_AVG and self.radon_lt_avg_char!=None):
                rawdata = self.radon_lt_avg_char.read()
                data    = struct.unpack('H', rawdata)[0] * 1.0
                unit    = " Bq/m3"
        else:
            logging.error("ERROR: Unkown sensor ID or device not paired")
            logging.error("GUIDE: (1) method connect() must be called first, (2) Ensure correct sensor_idx input value.")
            sys.exit(1)
        return str(data)
    
    def disconnect(self):
        if self.periph is not None:
            self.periph.disconnect()
            self.periph            = None
            self.datetime_char     = None
            self.humidity_char     = None
            self.temperature_char  = None
            self.radon_st_avg_char = None
            self.radon_lt_avg_char = None

try:

    #---- Connect to device ----#
    wave = Wave(aw_serial)
    wave.connect()

    # read current values
    date_time    = wave.read(SENSOR_IDX_DATETIME)
    humidity     = wave.read(SENSOR_IDX_HUMIDITY)
    temperature  = wave.read(SENSOR_IDX_TEMPERATURE)
    radon_st_avg = wave.read(SENSOR_IDX_RADON_ST_AVG)
    radon_lt_avg = wave.read(SENSOR_IDX_RADON_LT_AVG)

    if mqtt_host != None:
        publish_mqtt(radon_st_avg,radon_lt_avg,temperature,humidity,0)

except Exception as ex:
    logging.error('Exception while communicating with wave: {}'.format(ex))

finally:
    wave.disconnect()

