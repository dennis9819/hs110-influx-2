#!/usr/bin/env python3
#
# TP-Link Wi-Fi Smart Plug Influx Reader
# For use with TP-Link HS-110
#
# by Dennis Gunia
#
# TpLink Protocol code (reqCmd(), encrypt(), decrpyt()) based on https://github.com/softScheck/tplink-smartplug
# by Lubomir Stroetmann
# Copyright 2016 softScheck GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

# import libs
import yaml
import socket
import sys
import pytz
import json 
from struct import pack
from influxdb import InfluxDBClient
from datetime import datetime

# list of influx data points
points = []

# read config file
with open(r'./config.yml') as file:
    config = yaml.load(file, Loader=yaml.FullLoader)

# connect to influxdb
try:
    client = InfluxDBClient(host=config['influx']['ip'], port=config['influx']['port'], username=config['influx']['user'], password=config['influx']['password'], database=config['influx']['db'])
    client.get_list_database()
except:
    exit("Cannot connect to influxdb")

# Encryption and Decryption of TP-Link Smart Home Protocol
# XOR Autokey Cipher with starting key = 171
# Python 3.x Version
if sys.version_info[0] > 2:
	def encrypt(string):
		key = 171
		result = pack('>I', len(string))
		for i in string:
			a = key ^ ord(i)
			key = a
			result += bytes([a])
		return result

	def decrypt(string):
		key = 171
		result = ""
		for i in string:
			a = key ^ i
			key = i
			result += chr(a)
		return result

# Python 2.x Version
else:
	def encrypt(string):
		key = 171
		result = pack('>I', len(string))
		for i in string:
			a = key ^ ord(i)
			key = a
			result += chr(a)
		return result

	def decrypt(string):
		key = 171
		result = ""
		for i in string:
			a = key ^ ord(i)
			key = ord(i)
			result += chr(a)
		return result

# send command to tplink device
def reqCmd(cmd, ip):
    sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock_tcp.settimeout(20)
    sock_tcp.connect((ip, 9999))
    sock_tcp.settimeout(None)
    sock_tcp.send(encrypt(cmd))
    data = sock_tcp.recv(2048)
    sock_tcp.close()
    return json.loads(decrypt(data[4:]))

# read single plug and add to data array
def readPlug(ip):
    try:
        # create utc timetsamp
        dateTimeObj = datetime.now(tz=pytz.utc).isoformat()

        # retrieve data from plug
        dInfo = reqCmd('{"system":{"get_sysinfo":{}}}', ip)['system']['get_sysinfo']
        dData = reqCmd('{"emeter":{"get_realtime":{}}}', ip)['emeter']['get_realtime']

        # create point and add to points array
        json_body = {
            "measurement": config['influx']['measurement'],
            "tags": {
                "mac": dInfo['mac'],
                "alias": dInfo['alias'],
                "ip": ip
            },
            "time": dateTimeObj,
            "fields": {
                "volts": dData['voltage_mv'],
                "amps": dData['current_ma'],
                "watts": dData['power_mw'],
                "wh": dData['total_wh']
            }
        }
        points.append(json_body)
        print("Read plug " + ip )

    except socket.error:
        print("Could not connect to plug " + ip )

# read all plugs
for deviceIp in config['plugs']:
    readPlug(deviceIp)

# write to influxdb
try:
    client.write_points(points)
except:
    exit("error writing influxdb")
finally:
    print("done!")
