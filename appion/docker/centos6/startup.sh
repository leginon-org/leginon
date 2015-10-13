#!/bin/sh

vncserver -autokill :1 -name vnc -geometry 1200x800 &
updatedb &
/etc/init.d/httpd start &
/etc/init.d/reduxd start &
/etc/init.d/mysqld start &
sleep 3
mysql -u root < /emg/sw/docker.sql
tail -f .vnc/*:1.log
