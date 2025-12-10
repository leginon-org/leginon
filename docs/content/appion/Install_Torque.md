#### Install TORQUE (OpenPBS) Server on Goby Head Node

    yum install pdsh-mod-torque torque-server pdsh-mod-torque torque-libs -y 
    /etc/init.d/pbs_server start
    /etc/init.d/pbs_sched start


The last command was giving:

    pbs_sched: LOG_ERROR::Cannot assign requested address (99) in main, bind


After Googling for answer found this http://www.supercluster.org/pipermail/torqueusers/2009-May/009101.html and changed /etc/sysconfig/network to:

    NETWORKING=yes
    NETWORKING_IPV6=no
    HOSTNAME=goby.amigroup.scripps.edu
    GATEWAY=137.131.204.1


Then restarted pbs_server and pbs_sched. Encounter another problem:

    [root@goby ~]# pbsnodes
    munge: Error: Unable to access "/var/run/munge/munge.socket.2": No such file or directory
    pbsnodes: Invalid credential


Run the following commands to fix this:

    create-munge-key
    chkconfig munge on
    /etc/init.d/munge start


* Copy [nodes](https://emg.nysbc.org/redmine/attachments/2496/nodes) to goby:/var/lib/torque/server_priv and restart /etc/init.d/pbs_server.

    [root@goby ~]# cd ~
    [root@goby ~]# cat > safadmin
    #!/bin/sh

    for node in `cat  /var/lib/torque/server_priv/nodes |awk {'print $1'}`
    do
      echo "Executing on $node"
      ssh -oStrictHostKeyChecking=no  $node $@
    done
    [root@goby ~]# chmod +x safadmin 
    [root@goby ~]# ./safadmin ls


This adds RSA key for nodes to the list of known hosts.
