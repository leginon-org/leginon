#!/bin/sh

/etc/init.d/reduxd start && echo 'reduxd' >> /var/log/startup.log
/etc/init.d/mysqld start && echo 'mysqld' >> /var/log/startup.log
<<<<<<< HEAD
rm -fr /tmp/.X* && vncserver -autokill :1 -name vnc -geometry 1440x900 && echo 'vncserver' >> 
/var/log/startup.log
=======
rm -fr /tmp/.X* && vncserver -autokill :1 -name vnc -geometry 1200x800 && echo 'vncserver' >> /var/log/startup.log
>>>>>>> origin/trunk
updatedb && echo 'updatedb' >> /var/log/startup.log
/etc/init.d/httpd start && echo 'http' >> /var/log/startup.log
#sleep 2s && echo 'sleep' >> /var/log/startup.log
if [ ! -d "/emg/data/appion" ]; then
	mysql -u root < /emg/sw/docker.sql && echo 'mysqldump' >> /var/log/startup.log
	mkdir /emg/data/appion
fi

#need a command that does not end to keep container alive
tail -f /home/appionuser/.vnc/*:1.log 
