#!/bin/bash
ALERTS_FILE="/home/truewatch/.w3rkstatt/logs/alerts.log"
sudo sh -c "echo '$*' >> '${ALERTS_FILE}'"
sudo su - ctmem -c "/usr/bin/python3 /opt/ctm/ctm_alerts.py $*"
