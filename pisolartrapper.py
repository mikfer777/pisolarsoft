#! /home/pi/pisolar-env/bin/python
import RPi.GPIO as GPIO
import time
import array
import os
import signal
import subprocess

import threading
import socket

from solarconfig import *
from mcp3008 import *
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

from pyzabbix import ZabbixMetric, ZabbixSender, ZabbixResponse




STATUSNOBAT = 0
STATUSDNGBAT = 0
STATUSLOWBAT = 0
STATUSGOODBAT = 0
ret = 0

### Main part

if DEBUGMSG == 1:
    print("Batteries high voltage:       " + str(VHIGHBAT))
    print("Batteries low voltage:        " + str(VLOWBAT))
    print("Batteries dangerous voltage:  " + str(VDNGBAT))
    print("ADC high voltage value:       " + str(ADCHIGH))
    print("ADC low voltage value:        " + str(ADCLOW))
    print("ADC dangerous voltage value:  " + str(ADCDNG))


# Called on process interruption. Set all pins to "Input" default mode.
def endProcess(signalnum=None, handler=None):
    GPIO.cleanup()
    exit(0)


# Get current pid
pid = os.getpid()

# Save current pid for later use
try:
    fhandle = open('/home/pi/pisolar.pid', 'w')
except IOError:
    print("Unable to write /home/pi/pisolar.pid")
    exit(1)
fhandle.write(str(pid))
fhandle.close()

# Prepare handlers for process exit
signal.signal(signal.SIGTERM, endProcess)
signal.signal(signal.SIGINT, endProcess)

# Use Raspberry Pi board pin numbers
GPIO.setmode(GPIO.BOARD)

# simple parse for arguments
zserver = sys.argv[1]
if zserver.lower().startswith("http"):
    print("Do not prefix the zabbix server name with 'http' or 'https', just specify the hostname or IP")
    sys.exit(1)
hostId = sys.argv[2]
key = "adc"
port = 10051
while True:
    # Read ADC measure on channel ADCCHANNEL
    ret = readadc(ADCCHANNEL, SPICLK, SPIMOSI, SPIMISO, SPICS)
    ret2 = readadc(1, SPICLK, SPIMOSI, SPIMISO, SPICS)
    if DEBUGMSG == 1:
        print("ADC value channel0: " + str(ret) + " (" + str((3.3 / 1024.0) * ret) + " V)" + " (" + str(6.18 * (3.3 / 1024.0) * ret) + " V)")
        print("ADC value channel1: " + str(ret2))

    if ret < ADCUNP:
        # No battery plugged : we switch all LED off, and run NOBAT_SCRIPT_PATH
        if STATUSNOBAT == 0:
            STATUSNOBAT = 1
            STATUSDNGBAT = 0
            STATUSLOWBAT = 0
            STATUSGOODBAT = 0


    elif ret < ADCDNG:
        # Dangerous battery voltage : we switch OK LED off, KO LED on,
        #   and run DNGBAT_SCRIPT_PATH
        if STATUSDNGBAT == 0:
            STATUSNOBAT = 0
            STATUSDNGBAT = 1
            STATUSLOWBAT = 0
            STATUSGOODBAT = 0
            # try:
            #     p = subprocess.Popen(DNGBAT_SCRIPT_PATH, stdout=subprocess.PIPE)
            # except OSError as detail:
            #     print("Could not execute " + DNGBAT_SCRIPT_PATH[0] + " ", detail)

    elif ret < ADCLOW:
        # Test if we were previously in dangerous status and are actually
        #   encountering a voltage bounce situation after kill switch
        #   activation.
        if STATUSDNGBAT == 1 and ret > ADCDNGBOUNCE:
            # Low battery voltage : we switch OK LED off, KO LED on,
            #   and run KOBAT_SCRIPT_PATH
            if STATUSLOWBAT == 0:
                STATUSNOBAT = 0
                STATUSDNGBAT = 0
                STATUSLOWBAT = 1
                STATUSGOODBAT = 0
                # try:
                #     p = subprocess.Popen(KOBAT_SCRIPT_PATH, stdout=subprocess.PIPE)
                # except OSError as detail:
                #     print("Could not execute " + KOBAT_SCRIPT_PATH[0] + " ", detail)

    else:
        # Normal battery voltage : we switch OK LED on, KO LED off,
        #   and OKBAT_SCRIPT_PATH
        if STATUSGOODBAT == 0:
            STATUSNOBAT = 0
            STATUSDNGBAT = 0
            STATUSLOWBAT = 0
            STATUSGOODBAT = 1
            # try:
            #     p = subprocess.Popen(OKBAT_SCRIPT_PATH, stdout=subprocess.PIPE)
            # except OSError as detail:
            #     print("Could not execute " + OKBAT_SCRIPT_PATH[0] + " ", detail)

    # Send metrics to zabbix trapper
    packet = [
        ZabbixMetric(hostId, key, ret)
        # multiple metrics can be sent in same call for effeciency
        # ,ZabbixMetric(hostId, 'anotherkey', 'anothervalue')
    ]

    ZabbixResponse = ZabbixSender(zserver, port, use_config=None).send(packet)
    print(ZabbixResponse)
    # Pause before starting loop once again
    time.sleep(REFRESH_RATE / 1000)
