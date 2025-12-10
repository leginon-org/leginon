In this case, we are setting up a job submission server that will have all of the data directories mounted and external packages installed (EMAN, Xmipp, etc.) on the compute nodes. Most institutions have a job submission server already, but the data is not accessible. Appion is not set up for this scenario except for large reconstruction jobs.

## .appion.cfg config file

The .appion.cfg config file is used to automatically create and submit job files to your job submission server. The sample config file provided in the [Processing Server Installation](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation) instructions was created for the Torque Resource Manager. If a different resource manager is used, the .appion.cfg file will need to be modified appropriately.

## PBS and the Torque Resource Manager

PBS stands for a [Portable Batch System](http://en.wikipedia.org/wiki/Portable_Batch_System). It is a job submission system meaning that users submit many jobs and the server prioritizes and executes each job as resources permit. Below we show how to install the popular open source PBS system called [TORQUE](http://en.wikipedia.org/wiki/TORQUE_Resource_Manager).

A TORQUE cluster consists of one head node and many compute nodes. The head node runs the **pbs_server daemon** and the compute nodes run the **pbs_mom daemon**. Client commands for submitting and managing jobs can be installed on any host (including hosts not running pbs_server or pbs_mom). More documentation about Torque is [available here.](http://docs.adaptivecomputing.com/torque/5-1-0/help.htm#topics/torque/0-intro/introduction.htm)

## Alternate instructions

It may be helpful to review the [head node installation notes](/appion/Install_Torque) and [client installation notes](/appion/Install_Torque_Client) from a recent installation on CentOS 6.

## Head node installation

### Install Torque-server

Torque available with Fedora and CentOS 5.4 (through the EPEL). For YUM based systems type:

    sudo yum -y install torque-server torque-scheduler torque-client

### Initialize Torque-server, because PATH setting you will need to become root

Make sure the directory containing the *pbs_server* executable is in your PATH. For CentOS this is usually /usr/sbin.

    sudo pbs_server -t create

### Activate Torque-server

Enable the torque pbs_mom daemon on reboot:

    sudo /sbin/chkconfig pbs_server on
    sudo /sbin/service pbs_server restart
    sudo /sbin/chkconfig pbs_sched on
    sudo /sbin/service pbs_sched start

### Add nodes to Torque-server nodes file: /var/lib/torque/server_priv/nodes

The format is:

    node-name[:ts] [np=] [properties]

To add the localhost with two processors as a node, you would add:

    localhost np=2

You should add every **compute node** to this file, e.g.,

    node01.INSTITUTE.EDU np=2
    node02.INSTITUTE.EDU np=4
    node03.INSTITUTE.EDU np=2

## Compute node installation

### Install Torque-mom

Torque available in with Fedora and CentOS 5.4 (through the EPEL). For YUM based systems type:

    sudo yum -y install torque-mom torque-client

### Configure node to receive jobs from headnode:

> see http://docs.adaptivecomputing.com/torque/5-1-0/help.htm#topics/torque/1-installConfig/computeNodes.htm for more details

Edit the /var/torque/mom_priv/config (CentOS 5) OR /var/lib/torque/mom_priv/config (CentOS 6) file:

    $pbsserver  headnode.INSTITUTE.EDU   # hostname running pbs_server

For the localhost add:

    $pbsserver  localhost   # hostname running pbs_server

### Activate Torque-mom

Enable the torque pbs_mom daemon on reboot:

    sudo /sbin/chkconfig pbs_mom on
    sudo /sbin/service pbs_mom start

## Munge

http://docs.adaptivecomputing.com/torque/5-1-0/help.htm#topics/torque/1-installConfig/serverConfig.htm#usingMUNGEAuth

Munge is an authentication service that creates and validates user credentials and other features

    sudo create-munge-key
    sudo /sbin/chkconfig munge on
    sudo service munge start
    sudo qmgr -c 'set server authorized_users=user01@host01'
    sudo qmgr -c 'set server authorized_users=user01@host02'
    sudo qmgr -c 'set server authorized_users=user01@*'

_

## Test Torque Setup

On the head node, see if you can run a `qstat`:

    qstat

You can type:

    pbsnodes

to check the state of the compute clusters.

On the head node, create a job and submit it:

    echo "sleep 60" > test.job
    echo "echo hello" >> test.job
    qsub test.job
    qstat

get all settings

    sudo qmgr -c 'list server'

_

[^ Setup Remote Processing](/appion/Appion_Manual/Complete_Installation/Setup_Remote_Processing) | [Install SSH module for PHP >](/appion/Appion_Manual/Complete_Installation/Setup_Remote_Processing/Install_SSH_module_for_PHP)
