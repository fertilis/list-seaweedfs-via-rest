#!/bin/bash

dir=$(cd $(dirname $0) && pwd)

while true
do
    python3 $dir/dfs_list.py "${@:1}"
    if [[ $? -eq 0 ]]
    then
        break
    else
        sleep 1
    fi
done
