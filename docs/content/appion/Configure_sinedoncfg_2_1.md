Sinedon is an object relational mapping library designed to interact with the Leginon and Appion databases.

* An example configuration file is available at:
myami/sinedon/examples/sinedon.cfg

* Configurations for all users should be placed at the following path:
$PYTHONSITEPKG/sinedon/sinedon.cfg
 
Note: You can discover the $PYTHONSITEPKG path by starting python:

    python
    import sys
    sys.path


The first path to site-packages should hold the config file.

* Modify sinedon.cfg to look like the following example. Set the host, [db, user, and passwd to match the databases created during your Database Server setup](/appion/Appion_Manual/Complete_Installation/Processing_Server_Installation/Explanation_of_Sample_Names). Note that the user here is the MySQL user Leginon uses to communicate with the database for all Leginon users. For an Appion or Leginon installation that uses Project database, set the following:

    [global]
    #host: your_database_host
    host: localhost
    user: usr_object
    passwd:

    [projectdata]
    db: projectdb

    [leginondata]
    db: leginondb

**Note:** If you are a developer, and you need to use sinedon.cfg settings that are different from the global settings, you may create your own sinedon.cfg file and place it in your home directory. This version will override the global version located in the site packages directory.
