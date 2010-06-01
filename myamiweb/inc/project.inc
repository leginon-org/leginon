<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

if (ENABLE_LOGIN) {
	require_once "inc/dbemauth.php";
}

require_once "inc/session.inc";

define('DEFAULT_PROJECT', 'all'); 
define('PROJECT_DB_HOST', $PROJECT_DB_HOST);
define('PROJECT_DB_USER', $PROJECT_DB_USER);
define('PROJECT_DB_PASS', $PROJECT_DB_PASS);
define('PROJECT_DB', $PROJECT_DB);

setsession();

function setDatabase($expId="") {
	$leginondata=&new leginondata;
	if (!$expId) {
		$expId= ($_POST['sessionId']) ? $_POST['sessionId'] : $_GET['expId'];
	}
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
	$db=$p->getProcessingDB($projectId);
	$_SESSION['processingdb']=$db;
	$_SESSION['expId']=$expId;
	return $db;
}

if (!$PROCESSING_DB) {
	$PROCESSING_DB=setDatabase($newexpId);
}

define('PARTICLE_DB', $PROCESSING_DB);

class project {

	function project(){
		$this->mysql = new mysql(	DB_HOST, DB_USER,
			DB_PASS, DB_PROJECT);
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

	function getProjectFromSession($session) {
		$q='select p.`DEF_id` as projectId, p.name  '
			.'from projectexperiments pe '
			.'left join projects p '
			.'on (pe.`REF|projects|project` = p.`DEF_id`) '
			.'left join '.DB_LEGINON.'.`SessionData` s '
			.'on (s.`DEF_id` = pe.`REF|leginondata|SessionData|session`) '
			.'where s.name="'.$session.'"';
		list($info) = $this->mysql->getSQLResult($q);

		$projectId=$info['projectId'];

		return $info;
	}

	function sessionExists($projectId, $sessionId) {
		if (!is_numeric($projectId)) {
			return true;
		}
		$projectinfo = $this->getProjectfromSessionId($sessionId);
		$nprojectId = $projectinfo['projectId'];
		return ($nprojectId==$projectId) ? true : false;
	}

	function getProjectfromSessionId($sessionId) {
 		$q="SELECT projexp.`REF|projects|project` AS projectId  "
			."FROM projectexperiments AS projexp "
			."WHERE projexp.`REF|leginondata|SessionData|session` = '$sessionId' ";
		list($info) = $this->mysql->getSQLResult($q);

		$projectId=$info['projectId'];
		
		return $info;
	}

	function getProjects($type=""){
		
		$userId = getLoginUserId();
		$privilege_level = privilege('projects');
		global $dbemauth;
		
		// If the users privilege level is admin(4) or power user(3),
		// they may view all projects, otherwise they may only 
		// view projects they own or projects that contain experiments
		// that have been shared with the user.
		$findOwnedProjects = ($privilege_level <= 2 && $userId); 

		if ($findOwnedProjects) {		
			$sharedProjectsQuery = " SELECT ".DB_PROJECT.".projectexperiments.`REF|projects|project` "
				." FROM ".DB_PROJECT.".projectexperiments " 
				." WHERE ".DB_PROJECT.".projectexperiments.`REF|leginondata|SessionData|session` IN ( "
						." SELECT ".DB_PROJECT.".shareexperiments.`REF|leginondata|SessionData|experiment` "
						." FROM ".DB_PROJECT.".shareexperiments "
						." WHERE ".DB_PROJECT.".shareexperiments.`REF|leginondata|UserData|user` = ".$userId." ) ";

			// Build a query to find the projects that are owned by the user, then add on the query to find
			// the projects that are shared with the user.
			$ownedProjectsQuery = "projects.DEF_id IN ( "
				."SELECT projectowners.`REF|projects|project` "
				."FROM projectowners WHERE projectowners.`REF|leginondata|UserData|user` = ".$userId." ) " 
				."OR projects.DEF_id IN ( ".$sharedProjectsQuery." )";
		}
		
		// The hidden field of the projects table apparently may not exist. 
		// Don't know the history of that.
		// If it does exist, we do not want to show hidden projects
		$projectdef = $this->mysql->getFieldTypes('projects');
		
		// Begin SQL to select the projects that the user may view
		$q = "SELECT projexp.`REF|projects|project` AS id, "
			."   projects.`name` AS name, "
			."   DATEDIFF(NOW(), MAX(projexp.`DEF_timestamp`)) AS age "
			." FROM projectexperiments AS projexp "
			." LEFT JOIN projects "
			."   ON projects.`DEF_id` = projexp.`REF|projects|project` "
			." WHERE projexp.`REF|projects|project` IS NOT NULL AND projects.`name` IS NOT NULL ";

		// Build the query based on the combination of checking for the hidden flag
		// and showing only projects owned by the user
		if ($findOwnedProjects) {
			$q .= " AND ( ".$ownedProjectsQuery." ) ";
		}
		
		$q .= " GROUP BY projexp.`REF|projects|project` ";

		// Make sure the projects appear in alphabetical order
		$q .= ' ORDER by projects.`name`';
		//echo $q."<br/><br/>\n";

		$rprojects = $this->mysql->getSQLResult($q);

		$projects = array();
		if ($type=="all") {
			$projects[] = array(	'id' => DEFAULT_PROJECT, 'name' => DEFAULT_PROJECT);
		}
		$projects = array_merge($projects, $rprojects);
		return $projects;
	}

	function getSample($sessionId="") {
		# get sample name from project database
		$sample="";
		return $sample;
	}

	function getProjectInfo($projectId) {
		$q='select DEF_id AS projectId, name from projects '
			.'where DEF_id='.$projectId;
		list($r)=$this->mysql->getSQLResult($q);

		return $r;
	}

	function getSessions($sessions) {
		return $sessions;
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

	function getProcessingDB($projectId) {
		$db="";
		$q="select `appiondb` from processingdb "
			."where `REF|projects|project`=$projectId";
		if ($r=$this->mysql->getSQLResult($q)) {
			$db=$r[0]['appiondb'];
		}
		return $db;
	}

}
?>
