#!/usr/bin/env bash
storage=$(grep 'STORAGE' config.py | cut -d'=' -f2 | tr -d \')
dir=$(grep 'UPLOAD_DIR' config.py | cut -d'=' -f2 | tr -d \')
if [ ${storage} == 'LOCAL' ] && [ ! -d ${dir} ]; then
    mkdir ${dir}
    echo ${dir} created!
fi
