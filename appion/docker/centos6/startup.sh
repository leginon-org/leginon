#!/bin/sh

/etc/init.d/mysqld start &
vncserver -autokill :1 -name vnc -geometry 1200x800 &
updatedb &
/etc/init.d/httpd start &
/etc/init.d/reduxd start &
sleep 7
#mysql -u root < /emg/sw/docker.sql
#mysql_upgrade
su appionuser
tail -f .vnc/*:1.log
