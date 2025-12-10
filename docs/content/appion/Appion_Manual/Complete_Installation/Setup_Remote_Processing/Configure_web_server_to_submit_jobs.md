**This file is no longer needed as of Appion version 2.2.** The information that was configured in the cluster.php file is not set in the main config.php file in the PROCESSING_HOST array. [(instructions for editing the config.php file)](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Install_the_Web_Interface/Install_the_Web_Interface_Advanced)

## configuration at web server side

**IMPORTANT**: What we refer here as *your_cluster.php* should not be taken literally. For example, if you access your cluster through the network with a name "bestclusterever", you should name your cluster configuration php file **bestclusterever.php**, not *your_cluster.php*.

1.  Go to your myamiweb/processing directory (on CentOS this may be in /var/www/html)
2.  Copy **default_cluster.php** to *your_cluster.php*
3.  [Edit your_cluster.php](/appion/Appion_Manual/Complete_Installation/Setup_Remote_Processing/ClusterPhpSettings) to correspond to your cluster configuration.
4.  Run the setup wizard found at http://YOUR_SERVER/myamiweb/setup to register the *your_cluster.php* you just created.

_

[Setup Remote Processing ^](/appion/Appion_Manual/Complete_Installation/Setup_Remote_Processing)

_
