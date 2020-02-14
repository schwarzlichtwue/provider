#!/bin/sh

tor &

content-provider -e /app/.env -d /app/db/db.sqlite3 -u 12 \
		--jekyll-source /source_repo --jekyll-target /target_repo \
		-a www3.systemli.org -c /app/ssh_config -r /www/ \
