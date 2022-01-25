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
from datetime import datetime

import sys
import time
import struct
import logging
import os

SENSOR_IDX_DATETIME      = 0
SENSOR_IDX_HUMIDITY      = 1
SENSOR_IDX_TEMPERATURE   = 2
SENSOR_IDX_RADON_ST_AVG  = 3
SENSOR_IDX_RADON_LT_AVG  = 4

def parseSerialNumber(ManuDataHexStr):
    if (ManuDataHexStr == None):
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

class Wave():

    UUID_DATETIME     = UUID(0x2A08)
    UUID_HUMIDITY     = UUID(0x2A6F)
    UUID_TEMPERATURE  = UUID(0x2A6E)
    UUID_RADON_ST_AVG = UUID("b42e01aa-ade7-11e4-89d3-123b93f75cba")
    UUID_RADON_LT_AVG = UUID("b42e0a4c-ade7-11e4-89d3-123b93f75cba")

    def __init__(self, SerialNumber):
        self.SN            = SerialNumber
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
                if (SN == int(self.SN)):
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
