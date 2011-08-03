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
	function getRemoteOutputPath() 	{ return $this->remoteOutputPath; }
	function getLocalHelperHost()   { return $this->localHelperHost; }
	
	function setRemoteOutputPath()
	{
		$leginondata = new leginondata();
		// TODO: should we pass in the expID?
		$sessiondata = $leginondata->getSessionInfo($_GET['expId']);
		$sessionname = $sessiondata['Name'];
		// TODO: need to pass in the folder name 
		// TODO: we have an extra slash in our paths. Should we make everything seperator independent?
		$rootpath = $sessionname."/recon/";
		
		// if no baseoutdir was provided, set it to the current user's home directory 
		if ( $this->baseoutdir === "") {
			 $this->baseoutdir = '~'.$_SESSION['username']."/appion/";
		}

		$remoteOutputPath = $this->baseoutdir.$rootpath;
		$this->remoteOutputPath = ($_POST['clusterpath']) ? $_POST['clusterpath'] : $remoteOutputPath;		
	}

	function get_path() {
		$path = $_POST['clusterpath'] ? $_POST['clusterpath'] : $this->remoteOutputPath;
		return $path;
	}

	function post_data() 
	{
		throw new Exception("The post_data function has been depricated, yet it was just called! Fix Me!!");
	}

	function cluster_parameters() 
	{
		throw new Exception("The cluster_parameters function has been depricated, yet it was just called! Fix Me!!");
	}

	function cluster_cmd($host, $user, $pass) 
	{
		throw new Exception("The cluster_cmd function has been depricated, yet it was just called! Fix Me!!");
	}

	function cluster_send_data() 
	{
		throw new Exception("The cluster_send_data function has been depricated, yet it was just called! Fix Me!!");
	}

	function cluster_receive_data() 
	{
		throw new Exception("The cluster_receive_data function has been depricated, yet it was just called! Fix Me!!");
	}

	function cluster_job_file($job) 
	{
		throw new Exception("The cluster_job_file function has been depricated, yet it was just called! Fix Me!!");
	}

	function cluster_check_msg() 
	{
		throw new Exception("The cluster_check_msg function has been depricated, yet it was just called! Fix Me!!");
	}

	function get_javascript() 
	{
		throw new Exception("The get_javascript function has been depricated, yet it was just called! Fix Me!!");
	}

	function formatEndPath($path) {
		$path = ereg($this->dirSeparator."$", $path) ? $path : $path.$this->dirSeparator;
		return $path;
	}
}
?>
