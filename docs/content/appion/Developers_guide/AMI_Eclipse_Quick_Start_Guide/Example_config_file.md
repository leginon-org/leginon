**The example config file below may be out of date.**

    <?php

    /**
    * The Leginon software is Copyright 2010
    * The Scripps Research Institute, La Jolla, CA
    * For terms of the license agreement
    * see http://emg.nysbc.org/software/leginon-license
    *
    */

    /**
    * Please visit http://yourhost/myamiwebfolder/setup
    * for automatically setup this config file for the
    * first time.
    */


    require_once 'inc/config.inc';
    define('WEB_ROOT',dirname(__FILE__));

    // --- define myamiweb tools base --- //
    define('PROJECT_NAME',"myamiweb");
    define('PROJECT_TITLE',"Ambers Trunk Appion and Leginon Tools");

    // --- define site base path -- //
    // --- This should be changed if the myamiweb directory is located -- //
    // --- in a sub-directory of the Apache web directory. -- //
    // --- ex. myamiweb is in /var/www/html/applications/myamiweb/ then -- //
    // --- change "myamiweb to "applications/myamiweb" -- //
    define('BASE_PATH',"~amber/myamiweb");

    define('BASE_URL',"/~amber/myamiweb/");
    define('PROJECT_URL',"/~amber/myamiweb/project/");

    // --- myamiweb login --- //
    // Browse to the administration tools in myamiweb prior to
    // changing this to true to populate DB tables correctly.
    define('ENABLE_LOGIN', true);

    // --- Administrator email title and email address -- //
    define('EMAIL_TITLE',"asdfasf");
    define('ADMIN_EMAIL',"amber@scripps.edu");

    // --- When 'ENABLE_SMTP set to true, email will send out -- //
    // --- via ADMIN_EMIL's SMTP server. --//
    define('ENABLE_SMTP', false);
    define('SMTP_HOST',"");

    // --- Check this with your email administrator -- //
    // --- Set it to true if your SMTP server requires authentication -- //
    define('SMTP_AUTH', false);

    // --- If SMTP_AUTH is not required(SMTP_AUTH set to false, -- //
    // --- no need to fill in 'SMTP_USERNAME' & SMTP_PASSWORD -- //
    define('SMTP_USERNAME',"");
    define('SMTP_PASSWORD',"");

    // --- Set your MySQL database server parameters -- //
    define('DB_HOST',"cronus4.scripps.edu");
    define('DB_USER',ask someone);
    define('DB_PASS',ask someone);
    define('DB_LEGINON',"dbemdata");
    define('DB_PROJECT',"project");

    // --- default URL for project section --- //
    define('VIEWER_URL', BASE_URL."3wviewer.php?expId=");
    define('SUMMARY_URL', BASE_URL."summary.php?expId=");
    define('UPLOAD_URL', BASE_URL."processing/uploadimage.php");

    // --- Set cookie session time -- //
    define('COOKIE_TIME', 0); //0 is never expire.

    // --- defaut user group -- //
    define('GP_USER', 'users');

    // --- XML test dataset -- //
    $XML_DATA = "test/viewerdata.xml";

    // --- Set Default table definition -- //
    define('DEF_PROCESSING_TABLES_FILE', "defaultprocessingtables.xml");
    define('DEF_PROCESSING_PREFIX',"ap");

    // --- Set External SQL server here (use for import/export application) -- //
    // --- You can add as many as you want, just copy and paste the block -- //
    // --- to a new one and update the connection parameters -- //
    // --- $SQL_HOSTS['example_host_name']['db_host'] = 'example_host_name'; -- //
    // --- $SQL_HOSTS['example_host_name']['db_user'] = 'usr_object'; -- //
    // --- $SQL_HOSTS['example_host_name']['db_pass'] = ''; -- //
    // --- $SQL_HOSTS['example_host_name']['db'] = 'legniondb'; -- //

    $SQL_HOSTS[DB_HOST]['db_host'] = DB_HOST;
    $SQL_HOSTS[DB_HOST]['db_user'] = DB_USER;
    $SQL_HOSTS[DB_HOST]['db_pass'] = DB_PASS;
    $SQL_HOSTS[DB_HOST]['db'] = DB_LEGINON;

    // --- path to main --- //
    set_include_path(dirname(__FILE__).PATH_SEPARATOR
    .dirname(__FILE__)."/project".PATH_SEPARATOR
    .dirname(__FILE__)."/lib".PATH_SEPARATOR
    .dirname(__FILE__)."/lib/PEAR");

    // --- add plugins --- //
    // --- uncomment to enable processing web pages -- //
    addplugin("processing");

    define('DEFAULT_APPION_PATH',"/ami/data00/appion/");

    // --- Add as many processing hosts as you like -- //
    // --- Please enter your processing host information associate with -- //
    // --- Maximum number of the processing nodes -- //
    // --- $PROCESSING_HOSTS[] = array('host' => 'host1.school.edu', 'nproc' => 4); -- //
    // --- $PROCESSING_HOSTS[] = array('host' => 'host2.school.edu', 'nproc' => 8); -- //

    $PROCESSING_HOSTS[] = array('host' => 'guppy.scripps.edu',
                                'nproc' => 8,
                                'nodesdef' => '2',
                                'nodesmax' => '8',
                                'ppndef' => '8',
                                'ppnmax' => '8',
                                'reconpn' => '8',
                                'walltimedef' => '2',
                                'walltimemax' => '2',
                                'cputimedef' => '2',
                                'cputimemax' => '2',
                                'memorymax' => '30',
                                'appionbin' => '/opt/myamisnap/bin/appion/',
                                'baseoutdir' => DEFAULT_APPION_PATH,
                                'localhelperhost' => 'guppy.scripps.edu',
                                'dirsep' => '/' );

    $PROCESSING_HOSTS[] = array('host' => 'garibaldi.scripps.edu', 
                                'nproc' => 8,
                                'nodesdef' => '16',
                                'nodesmax' => '280',
                                'ppndef' => '4',
                                'ppnmax' => '8',
                                'reconpn' => '4',
                                'walltimedef' => '240',
                                'walltimemax' => '240',
                                'cputimedef' => '240',
                                'cputimemax' => '240',
                                'memorymax' => '30',
                                'appionbin' => '~bcarr/appionbin/',
                                'baseoutdir' => '', //sends appion procession output to a location under the users home directory on the remote host
                                'localhelperhost' => 'amibox03.scripps.edu',
                                'dirsep' => '/' );


    // --- register your cluster configure file below i.e (default_cluster) --- //
    // --- $CLUSTER_CONFIGS[] = 'cluster1'; -- //
    // --- $CLUSTER_CONFIGS[] = 'cluster2'; -- //

    //$CLUSTER_CONFIGS[] = 'guppy_cluster';
    //$CLUSTER_CONFIGS[] = 'garibaldi';
    //$CLUSTER_CONFIGS[] = 'test1_cluster';
    //$CLUSTER_CONFIGS[] = 'test2_cluster';

    // --- Microscope spherical aberration constant
    // --- Example : 2.0 --- //
    define('DEFAULTCS',"2.0");

    // --- Restrict file server if you want --- //
    // --- Add your allowed processing directory as string in the array
    $DATA_DIRS = array();

    // --- Enable Image Cache --- //
    define('ENABLE_CACHE', false);
    // --- caching location --- //
    // --- please make sure the apache user has write access to this folder --- //
    // --- define('CACHE_PATH', "/srv/www/cache/"); --- //
    define('CACHE_PATH',"");
    define('CACHE_SCRIPT', WEB_ROOT.'/makejpg.php');

    // --- define Flash player base url --- //
    define('FLASHPLAYER_URL', "/flashplayer/");

    // --- define python commands - path --- //

    // to download images as TIFF or JPEG
    // $pythonpath="/your/site-packages";
    // putenv("PYTHONPATH=$pythonpath");

    // To use mrc2any, you need to install the pyami package which is part
    // of myami. See installation documentation for help.
    // --- define('MRC2ANY', "/usr/bin/mrc2any" --- //
    define('MRC2ANY',"/usr/bin/mrc2any");

    // --- Check if IMAGIC is installed and running, otherwise hide all functions --- //
    define('HIDE_IMAGIC', false);

    // --- Check if MATLAB is installed and running, otherwise hide all functions --- //
    define('HIDE_MATLAB', false);

    // --- hide processing tools still under development. --- //
    define('HIDE_FEATURE', false);

    // --- temporary images upload directory --- //
    define('TEMP_IMAGES_DIR',"/tmp");

    // --- use appion warpper --- //
    define('USE_APPION_WRAPPER', true);
    // --- define('APPION_WRAPPER_PATH', ""); --- //
    define('APPION_WRAPPER_PATH',"/opt/myamisnap/bin/appion");


    // --- sample tracking ---//
    define('SAMPLE_TRACK', false);

    // --- exclude projects in statistics. give a string with numbers separated by ',' ---//
    // --- for example, "1,2" ---//
    define('EXCLUDED_PROJECTS',"");


    // --- hide processing tools still under development. --- //
    define('HIDE_TEST_TOOLS', false);

    $TEST_SESSIONS = array(
            'zz07jul25b'
            ,'zz06apr27c'
            ,'zz09feb12b'
            ,'zz09apr14b'
            ,'zz09feb18c'
        );

    ?>
