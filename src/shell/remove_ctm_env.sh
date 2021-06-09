#!/usr/bin/env bash
# set -x
################################################################################
# License                                                                         #
################################################################################
function license() {
        # On MAC update bash: https://scriptingosx.com/2019/02/install-bash-5-on-macos/
        printf '%s\n' ""
        printf '%s\n' " GPL-3.0-only or GPL-3.0-or-later"
        printf '%s\n' " Copyright (c) 2021 BMC Software, Inc."
        printf '%s\n' " Author: Volker Scheithauer"
        printf '%s\n' " E-Mail: orchestrator@bmc.com"
        printf '%s\n' " Contributor: Daniel Companeetz"
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

function ctm() {
        printf '%s\n' ""
        printf '%s\n' "  @@@@@@@   @@@@@@   @@@  @@@  @@@@@@@  @@@@@@@    @@@@@@   @@@                  @@@@@@@@@@   "
        printf '%s\n' " @@@@@@@@  @@@@@@@@  @@@@ @@@  @@@@@@@  @@@@@@@@  @@@@@@@@  @@@                  @@@@@@@@@@@  "
        printf '%s\n' " !@@       @@!  @@@  @@!@!@@@    @@!    @@!  @@@  @@!  @@@  @@!                  @@! @@! @@!  "
        printf '%s\n' " !@!       !@!  @!@  !@!!@!@!    !@!    !@!  @!@  !@!  @!@  !@!                  !@! !@! !@!  "
        printf '%s\n' " !@!       @!@  !@!  @!@ !!@!    @!!    @!@!!@!   @!@  !@!  @!!       @!@!@!@!@  @!! !!@ @!@  "
        printf '%s\n' " !!!       !@!  !!!  !@!  !!!    !!!    !!@!@!    !@!  !!!  !!!       !!!@!@!!!  !@!   ! !@!  "
        printf '%s\n' " :!!       !!:  !!!  !!:  !!!    !!:    !!: :!!   !!:  !!!  !!:                  !!:     !!:  "
        printf '%s\n' " :!:       :!:  !:!  :!:  !:!    :!:    :!:  !:!  :!:  !:!   :!:                 :!:     :!:  "
        printf '%s\n' "  ::: :::  ::::: ::   ::   ::     ::    ::   :::  ::::: ::   :: ::::             :::     ::   "
        printf '%s\n' "  :: :: :   : :  :   ::    :      :      :   : :   : :  :   : :: : :              :      :    "
}

version="20.21.07.00"

################################################################################
# Help                                                                         #
################################################################################
function help() {
        # Display Help
        printf '%s\n' ""
        printf '%s\n' "Remove environment definitions from ctm aaapi."
        printf '%s\n' ""
        printf '%s\n' "Syntax: remove_ctm_env.sh [-p|h|v]"
        printf '%s\n' "options:"
        printf '%s\n' "h     Print this Help."
        printf '%s\n' "p     control-m aapi environment name search pattern."
        printf '%s\n' "v     script version."
        exit 0
}

function updateCtm() {
        printf '%s\n' " Updating ctm environment"
        echo '{' >ctmenv.deleted.json
        if [ "$pattern" != "" ]; then
                todelete=$pattern
                echo '{' >ctmenv.current.json
                ctm env show >>ctmenv.current.json
                sed -i -e 2,3d ctmenv.current.json
                [ -e ctmenv.current.json-e ] && rm ctmenv.current.json-e

                # Check if there is a ctm envirnoment at all
                num=$(cat ctmenv.current.json | wc -l)
                if [ $num -eq 1 ]; then
                        printf '%s\n' " Currently no ctm environment configured"
                        echo "    \"counter\": 0," >>ctmenv.deleted.json
                        echo "    \"status\":\"no environment defined\"," >>ctmenv.deleted.json
                        echo "    \"pattern\":\"$pattern\"," >>ctmenv.deleted.json
                        echo "    \"exit\": 1" >>ctmenv.deleted.json
                        echo '}' >>ctmenv.deleted.json
                        echo '}' >>ctmenv.current.json
                        return 1
                fi

                # Check if there is a ctm environment matching the search pattern
                mapfile -t arr < <(jq -r 'keys[]' ctmenv.current.json)
                if [ ${#arr[@]} -eq 0 ]; then
                        printf '%s\n' " No ctm environment matching the pattern found"
                        printf '%s\n' "  - Search pattern: $pattern"
                        echo "    \"counter\": 0," >>ctmenv.deleted.json
                        echo "    \"status\":\"no matching pattern\"," >>ctmenv.deleted.json
                        echo "    \"exit\": 2" >>ctmenv.deleted.json
                        echo '}' >>ctmenv.deleted.json
                        return 2
                else
                        counter=0
                        printf "    \"environments\":[" >>ctmenv.deleted.json
                        # Delete ctm environment matching the pattern
                        for item in $(printf "%s\n" ${arr[@]} | grep $todelete); do
                                counter=$((counter + 1))
                                echo " Found ctm environment matching the pattern"
                                echo "  - Deleting ctm environment $item"
                                printf "\"$item\"," >>ctmenv.deleted.json
                                status=$(ctm env delete $item)
                        done
                        printf "\"\"]" >>ctmenv.deleted.json
                        echo "," >>ctmenv.deleted.json
                        echo "    \"counter\":\"$counter\"," >>ctmenv.deleted.json
                        if [ $counter -eq 0 ]; then
                                echo "    \"status\":\"nothing to do\"," >>ctmenv.deleted.json
                        else
                                echo "    \"status\":\"deleted environments\"," >>ctmenv.deleted.json
                        fi
                        echo "    \"pattern\":\"$pattern\"," >>ctmenv.deleted.json
                        echo "    \"exit\": 0" >>ctmenv.deleted.json
                        echo '}' >>ctmenv.deleted.json
                fi

                # update json files
                mv ctmenv.current.json ctmenv.old.json
                echo '{' >ctmenv.final.json
                ctm env show >>ctmenv.final.json
                sed -i -e 2,3d ctmenv.final.json
                [ -e ctmenv.final.json-e ] && rm ctmenv.final.json-e

        else
                # no parameter provided
                printf '%s\n' " No pattern provided"
                echo "    \"counter\": 0," >>ctmenv.deleted.json
                echo "    \"status\":\"no parameter provided\"," >>ctmenv.deleted.json
                echo "    \"pattern\":\"\"," >>ctmenv.deleted.json
                echo "    \"exit\": 3" >>ctmenv.deleted.json
                echo '}' >>ctmenv.deleted.json
                return 3
        fi
        return 0
}

POSITIONAL=()
while [[ $# -gt 0 ]]; do
        key="$1"

        case $key in
        -p | --pattern)
                pattern="$2"
                shift # past argument
                shift # past value
                ctm
                updateCtm $pattern

                ;;
        -h | --help)
                ctm
                help
                ;;
        -v | --version)
                ctm
                echo "Version: ${version}"
                exit
                ;;
        -l | --license)
                ctm
                license
                exit
                ;;
        *)
                ctm
                exit
                ;;

        esac
done
ctm
set -- "${POSITIONAL[@]}" # restore positional parameters
exit 99