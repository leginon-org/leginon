<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "inc/dbemauth.php";

$me=($_SERVER['REMOTE_ADDR']=="137.131.204.65") ? true : false;

define('DEFAULT_PROJECT', 'all'); 
define('PROJECT_DB_HOST', $PROJECT_DB_HOST);
define('PROJECT_DB_USER', $PROJECT_DB_USER);
define('PROJECT_DB_PASS', $PROJECT_DB_PASS);
define('PROJECT_DB', $PROJECT_DB);

function setDatabase() {
	global $me;
	$leginondata=&new leginondata;
	$expId= ($_POST['sessionId']) ? $_POST['sessionId'] : $_GET['expId'];
	$projectId = ($_POST['projectId']) ? $_POST['projectId'] : $_GET['projectId'];
	if ($projectId) {
		$sessions = $leginondata->getSessions('description', $projectId);
		$sessionId_exists = $leginondata->sessionIdExists($sessions, $expId);
		if (!$sessionId_exists) {
			$expId=$sessions[0]['id'];
		}
	}
	if (!$expId) {
		if ($_GET['session']) {
			$expId=$_GET['session'];
		} else {
			$expId=$leginondata->getLastSessionId();
		}
	}
	$p=new project();
	$r=$p->getProjectfromSessionId($expId);
	$projectId=$r['projectId'];
	$db="ap".$projectId;
	$_SESSION['processingdb']=$db;
	$_SESSION['expId']=$expId;
	return $db;
}

if (!$PROCESSING_DB) {
	$PROCESSING_DB=setDatabase();
}

define(PARTICLE_DB, $PROCESSING_DB);

class project {

	function project(){
		$this->mysql = new mysql(	PROJECT_DB_HOST, PROJECT_DB_USER,
						PROJECT_DB_PASS, PROJECT_DB);
        }

	function checkDBConnection() {
		return $this->mysql->checkDBConnection();
	}

	function getGridInfo($gridId){
		$q='select g.gridId, label as "label", '
		  .'date_format(g.prepdate,"%m/%e/%Y") as prepdate, '
		  .'g.specimenId, '
		  .'g.substrate, '
		  .'g.preparation, '
		  .'g.number, '
		  .'g.note, '
		  .'g.boxId, '
		  .'g.peopleId, '
		  .'l.location '
		  .'from grids g '
		  .'left join gridlocations l '
		  .'on (l.gridId = g.gridId) '
		  .'where g.gridId="'.$gridId.'"';

		list($info) = $this->mysql->getSQLResult($q);
		return $info;
	}

	function getProjectfromSession($session) {
		$q='select p.projectId, p.name  '
			.'from projectexperiments pe '
			.'left join projects p '
			.'on (pe.projectId=p.projectId) '
		  .'where pe.name="'.$session.'"';

		list($info) = $this->mysql->getSQLResult($q);

		$projectId=$info['projectId'];

		if ($this->isRestricted($projectId)) {
			return "restricted";
		}
		return $info;
	}

	function getProjectfromSessionId($sessionid) {
		$dbemdata = &new leginondata;
		$db  = &$dbemdata->mysql;
		$q='select `name` as sessionname '
			.'from `SessionData` '
			.'where `DEF_id`='.$sessionid;
		list($r)=$db->getSQLResult($q);
		$sname=$r[sessionname];
 		$q='select p.projectId, p.name  '
 			.'from projectexperiments pe '
 			.'left join projects p '
 			.'on (pe.projectId=p.projectId) '
 		  .'where pe.name="'.$sname.'"';
		list($info) = $this->mysql->getSQLResult($q);

		$projectId=$info['projectId'];
		
		if ($this->isRestricted($projectId)) {
			return "restricted";
		}
		return $info;
	}

	function getProjects($type=""){
		global $dbemauth;
		$login_check = $dbemauth->is_logged();
		$projects = array();
		if ($type=="all")  
			$projects[] = array(	'id' => DEFAULT_PROJECT, 'name' => DEFAULT_PROJECT);
		$q='select projectId as id, name  from projects order by name';
		$rprojects = $this->mysql->getSQLResult($q);
		$projects = array_merge($projects, $rprojects);

		$projects=$this->restrict($projects, $login_check);

		return $projects;
	}

	function getSample($sessionId="") {
		# get sample name from project database
		$sample="";
		return $sample;
	}

	function getProjectInfo($projectId) {
		$q='select projectId, name  from projects '
			.'where projectId='.$projectId;
		list($r)=$this->mysql->getSQLResult($q);

		if ($this->isRestricted($projectId)) {
			return array();
		}
		return $r;
	}

	function getRestritedProject($projectId="") {
		$q="select r.projectId, r.type, u.username from restriction r left join pis u on (u.projectId=r.projectId)";
		if (is_numeric($projectId)) {
			$q.=" where r.projectId=$projectId ";
		}
		$r=$this->mysql->getSQLResult($q);
		return $r;
	}

	function restrict($projects, $authentication) {
		### check if is admin ###
		if ($authentication[2]==2) {
			return $projects;
		}
		### check if user belongs to restricted projects ###
		$rprojects=$this->getRestritedProject();
		$username=$authentication[0];
		$rprojectIds=array();
		foreach ($rprojects as $rp) {
			if ($rp['type']=='USER' && $rp['username']==$username) {
				continue;
			}
			$rprojectIds[]=$rp['projectId'];
		}
		
		$newprojects=array();
		foreach ($projects as $p) {
			if (in_array($p['id'], $rprojectIds)) {
				continue;
			}
			$newprojects[]=$p;
		}
		return $newprojects;
	}

	function isRestricted($projectId) {
		global $dbemauth;
		$authentication = $dbemauth->is_logged();
		if ($authentication[2]==2) {
			return false;
		}
		$username=$authentication[0];
		$rprojects=$this->getRestritedProject($projectId);
		
		if (!$rprojects)
			return false;
		$isrestricted=true;
		foreach ($rprojects as $rp) {
			if ($rp['type']=='USER' && $rp['username']==$username) {
				$isrestricted=false;
				break;
			}
		}
		return $isrestricted;
	}

	function hasProjectId($projectId, $projects) {
		$exists=false;
		foreach ((array)$projects as $p) {
			if ($p['projectId']==$projectId) {
				$exists=true;
				break;
			}
		}
		return $exists;
	}

}
?>
