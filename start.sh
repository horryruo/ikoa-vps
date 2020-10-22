#!/bin/bash


SERIAL_CODE=$1
TEAM_DRIVE_ID=$2
SA_JSON_1=$3
SA_JSON_2=$4
MERGE_BOOL=$5
OUTPUT_FILENAME=$6
if [[ -n $SERIAL_CODE && -n $MERGE_BOOL ]]; then
    sed -i "/^serial/c\serial = \'$SERIAL_CODE\'" ./fanza/config.toml
    echo "team_drive = $TEAM_DRIVE_ID" >> ./fanza/rclone_1.conf
    echo "team_drive = $TEAM_DRIVE_ID" >> ./fanza/rclone_2.conf
    echo "$SA_JSON_1" > ./fanza/service_account_1.json
    echo "$SA_JSON_2" > ./fanza/service_account_2.json
    if [[ $MERGE_BOOL == "false" ]]; then
        sed -i -e "/^merge/c\merge = false" -e "/^m3u_merge/c\m3u_merge = false" ./fanza/config.toml
    fi
    if [[ $OUTPUT_FILENAME == "pid" || $OUTPUT_FILENAME == "num" ]]; then
        sed -i "/^filename/c\filename = \'$OUTPUT_FILENAME\'" ./fanza/config.toml
    fi
else
    echo "Warning: Please make sure there exist all of the needed config vars!"
    exit 1
fi






gunicorn --worker-class eventlet -w 1 -c gunicorn.conf.py --bind 0.0.0.0:5000 wsgi --preload