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
}
?>
