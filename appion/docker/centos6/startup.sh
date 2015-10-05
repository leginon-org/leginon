#!/bin/sh

vncserver -autokill :1 -name vnc -geometry 1200x800 &
/usr/sbin/httpd &
/etc/init.d/mysqld start &
sleep 3
mysql -u root < /emg/sw/myami-3.1/docker.sql
tail -f .vnc/*:1.log
