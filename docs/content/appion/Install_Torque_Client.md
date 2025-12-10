#### Install Install TORQUE (OpenPBS) Client on Goby Work Nodes

    [root@goby ~]# pdsh -w node[01-16]
    pdsh> yum install -y torque-client torque-mom
    pdsh> sed -i 's/localhost/goby/g' /var/lib/torque/server_name
    pdsh> chkconfig pbs_mom on
    pdsh> service pbs_mom start
    [root@goby queues]# qmgr
    Qmgr: create queue batch
    Qmgr: set queue batch queue_type = Execution
    Qmgr: set queue batch enabled = True
    Qmgr: set queue batch started = True
