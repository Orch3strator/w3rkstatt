#!/usr/bin/env bash
# set -x
# On MAC update bash: https://scriptingosx.com/2019/02/install-bash-5-on-macos/

echo "Updating ctm environment"
echo '{' >ctmenv.deleted.json
if [ "$1" != "" ]; then
        todelete=$1
        echo '{' >ctmenv.current.json
        ctm env show >>ctmenv.current.json
        sed -i -e 2,3d ctmenv.current.json
        [ -e ctmenv.current.json-e ] && rm ctmenv.current.json-e

        # Check if there is a ctm envirnoment at all
        num=$(cat ctmenv.current.json | wc -l)
        if [ $num -eq 1 ]; then
                echo "Currently no ctm environment configured"
                echo "    \"counter\": 0," >>ctmenv.deleted.json
                echo "    \"status\":\"no environment defined\"," >>ctmenv.deleted.json
                echo "    \"pattern\":\"$1\"," >>ctmenv.deleted.json
                echo "    \"exit\": 1" >>ctmenv.deleted.json
                echo '}' >>ctmenv.deleted.json
                echo '}' >>ctmenv.current.json
                exit 1
        fi

        # Check if there is a ctm environment matching the search pattern
        mapfile -t arr < <(jq -r 'keys[]' ctmenv.current.json)
        if [ ${#arr[@]} -eq 0 ]; then
                echo "No ctm environment matching the pattern found"
                echo " - Search pattern: $1"
                echo "    \"counter\": 0," >>ctmenv.deleted.json
                echo "    \"status\":\"no matching pattern\"," >>ctmenv.deleted.json
                echo "    \"exit\": 2" >>ctmenv.deleted.json
                echo '}' >>ctmenv.deleted.json
                exit 2
        else
                counter=0
                printf "    \"environments\":[" >>ctmenv.deleted.json
                # Delete ctm environment matching the pattern
                for item in $(printf "%s\n" ${arr[@]} | grep $todelete); do
                        counter=$((counter + 1))
                        echo "Found ctm environment matching the pattern"
                        echo " - Deleting ctm environment $item"
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
                echo "    \"pattern\":\"$1\"," >>ctmenv.deleted.json
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
        echo "    \"counter\": 0," >>ctmenv.deleted.json
        echo "    \"status\":\"no parameter provided\"," >>ctmenv.deleted.json
        echo "    \"pattern\":\"\"," >>ctmenv.deleted.json
        echo "    \"exit\": 3" >>ctmenv.deleted.json
        echo '}' >>ctmenv.deleted.json
        exit 3
fi
exit 0
