<?php

/**
 * This class allows you to customize your cluster params
 * You can add/modify:
 * 	- job file input
 * 	- form input
 * 	- javqascript check
 *
 * Note: each cluster file must be register in config_processing.php
 * */
require_once "inc/leginon.inc";
require_once "inc/path.inc";

class Cluster {

    private $hostname;   //hostname of the cluster or its IP address
    private $nodesDef;
    private $nodesMax;
    private $ppnDef;
    private $ppnMax;
    private $reconPerNodeDef; // default reconstructions per node
    private $wallTimeDef;
    private $wallTimeMax;
    private $cpuTimeDef;
    private $cpuTimeMax;
    private $memoryMax;
    private $appionBin; // location of appion scripts on cluster, must end in slash, e.g., /usr/local/appion/bin/
    private $appionLibDir; // location of appionlib directory on cluster, must end in slash, e.g., /usr/local/appion/appionlib/
    private $dirSeparator; // eg. "/"
    private $remoteOutputPath;
    private $baseoutdir;
    private $localHelperHost; // local host used by remote host to rsync results
    private $loginMethod;     //Method used to login to cluster curently only USERPASSWORD or SHAREDKEY
    private $loginUserName;   //Username for shared logins
    private $publicKey;    //Location of publickey file(s)
    private $privateKey;   //Location of private key file(s)
    private $passPhrase;   //passPhrase if it is to be stored in cluster config
    private $gpus;     // a dictionary array of the gpu names and device numbers available on this host
    private $queues;  // an array of queues that jobs may be submitted to. This may be empty.	

    function __construct($hostname) {
        global $PROCESSING_HOSTS;
        $appionPathAddon = 0; // This represents the number of path levels of the leginon path to an image to add to the appion path?
        if (defined('APPION_PARENT_ADDITION') && APPION_PARENT_ADDITION != 0)
            $appionPathAddon = APPION_PARENT_ADDITION;

        if (empty($PROCESSING_HOSTS))
            return;
        foreach ($PROCESSING_HOSTS as $hostconfig) {
            // We have an issue with machines that have multiple host names.
            // as a quick fix, we added an 'alias' field in the 
            // config file. This alias name will only be used for
            // identification during this cluster object construction.
            if ($hostconfig['host'] == $hostname || $hostconfig['alias'] == $hostname) {
                $this->loadConfig($hostconfig);
                break;
            }
        }

        // Error if the hostname was not found in the config file
        if (is_null($this->hostname)) {
            throw new Exception("Trying to establish a connection with an unknown host ($hostname). Ask your sys admin to add this host to your configuration file.");
        }

        $this->setRemoteOutputPath($appionPathAddon);
    }

    function loadConfig($hostconfig) {
        $this->hostname = $hostconfig['host'];
        $this->nodesDef = $hostconfig['nodesdef'];
        $this->nodesMax = $hostconfig['nodesmax'];
        $this->ppnDef = $hostconfig['ppndef'];
        $this->ppnMax = $hostconfig['ppnmax'];
        $this->reconPerNodeDef = $hostconfig['reconpn']; // default reconstructions per node
        $this->wallTimeDef = $hostconfig['walltimedef'];
        $this->wallTimeMax = $hostconfig['walltimemax'];
        $this->cpuTimeDef = $hostconfig['cputimedef'];
        $this->cpuTimeMax = $hostconfig['cputimemax'];
        $this->memoryMax = $hostconfig['memorymax'];
        $this->appionBin = $hostconfig['appionbin']; // location of appion scripts on cluster, must end in slash, e.g., /usr/local/appion/bin/
        $this->appionLibDir = $hostconfig['appionlibdir']; // location of appionlib directory on cluster, must end in slash, e.g., /usr/local/appion/appionlib
        $this->baseoutdir = $hostconfig['baseoutdir'];
        $this->localHelperHost = $hostconfig['localhelperhost'];
        $this->dirSeparator = $hostconfig['dirsep']; // eg. "/"	
        $this->wrapperPath = $hostconfig['wrapperpath'];
        $this->loginMethod = $hostconfig['loginmethod'];
        $this->loginUsername = $hostconfig['loginusername'];
        $this->passPhrase = $hostconfig['passphrase'];
        $this->publicKey = $hostconfig['publickey'];
        $this->privateKey = $hostconfig['privatekey'];
        $this->gpus = $hostconfig['gpus'];
        $this->queues = $hostconfig['queues']; //an array of queues available on this cluster
    }

    function getHostName() {
        return $this->hostname;
    }

    function getNodesDef() {
        return $this->nodesDef;
    }

    function getNodesMax() {
        return $this->nodesMax;
    }

    function getPpnDef() {
        return $this->ppnDef;
    }

    function getPpnMax() {
        return $this->ppnMax;
    }

    function getRpnDef() {
        return $this->reconPerNodeDef;
    }

    function getWallTimeDef() {
        return $this->wallTimeDef;
    }

    function getWallTimeMax() {
        return $this->wallTimeMax;
    }

    function getCpuTimeDef() {
        return $this->cpuTimeDef;
    }

    function getCpuTimeMax() {
        return $this->cpuTimeMax;
    }

    function getMemoryMax() {
        return $this->memoryMax;
    }

    function getAppionBinDir() {
        return $this->appionBin;
    }

    function getAppionLibDir() {
        return $this->appionLibDir;
    }

    function getWrapperPath() {
        return $this->wrapperPath;
    }

    function getRemoteOutputPath() {
        return $this->remoteOutputPath;
    }

    function getLocalHelperHost() {
        return $this->localHelperHost;
    }

    function getLoginMethod() {
        return $this->loginMethod;
    }

    function getUsername() {
        return $this->loginUsername;
    }

    function getPublicKey() {
        return $this->publicKey;
    }

    function getPrivateKey() {
        return $this->privateKey;
    }

    function getPassPhrase() {
        return $this->passPhrase;
    }

    function getGpus() {
        return $this->gpus;
    }

    function getQueues() {
        return $this->queues;
    }

    function getQueue() {
        return !empty($this->queues) ? $this->queues[0] : '';
    }

    function hasGpu() {
        return !empty($this->gpus);
    }

    function usesLoginMethod() {
        $method = $this->loginMethod;
        if ("SHAREDKEY" == $method || "USERPASSWORD" == $method) {
            return true;
        }
        return false;
    }

    function setLoginMethod($method) {
        if ("SHAREDKEY" == $method || "USERPASSWORD" == $method)
            $this->loginMethod = $method;
        else
            throw new Exception("Trying to set unknown login Method");
    }

    function setUsername($userName) {
        $this->username = $userName;
    }

    function setPassphrase($passPhrase) {
        $this->passphrase = $passPhrase;
    }

    function setPubkeyfile($keyfile) {
        if (@is_file($keyfile)) {
            $this->publickeyFile = $keyfile;
        } else
            throw new Exception("Can not read public key file.");
    }

    function setPrikeyfile($keyfile) {
        if (@is_file($keyfile)) {
            $this->privatekeyFile = $keyfile;
        } else
            throw new Exception("Can not read private key file");
    }

    // Sets the base path that appion Run directories should be set to.
    // $appionPathAddon is for feature #2470 which allows a level of the path to the
    // leginon image file to be added to the appion path, such as a username.
    // TODO: this uses Path::join() which is only working for "/" as as dir separator
    // Should we make the path function non-static? This class shoulld remain separator neutral!
    function setRemoteOutputPath($appionPathAddon) {
        $leginondata = new leginondata();
        // TODO: should we pass in the expID?
        $sessiondata = $leginondata->getSessionInfo($_GET['expId']);
        $sessionname = $sessiondata['Name'];
        $leginon_imagepath = $sessiondata['Image path'];
        $addition_parts = array(); // additional directories to add to the path prior to session name

        if ($appionPathAddon != 0) {
            $parts = explode($this->dirSeparator, $leginon_imagepath);
            $session_index = array_search($sessionname, $parts);
            if ($session_index !== false) {
                // add extra directory division prior to sessionname
                $addition_parts = array_splice($parts, $session_index - $appionPathAddon, $appionPathAddon);
            }
        }

        $rootpath = Path::join(implode($this->dirSeparator, $addition_parts), $sessionname);
        //$rootpath = $sessionname.$this->dirSeparator."recon".$this->dirSeparator;
        // if no baseoutdir was provided, set it to the current user's home directory 
        if ($this->baseoutdir === "") {
            $this->baseoutdir = Path::join('~' . $_SESSION['username'], "appion");
        }

        $remoteOutputPath = Path::join($this->baseoutdir, $rootpath);
        $remoteOutputPath = ($_POST['clusterpath']) ? $_POST['clusterpath'] : $remoteOutputPath;
        // Some forms are calling this 'remoteoutdir'
        $remoteOutputPath = ($_POST['remoteoutdir']) ? $_POST['remoteoutdir'] : $remoteOutputPath;
        $this->remoteOutputPath = $this->formatEndPath($remoteOutputPath);
    }

    function getPath($outdir = "recon") {
        $path = $_POST['clusterpath'] ? $_POST['clusterpath'] : $this->remoteOutputPath;
        // Check what the current basename is and don't add the outdir if they match.
        // There is a good chance that the page is being reloaded and we don't want it to occur mutiple times.
        if (basename($path) != $outdir) {
            $path = Path::join($path, $outdir);
        }
        $path = $this->formatEndPath($path);
        return $path;
    }

    // make sure a path ends with a single path separator.
    // uses the separator defined in the config file specific to this cluster instance.
    function formatEndPath($path) {
        return Path::formatEndPath($path, $this->dirSeparator);
    }

    //Returns all available queues on this cluster in an array
    function getAvailableQueues() {
        $queueArray = $this->getQueues();

        return $queueArray;
    }

    function executeOnHost($username, $password, $command, $returnResult = false, $port = 22, $max_time = 1) {// max time to wait for a result in seconds. I've seen it take 4 seconds, but this may need to be higher.
        $result = false;

        // dcshrum@fsu.edu - added this in conjunction with line 112 in /config.php
        // The returned custom response is customized by the web service to match whatever 
        // the calling code is looking for.  
        if ((WEBSERVICE_URL) and defined('WEBSERVICE_URL')) {
            
            $inputArray = array("session-data"=> $_SESSION, "command" => $command);
            $clean_json=json_encode($inputArray);
            $response = $this->external_exec("POST", $clean_json);
            $ar = json_decode($response, true);
            
            //echo "&#9992;<dl><dt>Command: " . $clean_json . "</dt>";
            //echo "<dd>Response: " . $response . "</dd></dl></li>";
            if ($ar['customResponse'] === 400) {
                echo '<div style="border: 12px rgb(247, 10, 10) dashed;">';
                echo '<h3>The webservice is not configured to handle a command that was sent.</h3>';
                echo "<li>The json content sent with this command: " . $clean_json . "</li>";

                echo "<dl><Dt>A backtrace of the function(s) that sent this command</dt>";
                $trace = debug_backtrace();
                foreach (debug_backtrace() as $trace) {
                    echo sprintf("<dd>%s:%s %s::%s", $trace['file'], $trace['line'], $trace['class'], $trace['function']);
                    echo "</dd>";
                }
                echo "</dl>";
                echo '</div>';
                return "";
            }
            
            return $ar['customResponse'];
        }

        if (!$connection = $this->authenticatedConnection($username, $password)) {
            throw new Exception("Authentication Failure, verify login credentials");
        }

        if (!$stream = ssh2_exec($connection, $command)) {
            $msg = "Could not run command on remote host " . $this->getHostName() . ".";
            throw new Exception($msg);
        }

        // return now if it is not important to know that a result was returned in the stream
        if (!$returnResult)
            return true;

        // Setting blocking to true can cause it to hang.
        stream_set_blocking($stream, false);

        //error_log("Command = ".$command." max_time =".$max_time);
        // This block will wait a given time to get a result from the output stream.
        $start_time = time();
        while (empty($result) && (( time() - $start_time ) < $max_time )) {
            if (function_exists("stream_get_contents")) {
                $result = stream_get_contents($stream);
            } else {
                $result = fread($stream, 4096);
            }
        }

        //error_log("Command Result = ".$result." Port = "."$port");
        // This is just for testing
//	  	$totalTime = time() - $start_time;
//	  	echo " <----------> Time in execute running $command: ---> ";
//	  	echo $totalTime;
        // We get here if we timed out before getting a result. Not throwing an
        // exception because some commands like mkdir will never return a result.
        // In this case, the command should be executed with $returnResult set to false.
        if (empty($result)) {
            $msg = "Command timed out on remote host " . $this->getHostName() . ".";
            //throw new Exception($msg);
        }

        // close the stream
        fclose($stream);

        return $result;
    }

    function copyToHost($username, $password, $localfile, $remotefile, $mode = 0644, $port = 22) {
        //Check that the local file exists
        if (!@is_file($localfile)) {
            throw new Exception("File doesn't exists $localfile");
        }


        if (!($connection = $this->authenticatedConnection($username, $password))) {
            throw new Exception("Authentication Failure, verify login credentials");
        }

        if (ssh2_scp_send($connection, $localfile, $remotefile, $mode)) {
            ssh2_exec($connection, 'exit');
            $result = true;
        } else {
            $msg = "Could not copy file to host " . $this->getHostName() . ".  Check permissions on remote file or directory.";
            throw new Exception($msg);
        }

        return $result;
    }

    // returns an ssh connection object which has already been authenticated 
    // using the method specified by $this->loginMehod
    private function authenticatedConnection($username, $password, $port = 22) {

        if (!($connection = ssh2_connect($this->getHostName(), $port))) {
            $msg = "Unable to establish a connection to remote host " . $this->getHostName() . "!";
            throw new Exception($msg);
        }

        $loginMethod = $this->getLoginMethod();
        switch ($loginMethod) {
            case "USERPASSWORD":

                $result = ssh2_auth_password($connection, $username, $password);

                if (!$result) {
                    // check that the server has not blocked ssh2 password authentication
                    $auth_methods = ssh2_auth_none($connection, $username);

                    if ($auth_methods === false) {
                        $msg = "Failure authenticating login to " . $this->getHostName() . ", for user " . $username . ". Unable to determine available host login methods.";
                    } else if (in_array('password', $auth_methods)) {
                        $msg = "Failure authenticating login to " . $this->getHostName() . ", verify login credentials for user " . $username;
                    } else {
                        $msg = "Trying to connect to remote host using password based authentication which is not enabled by " . $this->getHostName() . ".";
                    }
                    throw new Exception($msg);
                }
                break;
            case "SHAREDKEY":
                $pass = $this->getPassPhrase();
                if ($pass === false) {
                    $pass = $password;
                }
                $user = $this->getUserName();
                if ($user == "") {
                    $user = $username;
                }
                $result = ssh2_auth_pubkey_file($connection, $user, $this->getPublicKey(), $this->getPrivateKey(), $pass);
                if (!$result) {
                    $msg = "Failure authenticating login credentials for " . $user . " on " . $this->getHostName() . " using shared key. Verify login credentials.";
                    throw new Exception($msg);
                }
                break;

            default:
                $msg = "Can not login to " . $this->getHostName() . ". Unknown login authentication method.";
                throw new Exception($msg);
        }

        return $connection;
    }

    private function external_exec($method, $content) {
        $ch = curl_init(WEBSERVICE_URL);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_HTTPHEADER, Array("Content-Type: application/json"));
        curl_setopt($ch, CURLOPT_FOLLOWLOCATION, true);

        //Can be GET - read/  POST - create / PUT - update  / DELETE - delete
        curl_setopt($ch, CURLOPT_CUSTOMREQUEST, $method);
        if ($method === "POST") {
            curl_setopt($ch, CURLOPT_POSTFIELDS, $content);
        }
        try {

            $response = curl_exec($ch);

            if (curl_error($ch)) {
                curl_close($ch);
                return curl_error($ch);
            }

            curl_close($ch);

            return $response;
        } catch (Exception $e) {
            throw $e;
        }
    }

}

?>
