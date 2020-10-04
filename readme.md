# HS110 InfluxDB Exporter
This programm is the successor to my old HS110 exporter, written in bash and only capable of one device.

This exporter is rewritten in python and supports multiple plugs. In addition to that, error-handling is improved
The retrieved data is parsed and exported it to the specified influx database.

This script is based on the tplink-smartplug python code to retrieve power data form the TP-Link HS110 Smart-Plug and store it into an influx-database.
https://github.com/softScheck/tplink-smartplug

## Configuration
The configuration data is stored in the `config.yml` file. This file has to be in the same folder as the `scanner.py` script.

### Syntax:
```
influx:
  user: "<influx username>"
  password: "<influx password>"
  ip: "<influx ipor hostname>"
  port: <influx port> 
  db: "<influx database>"
  measurement: "<influx measurement name>"
plugs:
  - <ip> (Port is always 9999)
  ...
```

### Create cronjobs
If you execute `./scanner.py`, the script will gather the data and insert it into the database.
To automate this, one option is to use cronjobs.

Open your crontab file in an editor:
```
crontab -e
```

Insert the following lines at the bottom:
```
* * * * * /opt/hs110/hs110-influx/scanner.py >/dev/null 2>&1
* * * * * sleep 30; /opt/hs110/hs110-influx/scanner.py >/dev/null 2>&1
```

This will execute the schript every 30 seconds. You can also change the intervall. For more information on how to adjust cronjobs use `man crontab`

# Dependencies
`pip install pyyaml influxdb`
