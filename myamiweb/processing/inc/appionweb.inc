<?php

require_once "particledata.inc";
require_once "inc/login.inc";
require_once "processing.inc";

class appionweb{
	private $pageInfo;		/* type array, contain page title and page header */
	private $projectInfo;	/* type array, contain project name, session name, purpose, image path */
	private $sessionId;		/* type int, session number under each project */
	private $runName;		/* type string, name of this processing run */
	private $outDir;		/* type string, path of output directory */
	private $runDir;		/* type string, job run directory */
	private $description;	/* type string, description of this job */
	private $dbCommit;		/* type boolean, commit to database or not */
	private $showCommand;	/* type boolean, show job command */
	private $runCommand;	/* type boolean, run job command */
	private $processingHost;/* type string, processing host selection */
	private $hostLoginAuth;	/* type array, contain processing host login information */
	private $errorMsg;		/* type array, contain list of error messages */
	
	public $particle;		/* particle data object */
	
	/* constructor setups default values and classes */
	function __construct($title, $header, $sessionId = null, $projectId = null){
	//TODO: need a way to take care special case when there is no session id like image up-loader etc..
		
		if(!is_numeric($sessionId) && !is_numeric($projectId)){
			// error message show wrong value type url
			exit();
		}
		// check if current user has privilege to access current session
		checkExptAccessPrivilege($sessionId,'data');
		
		// create instance of particledata
		$this->particle = new particledata();
		
		$this->setPageInfo($title, $header);
		$this->setSessionId($sessionId);
		
		// get project and session information by given sessionId.
		$projectdata = new project();
		$sessiondata=getSessionList($projectId,$sessionId);
		$sessioninfo=$sessiondata['info'];
		
		
		
		$projectId = getProjectId();
		$currentproject = $projectdata->getProjectInfo($projectId);
	
	}
	
	/* private variables setter */
	function setPageInfo($title, $header){
		$this->pageInfo = array('title' => $title,
								'header' => $header);	
	}
	
	function setProjectInfo($sessionId){
		$this->projectInfo = array('projectName' => $projectName,
								   'sessionName' => $sessionName,
								   'purpose' => $purpose,
								   'imagePath' => $imagePath);
	}

	private function setSessionId($sessionId){
		$this->sessionId = $sessionId;
	}
	function setRunName($runName){
		$this->runName = $runName;
	}
	function setOutDir($outDir){
		$this->outDir = $outDir;
	}
	function setRunDir($runDir){
		$this->runDir = $runDir;
	}
	function setDescription($description){
		$this->description = $description;
	}
	function setDbCommit($dbCommit){
		$this->dbCommit = $dbCommit;
	}
	function setProcessingHost($processingHost){
		$this->processingHost = $processingHost;
	}
	function setShowCommand($showCommand){
		$this->showCommand = $showCommand;
	}
	function setRunCommand($runCommand){
		$this->runCommand = $runCommand;
	}
	function setHostLoginAuth($host, $hostUsername, $hostPassword){
		
		$this->hostLoginAuth = array('host' => $host,
									 'hostUsername' => $hostUsername,
									 'hostPassword' => $hostPassword);
	
	}
	function setErrorMsg($errorMsg){
		$this->errorMsg = $errorMsg;
	}
	
	
	/* private variable getter */
	function getPageInfo()		{ return $this->pageInfo; }
	function getProjectInfo()	{ return $this->projectInfo; }
	function getSessionId()		{ return $this->sessionId; }
	function getRunName()		{ return $this->runName; }
	function getOutDir()		{ return $this->outDir;	}
	function getRunDir()		{ return $this->runDir;	}
	function getDescription()	{ return $this->description; }
	function getDbCommit()		{ return $this->dbCommit; }
	function getProcessingHost(){ return $this->processingHost;	}
	function getShowCommand()	{ return $this->showCommand; }
	function getRunCommand()	{ return $this->runCommand; }
	function getHostLoginAuth()	{ return $this->hostLoginAuth; }
	function getErrorMsg()		{ return $this->errorMsg; }
}
?>
