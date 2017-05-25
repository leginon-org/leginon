#!/bin/sh

/etc/init.d/reduxd start && echo 'reduxd' >> /var/log/startup.log
nohup /usr/bin/mysqld_safe &
echo 'mysqld' >> /var/log/startup.log
rm -fr /tmp/.X* && \
  /usr/sbin/runuser -l appionuser -c 'vncserver -autokill :1 -name vnc -geometry 1440x900' \
  && echo 'vncserver' >> /var/log/startup.log
updatedb && echo 'updatedb' >> /var/log/startup.log
nohup /usr/sbin/apachectl -DFOREGROUND &
echo 'httpd' >> /var/log/startup.log
#sleep 2s && echo 'sleep' >> /var/log/startup.log
if [ ! -d "/emg/data/appion" ]; then
	mysql -u root < /emg/sw/docker.sql && echo 'mysqldump' >> /var/log/startup.log
	mkdir /emg/data/appion
fi

#need a command that does not end to keep container alive
tail -f /home/appionuser/.vnc/*:1.log
for i in {00..99}; do sleep 10; echo $i; done
