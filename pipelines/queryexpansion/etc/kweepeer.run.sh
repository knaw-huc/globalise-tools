#!/bin/sh
cd /usr/src || exit 1
sudo -u user /usr/bin/kweepeer --bind 0.0.0.0:8080 --config all.config.toml
