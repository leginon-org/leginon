<?php

/**
 * This class allows you to customize your cluster params
 * You can add/modify:
 *	- job file input
 *	- form input
 *	- javqascript check
 *
 * Note: each cluster file must be register in config_processing.php
 **/
require_once "inc/leginon.inc";

class Cluster 
{
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
	private $dirSeparator; // eg. "/"
	private $remoteOutputPath;
	private $baseoutdir;
	private $localHelperHost; // local host used by remote host to rsync results
	private $loginMehtod;     //Method used to login to cluster curently only USERPASSWORD or SHAREDKEY
	private $loginUserName;   //Username for shared logins
	private $publicKey;		  //Location of publickey file(s)
	private $privateKey;	  //Location of private key file(s)
	private $passPhrase;	  //passPhrase if it is to be stored in cluster config
	
	
	function __construct( $hostname )
	{
		global $PROCESSING_HOSTS;
		
		foreach ( $PROCESSING_HOSTS as $hostconfig ) {
			if ( $hostconfig['host'] == $hostname ) {
				$this->loadConfig( $hostconfig );
				break;
			}
		}
		$this->setRemoteOutputPath();
	}

	function loadConfig( $hostconfig )
	{
		$this->hostname 		= $hostconfig['host'];
		$this->nodesDef 		= $hostconfig['nodesdef'];
		$this->nodesMax 		= $hostconfig['nodesmax'];
		$this->ppnDef 			= $hostconfig['ppndef'];
		$this->ppnMax 			= $hostconfig['ppnmax'];
		$this->reconPerNodeDef 	= $hostconfig['reconpn']; // default reconstructions per node
		$this->wallTimeDef 		= $hostconfig['walltimedef'];
		$this->wallTimeMax 		= $hostconfig['walltimemax'];
		$this->cpuTimeDef 		= $hostconfig['cputimedef'];
		$this->cpuTimeMax 		= $hostconfig['cputimemax'];
		$this->memoryMax 		= $hostconfig['memorymax'];
		$this->appionBin 		= $hostconfig['appionbin']; // location of appion scripts on cluster, must end in slash, e.g., /usr/local/appion/bin/
		$this->baseoutdir		= $hostconfig['baseoutdir'];
		$this->localHelperHost 	= $hostconfig['localhelperhost'];
		$this->dirSeparator 	= $hostconfig['dirsep']; // eg. "/"	
		$this->wrapperPath		= $hostconfig['wrapperpath'];	
		$this->loginMethod		= $hostconfig['loginmethod'];
		$this->loginUsername	= $hostconfig['loginusername'];
		$this->passPhrase		= $hostconfig['passphrase'];
		$this->publicKey		= $hostconfig['publickey'];
		$this->privateKey       = $hostconfig['privatekey'];
	}
	
	function getHostName() 		{ return $this->hostname; }
	function getNodesDef() 		{ return $this->nodesDef; }
	function getNodesMax() 		{ return $this->nodesMax; }
	function getPpnDef()   		{ return $this->ppnDef; }
	function getPpnMax()   		{ return $this->ppnMax; }
	function getRpnDef() 		{ return $this->reconPerNodeDef; }
	function getWallTimeDef() 	{ return $this->wallTimeDef; }
	function getWallTimeMax()	{ return $this->wallTimeMax; }
	function getCpuTimeDef() 	{ return $this->cpuTimeDef; }
	function getCpuTimeMax() 	{ return $this->cpuTimeMax; }
	function getMemoryMax() 	{ return $this->memoryMax; }
	function getAppionBinDir() 	{ return $this->appionBin; }
	function getWrapperPath()   { return $this->wrapperPath; }
	function getRemoteOutputPath() 	{ return $this->remoteOutputPath; }
	function getLocalHelperHost()   { return $this->localHelperHost; }
 	function getLoginMethod() 	{ return $this->loginMethod; }
	function getUsername() 		{ return $this->loginUsername; }
	function getPublicKey()	{ return $this->publicKey;}
	function getPrivateKey()	{ return $this->privateKey; }
	function getPassPhrase()	{ return $this->passPhrase; }
	
	function usesLoginMethod()
	{
		$method = $this->loginMethod;
		if ("SHAREDKEY" == $method || "USERPASSWORD" == $method) {
			return true;
		}	
		return false;
	}

   function setLoginMethod($method)
   {
      if ("SHAREDKEY" == $method || "USERPASSWORD" == $method)
         $this->loginMethod = $method;
      else
         throw new Exception("Trying to set unknown login Method");
   }
   
   function setUsername($userName)
   {
      $this->username = $userName;
   }

   function setPassphrase($passPhrase)
   {
      $this->passphrase = $passPhrase;
   }

   function setPubkeyfile($keyfile)
   {
      if (@is_file($keyfile)){
         $this->publickeyFile = $keyfile;
      }
      else
         throw new Exception("Can not read public key file.");
   }

   function setPrikeyfile($keyfile)
   {
      if (@is_file($keyfile)){
         $this->privatekeyFile = $keyfile;
      }
      else
         throw new  Exception("Can not read private key file");
   }
	
	function setRemoteOutputPath()
	{
		$leginondata = new leginondata();
		// TODO: should we pass in the expID?
		$sessiondata = $leginondata->getSessionInfo($_GET['expId']);
		$sessionname = $sessiondata['Name'];
		// TODO: need to pass in the folder name 
		$rootpath = $sessionname.$this->dirSeparator."recon".$this->dirSeparator;
		
		// if no baseoutdir was provided, set it to the current user's home directory 
		if ( $this->baseoutdir === "") {
			 $this->baseoutdir = '~'.$_SESSION['username'].$this->dirSeparator."appion".$this->dirSeparator;
		}

		$remoteOutputPath = $this->formatEndPath($this->baseoutdir).$rootpath;
		$remoteOutputPath = ($_POST['clusterpath']) ? $_POST['clusterpath'] : $remoteOutputPath;
		$this->remoteOutputPath = $this->formatEndPath( $remoteOutputPath ); 		
	}

	function getPath() {
		$path = $_POST['clusterpath'] ? $_POST['clusterpath'] : $this->remoteOutputPath;
		$path = $this->formatEndPath($path);
		return $path;
	}
	
	// make sure a path ends with a single path separator.
	// uses the separator defined in the config file specific to this cluster instance.
	function formatEndPath($path) 
	{
		$path = ereg($this->dirSeparator."$", $path) ? $path : $path.$this->dirSeparator;
		return $path;
	}
	
	function executeOnHost ($username, $password, $command, $port=22)
	{
		$result = false;
				
		if (!$connection = $this->authenticatedConnection($username, $password)) {
			throw new Exception("Authentication Failure, verify login credentials");
		}
		
		if (!$stream = ssh2_exec($connection, $command)) {
			$msg = "Could not run command on remote host ".$this->getHostName().".";
			throw new Exception($msg);
		}
		
		sleep(25.1);

		stream_set_blocking($stream, false);
		if (function_exists("stream_get_contents")) {		
			$result = stream_get_contents($stream);
		} else {
			$result = fread($stream,4096);
			fclose($stream);
		}
		
		return $result;
	}
	
	
	function copyToHost	($username, $password, $localfile, $remotefile, $mode=0644, $port=22)
	{
		//Check that the local file exists
		if (!@is_file($localfile)){
			throw new Exception("File doesn't exists $localfile");
		}
		
		
		if ( !($connection = $this->authenticatedConnection($username, $password)) ){
			throw new Exception("Authentication Failure, verify login credentials");
		}
		
		if (ssh2_scp_send($connection, $localfile, $remotefile, $mode)) {
			ssh2_exec($connection, 'exit');
			$result = true;
		} else {
			$msg = "Could not copy file to host ".$this->getHostName().".  Check permissions on remote file ordirectory";
			throw new Exception( $msg );
		}
	
		return $result;
	}
	
	//returns an ssh connection object which has already been authenticated 
	//the method specified by $this->loginMehod
	private function authenticatedConnection($username, $password, $port=22)
	{
		
		if ( !($connection = ssh2_connect($this->getHostName(), $port)) ) {
			$msg = "Connection to remote host ". $this->getHostName()."!";
			throw new Exception($msg);
		}
		
		$loginMethod = $this->getLoginMethod();
		switch ($loginMethod){
			case "USERPASSWORD":
				$result = ssh2_auth_password($connection, $username, $password);
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
				$result = ssh2_auth_pubkey_file($connection, 
												$user,
												$this->getPublicKey(), 
												$this->getPrivateKey(), 
												$pass);
				break;
		
			default:
				throw new Exception("Unknown login authentication method.");
				
		}
		
		if (!$result){
			$msg = "Failure authenticating login to ".$this->getHostName().", verify login credentials";
			throw new Exception($msg);
		}
		
		return $connection;
	}
}
?>
