#!/usr/bin/env bash
#
# copyright (c) 2015 luffae@gmail.com
#

wd=$(cd $(dirname $0) && pwd)

cfg=$wd/main.conf

py=/usr/bin/python

if [[ ! -f $cfg ]]; then
  echo "config not found: $cfg"
  exit 1
fi

FLASK_CONFIG=$cfg nohup $py $wd/main.py 2>&1 > $wd/access.log &

