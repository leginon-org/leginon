Link to [top 10 cheat sheets](http://www.cyberciti.biz/tips/linux-unix-commands-cheat-sheets.html).

### make a folder writable

     chmod -R g+rw eman_recon14

### change the owner of a folder and its contents

    chown -R <usename> <folder>

### check the status of a job

# ssh to the processing server

#

    qstat -au YOUR_USER_NAME

1.  will list your jobs

### check which nodes are currently being used on processing machine

    qstat -an

### check the status of each node on the cluster

1.  spew a bunch of info about each of the nodes including status:
        pbsnodes
2.  For a graphic version use the command ( remember to use -X with
    ssh to display it back to your computer):
        xpbsmon

### kill a process

1.  Log into the machine it is running on
        ssh fly
2.  Look for processes with your user name
        ps -ef |grep [your_username]
3.  Kill the process using the number in the first column after your username
        kill [process id]
4.  If the process was a copy, remove the destination folder
        rm [destination folder]
5.  list system stats
        top

### submit a job to a job manager

    qsub <jobfilename>

### Kill a job running through the job manager

-   use **qdel** `<job number>

### Start an interactive session on a node

    qsub -I

-   you can type in job file contents line by line and see results.

### Check how much space is available on a data drive

-   cd to the drive (cd /ami/data00) and type:
        df -h .


-   to show disc usage status of all mounted systems:
        df -h

### see how large the files are in a directory

    du

-   Or for a more human readable command:


    du -sch *

### See what groups a user belongs to

    id <username>

-   **note:** the user's umask should be set to 002 in their .cshrc file if they are not using the global one to make sure AMI group members can process their data.

### Find user name from UID

    awk -v val=UID -F ":" '$3==val{print $1}' /etc/passwd

### Find the version of CentOS installed

    # cat /etc/*release*

### Fix a *Stale NFS file handle.* error

Do a lazy unmount followed by mount.

    umount -l <drive>
    mount <drive>

OR

On the file server:

    exportfs -f

### See what modules are available on a cluster

On Garibaldi at least:

1.  display a list of all the installed modules that can be added to your .cshrc file.
        module avai
2.  list all the modules that are currently loaded.
        module list
