### Manual configuration instructions (Advanced User)

**Note:** You may skip this section if you configured your installation with the setup wizard at http://localhost/myamiweb/setup.

Copy config.php.template to config.php and edit the latter by adding these parameters:
"config.php" should be located in /var/www/html/myamiweb/ on CentOS and /srv/www/htdocs/myamiweb/ on SuSE.

1.  define site base path
    This should be changed if the myamiweb directory is located
    in a sub-directory of the Apache web directory.
    ex. myamiweb is in /var/www/html/applications/myamiweb/ then
    change to define('BASE_PATH',"applications/myamiweb");
     
        define('BASE_PATH',"myamiweb"); 

    
     
2.  myamiweb login system
        // Browse to the administration tools in myamiweb prior to 
        // changing this to true to populate DB tables correctly.
        define('ENABLE_LOGIN', false);  

    
     
3.  Administrator email title and email address
        define('EMAIL_TITLE', 'The name of your institute');
        define('ADMIN_EMAIL', "example@institute.edu");

    
     
4.  SMTP Server setup (not required but recommended):
        define('ENABLE_SMTP', false);
        define('SMTP_HOST', 'mail.institute.edu');  //your smtp host

    
     
    1.  When SMTP server requires authentication
            // --- Check this with your email administrator -- //
            // --- Set it to true if your SMTP server requires authentication -- //
            define('SMTP_AUTH', false);

            // --- If SMTP_AUTH is not required(SMTP_AUTH set to false, -- //
            // --- no need to fill in 'SMTP_USERNAME' & SMTP_PASSWORD -- //
            define('SMTP_USERNAME', "");
            define('SMTP_PASSWORD', "");

        
         
5.  Setup your MySQL database server parameters:
        define('DB_HOST', "");      // DB Host name
        define('DB_USER', "");      // DB User name
        define('DB_PASS', "");      // DB Password
        define('DB_LEGINON', "");   // Leginon database name
        define('DB_PROJECT', "");   // Project database name

    
     
6.  Enable Image Cache
    If you want to use caching function for faster image loading time in image viewer, change 'ENABLE_CACHE' to true.
    You can change the 'CACHE_PATH' to other location, but make sure the apache user has write access to this folder.
        // --- Enable Image Cache --- //
        define('ENABLE_CACHE', true);
        // --- caching location --- //
        // --- please make sure the apache user has write access to this folder --- //
        define('CACHE_PATH', '/srv/www/cache/');
        define('CACHE_SCRIPT', WEB_ROOT.'/makejpg.php');

    
     
7.  Add Redux Image server parameters
        define('SERVER_HOST',"localhost")
        define('SERVER_PORT',"55123");

    
    The server port chosen should match the value found in redux.log when the redux server is started.

### Additional parameters needed for Appion Installations only:


1. Enable the processing plug-in by uncommenting out the following line in the file`myamiweb/config.php`
addplugin("processing");


 
2. IMAGIC and Other features:
// Check if IMAGIC is installed and running, otherwise hide all functions
define('HIDE_IMAGIC', false);

// hide processing tools still under development.
define('HIDE_FEATURE', true);


 
3. Add processing host information
**processing host is the computer with pbs server running (i.e. the head node of a computer cluster if applicable)**
 
**Appion version 2.2 and later:**
The following code should be added and modified for each processing host available.
$PROCESSING_HOSTS[] = array(
'host' => 'LOCAL_CLUSTER_HEADNODE.INSTITUTE.EDU', // for a single computer installation, this can be 'localhost'
'nproc' => 32, // number of processors available on the host, not used
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
'loginmethod' => 'USERPASSWORD', // Appion currently supports 'USERPASSWORD'. 'SHAREKEY' is possible, but not preferable.
'loginusername' => '', // if this is not set, Appion uses the username provided by the user in the Appion Processing GUI
'passphrase' => '', // if this is not set, Appion uses the password provided by the user in the Appion Processing GUI
'publickey' => 'rsa.pub', // set this if using 'SHAREDKEY' (not supported
'privatekey' => 'rsa' // set this if using 'SHAREDKEY'
);


 
**Appion version 2.1 and prior:**
// ---- Please enter your processing host information associate with --- //
// ---- Maximum number of the processing nodes --- //
// ---- $PROCESSING_HOSTS[] = array('host' => 'host1.school.edu', 'nproc' => 4); --- //
// ---- $PROCESSING_HOSTS[] = array('host' => 'host2.school.edu', 'nproc' => 8); --- //

// $PROCESSING_HOSTS[] = array('host' => '', 'nproc' => );


 
4. Microscope spherical aberration constant
 
Not needed for Appion version 2.2 and later. Version 2.1 and earlier only:
$DEFAULTCS = "2.0";


 
5. Redux server information
 
This is a very new feature, post Appion 2.2, so you only need this if you are running the trunk or 2.2-redux.
The Redux server replaces the old mrc_php module and will be released in Appion version 3.0.
[Information on redux parameters to add to the config.php](/appion/leginonUsing_Redux_to_serve_images_on_myamiweb)


We will not include the cluster registration now. It is covered in the last part of this document.

[Go back to Install the Web Interface](/appion/Appion_Manual/Complete_Installation/Web_Server_Installation/Install_the_Web_Interface)
