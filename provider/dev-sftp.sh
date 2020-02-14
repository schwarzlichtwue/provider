#!/bin/bash
# Development script that listens on new tweets and syncs to github.
# Basically a script that performs everything the provider was written for.
./script.py -e ../.env -d ../db/db.sqlite3 -a 127.0.0.1 -c \
~/.ssh/config -r /upload/ -u 12 --jekyll-source ../../schwarzlicht/ \
--jekyll-target ../../schwarzlicht-master
