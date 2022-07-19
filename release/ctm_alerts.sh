#!/bin/bash

ALERTS_FILE_LOG="/home/truewatch/.w3rkstatt/logs/alerts.log"
ALERTS_FILE_PYTHON="/opt/bmcs/w3rkstatt/ctm_alerts.py"
USER_NAME="truewatch"
USER_SHELL="/bin/bash"

sudo -i -u ${USER_NAME} ${USER_SHELL} -c "echo '$*' >> '${ALERTS_FILE_LOG}'"
sudo -i -u ${USER_NAME} ${USER_SHELL} -c "/usr/bin/python3 ${ALERTS_FILE_PYTHON} $*"
