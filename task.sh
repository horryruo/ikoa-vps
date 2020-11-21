#!/bin/bash

ID=$1
test "$2" = "mgs" && TYPE="cid" || TYPE=$2
TaskId=$3
RCLONE_DESTINATION=$4
LOG_PATH=$5
USE_DRIVE=$6
MONTHLY_ONLY_BOOL=$7
DOWN_TIME=$8
ACCOUNTS=$9
TAG=${10}
IFS="," read -r -a idList <<< "$ID"
idListLen=${#idList[@]}
if [[ $USE_DRIVE == "od" ]]; then
    RcloneConf="rclone_3.conf"
elif [[ $USE_DRIVE == "gd" ]]; then
    if [[ $ACCOUNTS == "personal" ]]; then
        RcloneConf="rclone_4.conf"
    elif [[ $ACCOUNTS == "sa" ]]; then
        RcloneConf="rclone_1.conf"
    else
        echo "配置文件accounts出错"
        exit 1
    fi
else
    echo "配置文件usedrive出错"
    exit 1
fi
DownloadCount=0
cd ./fanza || exit
ikoastart=$(./iKOA -E cid:118abp12345)
if [[ $ikoastart =~ "这程序的实例已在运行" ]]; then
    echo "另一个iKOA已在运行,请手动终止程序后再启动"
    exit 1
    #while [[ $(lsof -a iKOA|awk '{if(NR==2)print $2}') ]];do
        #echo "关闭已存在的进程： $(lsof -a iKOA|awk '{if(NR==2)print $2}')"
        #kill -9 $(lsof -a iKOA|awk '{if(NR==2)print $2}')
    #done
fi
codeQuota=$(echo $ikoastart | grep -oP '(?<=剩余\s)[0-9]+(?=\s次)')

if [[ $codeQuota -gt 0 ]]; then
    echo "序列码额度剩余 ${codeQuota} 次"
else

    echo "序列码额度为0，不能下载!"
    exit 1

fi

updateWaitTime() {
    if [[ $codeQuota -ge 1 && $codeQuota -lt 10 ]]; then
        waitTime=3600
    elif [[ $codeQuota -ge 10 && $codeQuota -lt 45 ]]; then
        waitTime=1800
    elif [[ $codeQuota -ge 45 && $codeQuota -lt 90 ]]; then
        waitTime=300
    elif [[ $codeQuota -ge 90 && $codeQuota -lt 10000 ]]; then
        waitTime=0
    elif [[ $codeQuota -ge 10000 ]]; then
        waitTime=600
    else
        echo "序列码额度为0，不能下载!"
        exit 1
    fi
}

sleepHandler() {
    local elapsedTime
    local lastTime
    updateWaitTime
    test -e TIME_VAR.txt && read -r lastTime < TIME_VAR.txt || lastTime=0
    nowTime=$(date +%s)
    elapsedTime=$(( nowTime - lastTime ))
    if [[ $lastTime -eq 0 ]]; then
        elapsedTime=0
    fi
    if [[ $elapsedTime -le $waitTime && $elapsedTime -ne 0 ]]; then
        local sleepTime=$((waitTime - elapsedTime))
        while [[ $sleepTime -ge 0 ]]; do
            printf '请求过快，需要等待 %02dh:%02dm:%02ds\n' $((sleepTime/3600)) $((sleepTime%3600/60)) $((sleepTime%60))
            sleepTime=$((sleepTime - 1))
            sleep 1
        done
    fi
}

if [[ $TaskId -eq 0 ]]; then
    NAME="$(date +"%Y-%m-%dT%H:%M:%SZ")-download_info.csv"
    echo "id,name,taskid,status,size,bitrate,multipart,tag,monthly" >> "$NAME"
    echo "$NAME" > FILENAME_VAR.txt
    mkdir -p backup 
fi
test -e FILENAME_VAR.txt && read -r fileName < FILENAME_VAR.txt || exit 1
test -n "$TAG" && dirArgs="downloads/${TAG}" || dirArgs="downloads"

for i in "${!idList[@]}"; do
    FLAG=0
    sleep 2
    query=$(curl -sL --retry 5 "https://v2.mahuateng.cf/isMonthly/${idList[i]}")
    isMonthly=$(echo "$query" | grep -oP '(?<=\"monthly\":)(true|false)(?=\,)' || echo "queryfailed")
    echo "Current id:${idList[i]} taskid:${TaskId} Current task progress:$((i + 1))/${idListLen} tag:${TAG:-None} Monthly:${isMonthly}"
    sleep 1
    if [[ $isMonthly == "true" ]]; then
        sleepHandler
        startTime=$(date +%s)
        ikoaOutput=$(./iKOA -E -d "$dirArgs" "$TYPE":"${idList[i]}" | tail -n 6)
    elif [[ $isMonthly == "false" ]]; then
        if [[ $MONTHLY_ONLY_BOOL == "true" ]]; then
            echo "id:${idList[i]} taskid:${TaskId} status:pass tag:${TAG:-None} Monthly:${isMonthly}"
            echo "${idList[i]},,${TaskId},pass,,,,${TAG},${isMonthly}" >> "$fileName"
            continue
        else
            sleepHandler
            startTime=$(date +%s)
            ikoaOutput=$(./iKOA -E -d "$dirArgs" "$TYPE":"${idList[i]}" | tail -n 6)
            FLAG=1         
        fi
    else
        echo "id:${idList[i]} taskid:${TaskId} status:pass tag:${TAG:-None} Monthly:${isMonthly}"
        echo "${idList[i]},,${TaskId},pass,,,,${TAG},${isMonthly}" >> "$fileName"
        continue
    fi
      
    if [[ $ikoaOutput =~ "已下载" ]]; then
        DownloadCount=$((DownloadCount + 1))
        bitrate=$(echo "$ikoaOutput" | grep -oE '[0-9]+kbps')
        multipart=$(echo "$ikoaOutput" | grep -oP '(?<=部分=\[)[0-9]+(,[0-9]+)*(?=\])' | awk 'BEGIN {FS=","} {print $NF}')
        if [[ $FLAG -eq 1 ]]; then
            if [[ $multipart -eq 0 || $MERGE_BOOL == "true" ]]; then
                codeQuota=$((codeQuota - 1))
            else
                codeQuota=$((codeQuota - multipart))
            fi
        fi
        filePath=$(find "$dirArgs" -mindepth 1 -maxdepth 1 -type d -printf '%T@ %p\n' | sort -k1 -r -n | head -1 | cut -d ' ' -f2)
        name=$(basename "$filePath")
        fileSize=$(du -m "$filePath" | cut -f1)
        echo "${idList[i]},${name},${TaskId},succeed,${fileSize}M,${bitrate},${multipart},${TAG},${isMonthly}" >> "$fileName"
        echo "id:${idList[i]} name:${name} taskid:${TaskId} status:succeed size:${fileSize}M bitrate:${bitrate} multipart:${multipart} tag:${TAG:-None} Monthly:${isMonthly}"         
    elif [[ $ikoaOutput =~ "序列码额度为0" ]]; then
        echo "序列码额度为0，不能下载!"
        break
    elif [[ $ikoaOutput =~ "查询无结果" ]]; then
        echo "${idList[i]},,${TaskId},notfound,,,,${TAG},${isMonthly}" >> "$fileName"
        echo "id:${idList[i]} taskid:${TaskId} status:notfound tag:${TAG:-None} Monthly:${isMonthly}"
    else
        test $FLAG -eq 1 && codeQuota=$((codeQuota - 1))
        echo "${idList[i]},,${TaskId},failed,,,,${TAG},${isMonthly}" >> "$fileName"
        echo "id:${idList[i]} taskid:${TaskId} status:failed tag:${TAG:-None} Monthly:${isMonthly}"
    fi
    if [[ ($ikoaOutput =~ "已下载" && ($((DownloadCount % DOWN_TIME)) -eq 0 || $codeQuota -lt 45)) || ${i} -eq ${idListLen} ]]; then
        sleep 2
        while true
        do
            rclone --config="$RcloneConf" move downloads "DRIVE:$RCLONE_DESTINATION" --drive-stop-on-upload-limit --drive-chunk-size 64M --exclude-from rclone-exclude-file.txt -v --stats-one-line --stats=1s
            rc=$?
            if [[ $rc -ne 7 ]]; then
                break
            else
                if [[ $RcloneConf == "rclone_1.conf" ]]; then
                    RcloneConf="rclone_2.conf"
                elif [[ $RcloneConf == "rclone_2.conf" ]]; then
                    RcloneConf="rclone_1.conf"
                elif  [[ $RcloneConf == "rclone_3.conf" ]]; then
                    RcloneConf="rclone_3.conf"
                elif  [[ $RcloneConf == "rclone_4.conf" ]]; then
                    RcloneConf="rclone_4.conf"
                else 
                    echo "rclone配置文件出错"
                fi
            fi
            sleep 10
        done
    fi
    if [[ $ikoaOutput =~ "查询无结果" ]]; then
        elapsed=0
    else
        elapsed=${startTime}
    fi  
    echo "$elapsed" > TIME_VAR.txt
done
csvOutput=$(awk 'BEGIN {FS=","; OFS=":"; ORS=" "} NR > 1 { array[$4]++; number=number+1; total=total+$5; } END { printf "ID in all:%d ", number; for (i in array) print i,array[i]; total=total/1024; printf "totalDownload:%.1fG",total }' "$fileName")
#taskStatus=$(ts | awk 'BEGIN {OFS=":"; ORS=" "} NR > 1 { array[$2]++;total+=1; } END { for (i in array) print i,array[i]; print "totalTask:" total }')

if [[ -e $fileName && -d backup ]]; then
    #totalTask=$(($(ts | wc -l) - 1))
    mv "$fileName" backup
    #if [[ $((TaskId + 1)) -eq $totalTask ]]; then
    echo "All tasks finished ===>>> ${csvOutput} 序列码额度剩余 ${codeQuota} 次"
    echo "Summary ===>>> ${csvOutput} 序列码额度剩余 ${codeQuota} 次 " >>  "./backup/${fileName}"      
    #else
    echo "Until Now ===>>> ${csvOutput} 序列码额度剩余 ${codeQuota} 次"
        
    #echo "taskStatus ===>>> ${taskStatus}"
    #echo "Until Now ===>>> ${csvOutput} 序列码额度剩余 ${codeQuota} 次 ${taskStatus}" >>  "./backup/${fileName}"
    #fi
    rclone --config="$RcloneConf" copy "backup/${fileName}" "DRIVE:$LOG_PATH"                     
fi
