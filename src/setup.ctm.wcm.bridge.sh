#!/bin/bash
# shellcheck enable=require-variable-braces
# file name: setup.ctm.wcm.bridge.sh
################################################################################
# License                                                                      #
################################################################################
function license() {
    # On MAC update bash: https://scriptingosx.com/2019/02/install-bash-5-on-macos/
    printf '%s\n' ""
    printf '%s\n' " GPL-3.0-only or GPL-3.0-or-later"
    printf '%s\n' " Copyright (c) 2021 BMC Software, Inc."
    printf '%s\n' " Author: Volker Scheithauer"
    printf '%s\n' " E-Mail: orchestrator@bmc.com"
    printf '%s\n' ""
    printf '%s\n' " This program is free software: you can redistribute it and/or modify"
    printf '%s\n' " it under the terms of the GNU General Public License as published by"
    printf '%s\n' " the Free Software Foundation, either version 3 of the License, or"
    printf '%s\n' " (at your option) any later version."
    printf '%s\n' ""
    printf '%s\n' " This program is distributed in the hope that it will be useful,"
    printf '%s\n' " but WITHOUT ANY WARRANTY; without even the implied warranty of"
    printf '%s\n' " MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the"
    printf '%s\n' " GNU General Public License for more details."
    printf '%s\n' ""
    printf '%s\n' " You should have received a copy of the GNU General Public License"
    printf '%s\n' " along with this program.  If not, see <https://www.gnu.org/licenses/>."
}

# Get current script folder
DIR_NAME=$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)
SCRIPT_SETTINGS="${DIR_NAME}/config/setup.settings.ini"

# import bash colors
if [[ -f "${SCRIPT_SETTINGS}" ]]; then
    source <(grep = "${SCRIPT_SETTINGS}")
fi

# Script defaults
retcode=0
SETUP_DIR="${DIR_NAME}"
SUDO_STATE="false"

while getopts d: flag; do
    case "${flag}" in
    d) CTM_BRIDGE_BASE_PATH=${OPTARG} ;;
    esac
done

# hostname is assumed to be a FQDN set during installation, or derived from data.json
# shellcheck disable=SC2006 disable=SC2086# this is intentional
HOST_FQDN=$(cat /etc/hostname)
# shellcheck disable=SC2006 disable=SC2086# this is intentional
HOST_NAME=$(echo ${HOST_FQDN} | awk -F "." '{print $1}')
# shellcheck disable=SC2006 disable=SC2086# this is intentional
HOST_FQDN=$(cat /etc/hostname)
# shellcheck disable=SC2006 disable=SC2086# this is intentional
DOMAIN_NAME=$(echo ${HOST_FQDN} | awk -F "." '{print $2"."$3}')

# shellcheck disable=SC2006 disable=SC2086# this is intentional
HOST_IPV4=$(ip address | grep -v "127.0.0" | grep "inet " | awk '{print $2}' | awk -F "/" '{print $1}')

DATE_TODAY="$(date '+%Y-%m-%d %H:%M:%S')"
LOG_DATE=$(date +%Y%m%d.%H%M%S)
LOG_DIR="${DIR_NAME}"

# shellcheck disable=SC2006 disable=SC2086# this is intentional
LOG_NAME=$(basename $0)
LOG_FILE="${LOG_DIR}/${LOG_NAME}.log"
SCRIPT_NAME="${LOG_NAME}"
SCRIPT_PURPOSE="Setup Control-M WCM Bridge to run as service"

# Show license
license

if [[ "${EUID}" = 0 ]]; then
    # create log dir
    if [ ! -d "${LOG_DIR}" ]; then
        sudo mkdir -p "${LOG_DIR}"
    fi
    sudo sh -c "echo ' -----------------------------------------------' >> '${LOG_FILE}'"
    sudo sh -c "echo ' Start date: ${DATE_TODAY}' >> '${LOG_FILE}'"
    sudo sh -c "echo ' User Name : ${USER}' >> '${LOG_FILE}'"
    sudo sh -c "echo ' Host FDQN : ${HOST_FQDN}' >> '${LOG_FILE}'"
    sudo sh -c "echo ' Host Name : ${HOST_NAME}' >> '${LOG_FILE}'"
    sudo sh -c "echo ' Host IPv4 : ${HOST_IPV4}' >> '${LOG_FILE}'"
    SUDO_STATE="true"
else
    echo " -----------------------------------------------"
    echo -e "${Color_Off} Setup Procedure for            : ${Cyan}${SCRIPT_PURPOSE}${Color_Off}"
    echo -e "${Color_Off} This procedure needs to run as : ${BRed}root${Color_Off}"
    echo -e "${Red} sudo ${Cyan}${SCRIPT_NAME}${Color_Off} -d [CTM WCM Python Script directory]"
    echo " -----------------------------------------------"
    retcode=1
    exit
fi

if [[ -d "${CTM_BRIDGE_BASE_PATH}" ]]; then

    # Start CTM WCM Bridge service
    STATUS_STEP="systemd"
    SYSTEMD_SERVICE_NAME="ctm-wcm"

    CTM_BRIDGE_SYSTEMD_PATH="/lib/systemd/system/${SYSTEMD_SERVICE_NAME}.service"
    CTM_BRIDGE_SCRIPT_FILE_PATH="${CTM_BRIDGE_BASE_PATH}/bridge_ctm.py"

    echo " -----------------------------------------------"
    echo -e "${Color_Off} CTM WCM Bridge Type : ${Cyan}systemd${Color_Off}"
    echo -e "${Color_Off} Service Name        : ${Cyan}${SYSTEMD_SERVICE_NAME}${Color_Off}"
    echo -e "${Color_Off} Systemd Path        : ${Cyan}${CTM_BRIDGE_SYSTEMD_PATH}${Color_Off}"
    echo -e "${Color_Off} Python Script       : ${Cyan}${CTM_BRIDGE_SCRIPT_FILE_PATH}${Color_Off}"

    if [[ ! -f "${CTM_BRIDGE_SYSTEMD_PATH}" ]]; then
        echo "[Unit]" | sudo tee -a ${CTM_BRIDGE_SYSTEMD_PATH}
        echo "Description=Control-M WCM Integration Bridge" | sudo tee -a ${CTM_BRIDGE_SYSTEMD_PATH}
        echo "After=multi-user.target" | sudo tee -a ${CTM_BRIDGE_SYSTEMD_PATH}
        echo "Conflicts=getty@tty1.service" | sudo tee -a ${CTM_BRIDGE_SYSTEMD_PATH}
        echo " " | sudo tee -a ${CTM_BRIDGE_SYSTEMD_PATH}
        echo "[Service]" | sudo tee -a ${CTM_BRIDGE_SYSTEMD_PATH}
        echo "PIDFile='${CTM_BRIDGE_BASE_PATH}/${SYSTEMD_SERVICE_NAME}'.pid" | sudo tee -a ${CTM_BRIDGE_SYSTEMD_PATH}
        echo "User=truewatch" | sudo tee -a ${CTM_BRIDGE_SYSTEMD_PATH}
        echo "Type=simple" | sudo tee -a ${CTM_BRIDGE_SYSTEMD_PATH}
        echo "WorkingDirectory='${CTM_BRIDGE_BASE_PATH}'" | sudo tee -a ${CTM_BRIDGE_SYSTEMD_PATH}
        echo "ExecStart=/usr/bin/python3 '${CTM_BRIDGE_SCRIPT_FILE_PATH}'" | sudo tee -a ${CTM_BRIDGE_SYSTEMD_PATH}
        echo "StandardInput=tty-force" | sudo tee -a ${CTM_BRIDGE_SYSTEMD_PATH}

        echo " " | sudo tee -a ${CTM_BRIDGE_SYSTEMD_PATH}
        echo "[Install]" | sudo tee -a ${CTM_BRIDGE_SYSTEMD_PATH}
        echo " WantedBy=multi-user.target" | sudo tee -a ${CTM_BRIDGE_SYSTEMD_PATH}
    fi

    sudo systemctl daemon-reload
    sudo systemctl enable ${SYSTEMD_SERVICE_NAME}
    sudo systemctl start ${SYSTEMD_SERVICE_NAME}
else
    echo " -----------------------------------------------"
    echo -e "${Color_Off} Setup Procedure for ${Cyan}${SCRIPT_PURPOSE}${Color_Off}"
    echo -e "${Color_Off} This procedure needs to run as ${BRed}root${Color_Off}"
    echo -e "${Cyan} Shell Command : ${BRed}sudo ${Yellow}./${SCRIPT_NAME}${Green} -d [CTM WCM Python Script directory]${Color_Off}"
    echo -e "${Cyan} Example       : ${BRed}sudo ${Yellow}./${SCRIPT_NAME}${Green} -d ${DIR_NAME}${Color_Off}"
    echo " -----------------------------------------------"
fi
