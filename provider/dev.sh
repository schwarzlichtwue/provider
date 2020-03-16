#!/bin/bash
# Development script that only listens on new tweets but does not sync to
# github
./script.py -e ../.env -d ../db/db.sqlite3 -u 1 --jekyll-source ../../schwarzlicht/ --jekyll-target /tmp/sl
