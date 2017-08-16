#!/bin/sh

curdir=$(pwd)

mkdir TGZ
cd TGZ/
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/631/eman-linux-x86_64-cluster-1.9.tar.gz'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/4485/spidersmall.13.00.tgz'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/4484/ctf_140609.tar.gz'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/8366/ctffind-4.1.5.tgz'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/5600/eman2_centos6_docker.tgz'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/5034/xmipp_centos6_docker.tgz'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/5166/relion-1.4.tgz'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/7489/findem-docker-centos7.tgz'
cd $curdir
tar zxvf TGZ/findem-docker-centos7.tgz

docker build -t myami_procnode - < procnode.Dockerfile