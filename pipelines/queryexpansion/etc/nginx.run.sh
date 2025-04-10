#!/bin/sh

sleep 1
while [ -e /tmp/nginx.wait ]; do
    echo "nginx is waiting to start...">&2
    sleep 5
done

ln -sf /dev/stdout /var/log/nginx/access.log
ln -sf /dev/stdout /var/log/nginx/error.log
nginx -g 'daemon off; error_log /dev/stdout info;'

sleep 10 #delay so we don't flood in case something goes horribly wrong
