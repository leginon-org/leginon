#!/bin/sh

wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/112/06jul12a_00015gr_00028sq_00004hl_00002en.mrc'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/113/06jul12a_00015gr_00028sq_00023hl_00002en.mrc'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/114/06jul12a_00015gr_00028sq_00023hl_00004en.mrc'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/115/06jul12a_00022gr_00013sq_00002hl_00004en.mrc'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/116/06jul12a_00022gr_00013sq_00003hl_00005en.mrc'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/109/06jul12a_00022gr_00037sq_00025hl_00004en.mrc'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/110/06jul12a_00022gr_00037sq_00025hl_00005en.mrc'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/111/06jul12a_00035gr_00063sq_00012hl_00004en.mrc'

wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/631/eman-linux-x86_64-cluster-1.9.tar.gz'
#wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/638/spidersmall.18.10.tar.gz'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/4485/spidersmall.13.00.tgz'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/636/Xmipp-2.4-src.tar.gz'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/4484/ctf_140609.tar.gz'
wget -nc -c 'http://emg.nysbc.org/redmine/attachments/download/4483/ctffind-4.0.16-linux64.tar.gz'

docker build -t vosslab/appion .
