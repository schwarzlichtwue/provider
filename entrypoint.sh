#!/bin/sh

tor &

content-provider -e /app/.env -d /app/db/db.sqlite3 -u 12 \
		--jekyll-source /source_repo --jekyll-target /target_repo/ \
		-a sftp://www3.systemli.org -f schwarzlicht -r /www/ \
