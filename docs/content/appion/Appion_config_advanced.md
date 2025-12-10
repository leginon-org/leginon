1.  Enable the processing plug-in by uncommenting out the following line in the file`myamiweb/config.php`
        addplugin("processing");

    
     
2.  IMAGIC and Other features:
        // Check if IMAGIC is installed and running, otherwise hide all functions
        define('HIDE_IMAGIC', false);

        // hide processing tools still under development.
        define('HIDE_FEATURE', true);

    
     
3.  Add processing host information
    **processing host is the computer with pbs server running (i.e. the head node of a computer cluster if applicable)**
     
    **Appion version 2.2 and later:**
    The following code should be added and modified for each processing host available.
        $PROCESSING_HOSTS[] = array(
        'host' => 'LOCAL_CLUSTER_HEADNODE.INSTITUTE.EDU', // for a single computer installation, this can be 'localhost'    
        'nproc' => 32,  // number of processors available on the host, not used
        'nodesdef' => '4', // default number of nodes used by a refinement job
        'nodesmax' => '280', // maximum number of nodes a user may request for a refinement job
        'ppndef' => '32', // default number of processors per node used for a refinement job
        'ppnmax' => '32', // maximum number of processors per node a user may request for a refinement job
        'reconpn' => '16', // recons per node, not used 
        'walltimedef' => '48', // default wall time in hours that a job is allowed to run
        'walltimemax' => '240', // maximum hours in wall time a user may request for a job
        'cputimedef' => '1536', // default cpu time in hours a job is allowed to run (wall time x number of cpu's) 
        'cputimemax' => '10000', // maximum cpu time in hours a user may request for a job
        'memorymax' => '', // the maximum memory a job may use
        'appionbin' => 'bin/', // the path to the myami/appion/bin directory on this host
        'appionlibdir' => 'appion/', // the path to the myami/appion/appionlib directory on this host
        'baseoutdir' => 'appion', // the directory that processing output should be stored in
        'localhelperhost' => '', // a machine that has access to both the web server and the processing host file systems to copy data between the systems
        'dirsep' => '/', // the directory separator used by this host
        'wrapperpath' => '', // advanced option that enables more than one Appion installation on a single machine, contact us for info 
        'loginmethod' => 'USERPASSWORD', // Appion currently supports 'USERPASSWORD'.  'SHAREKEY' is possible, but not preferable. 
        'loginusername' => '', // if this is not set, Appion uses the username provided by the user in the Appion Processing GUI
        'passphrase' => '', // if this is not set, Appion uses the password provided by the user in the Appion Processing GUI
        'publickey' => 'rsa.pub', // set this if using 'SHAREDKEY' (not supported 
        'privatekey' => 'rsa'     // set this if using 'SHAREDKEY'
        );

    
     
    **Appion version 2.1 and prior:**
        // --- Please enter your processing host information associate with -- //
        // --- Maximum number of the processing nodes                                   -- //
        // --- $PROCESSING_HOSTS[] = array('host' => 'host1.school.edu', 'nproc' => 4); -- //
        // --- $PROCESSING_HOSTS[] = array('host' => 'host2.school.edu', 'nproc' => 8); -- //

        // $PROCESSING_HOSTS[] = array('host' => '', 'nproc' => );

    
     
4.  Microscope spherical aberration constant
     
    Not needed for Appion version 2.2 and later. Version 2.1 and earlier only:
        $DEFAULTCS = "2.0";

    
     
5.  Redux server information
     
    This is a very new feature, post Appion 2.2, so you only need this if you are running the trunk or 2.2-redux.
    The Redux server replaces the old mrc_php module and will be released in Appion version 3.0.
    [Information on redux parameters to add to the config.php](/appion/leginonUsing_Redux_to_serve_images_on_myamiweb)
