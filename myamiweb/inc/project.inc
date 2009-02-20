<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

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
		return $info;
	}

	function getProjects($type=""){
                $projects = array();
		if ($type=="all")  
			$projects[] = array(	0 => DEFAULT_PROJECT, 'id' => DEFAULT_PROJECT,
						1 => DEFAULT_PROJECT, 'name' => DEFAULT_PROJECT);
                $q='select projectId, name  from projects order by name';
                $RprojectInfo = $this->mysql->SQLQuery($q);
                while ($row = mysql_fetch_array($RprojectInfo))
                        $projects[]=array(0 => $row[projectId], 'id' => $row[projectId],
                                          1 => $row[name], 'name' => $row[name] );
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
		return $r;
	}

}
?>
