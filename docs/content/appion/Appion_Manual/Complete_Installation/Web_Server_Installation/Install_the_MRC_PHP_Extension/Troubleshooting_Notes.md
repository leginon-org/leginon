**The following is an internal e-mail that describes a case in which we were able to run php-mrc module through text terminal with php command but not being able to see the images it produced through a network mounted drive,**
**The bottom line is that there is a permission issue. The tests were to eliminate the possibility one by one.**

Hi, Amber,

I got it to work.

The webserver user apache has no permission to serve files from
/home/linux_user/

What I did was:
(1) as root

    $ cd /
    $ mkdir data
    $ chmod -R 755 data

This way, if you check with ls -l
you will get

drwxr-xr-x 5 root root 73 Dec 4 11:42 data

(2) change leginon.cfg in the installation

    $ cd /usr/lib/python2.4/site-packages/leginon/config
    $ vi leginon.cfg

[Images]
/data/leginon

This way, when I upload images to a new session, it will create a
directory under /data/leginon that is readable by everyone.

I figured it out by changing the user assigned
in /etc/httpd/conf/httpd.conf to linux_user, then, after restarting
apache, it could read the test images in /linux_user/Desktop/myami/myamiweb/test.

Then I realize that the system we use at linux_box allows read access
to all, and that a file is still not readable by others if its
parent directories are not readable by others.

It is probably something that we need to formulate better with
our system administrator. It is likely that we can do something more
acceptable by other groups. Apache has all kinds of permission
settings I didn't read through.

Anchi
