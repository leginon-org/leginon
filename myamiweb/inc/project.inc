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

		if ($this->isRestricted($projectId)) {
			return "restricted";
		}
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
		
		if ($this->isRestricted($projectId)) {
			return "restricted";
		}
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
		$checkForHidden = (array_key_exists('hidden', $projectdef));
		
		if ($checkForHidden) {
			$checkForHiddenQuery = " projects.hidden !=1 OR projects.hidden IS NULL ";
		} 
		
		// Begin SQL to select the projects that the user may view
		$q = 'SELECT projects.`DEF_id` as id, projects.name FROM projects ';
		
		// Build the query based on the combination of checking for the hidden flag
		// and showing only projects owned by the user
		if ($checkForHidden && $findOwnedProjects == false) {
			$q .= " WHERE ";
			$q .= $checkForHiddenQuery;
		} else if ($checkForHidden && $findOwnedProjects) {
			$q .= " WHERE ";
			$q .= $checkForHiddenQuery;
			$q .= " AND ( ";
			$q .= $ownedProjectsQuery;
			$q .= " ) ";
		} else if ($checkForHidden == false && $findOwnedProjects) {
			$q .= " WHERE ";
			$q .= $ownedProjectsQuery;
		}
		
		// Make sure the projects appear in alphabetical order
		$q .= ' ORDER by name';
		
		$rprojects = $this->mysql->getSQLResult($q);

		$projects = array();
		if ($type=="all") {
			$projects[] = array(	'id' => DEFAULT_PROJECT, 'name' => DEFAULT_PROJECT);
		}
		$projects = array_merge($projects, $rprojects);

		if (ENABLE_LOGIN) {
			$login_check = $dbemauth->is_logged();
			$projects=$this->restrict($projects, $login_check);
		}
		return $projects;
	}

	function getSample($sessionId="") {
		# get sample name from project database
		$sample="";
		return $sample;
	}

	function getProjectInfo($projectId) {
		$q='select DEF_id AS projectId, name  from projects '
			.'where DEF_id='.$projectId;
		list($r)=$this->mysql->getSQLResult($q);

		if (ENABLE_LOGIN && $this->isRestricted($projectId)) {
			return array();
		}
		return $r;
	}

	function getRestrictedProject($projectId="") {
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
		$rprojects=$this->getRestrictedProject();
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
		if (!ENABLE_LOGIN) {
			return;
		}
		global $dbemauth;
		$authentication = $dbemauth->is_logged();
		if ($authentication[2]==2) {
			return false;
		}
		$username=$authentication[0];
		$rprojects=$this->getRestrictedProject($projectId);
		
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

	function getRestrictedSessions() {
		global $dbemauth;
		$rsessions=array();
		$r=array();
		$allowprojects=array();
		$authentication = $dbemauth->is_logged();
		$username=$authentication[0];
		if ($authentication[2]==2) {
			return $rsessions;
		}
		$rprojects=$this->getRestrictedProject();
		foreach ($rprojects as $rp) {
			if ($rp['type']=='USER' && $rp['username']==$username) {
				$allowprojects[]=$rp['projectId'];
				continue;
			}
			if (in_array($rp['projectId'], $allowprojects)) {
				continue;
			}
			$q = 'SELECT '.DB_LEGINON.'.SessionData.name '
				.'FROM '.DB_LEGINON.'.SessionData '
				.'WHERE '.DB_LEGINON.'.SessionData.DEF_id IN ( '
				.'SELECT pe.`REF|leginondata|SessionData|session`  '
				.'FROM projectexperiments pe '
				.'WHERE pe.`REF|projects|project`="'.$rp['projectId'].'" ) ';
			$r = $this->mysql->getSQLResult($q);
			$r = array_merge($r, $r);
		}
		foreach ($r as $rs) {
			if (!in_array($rs['name'], $rsessions)) {
				$rsessions[]=$rs['name'];
			}
		}
		return $rsessions;
	}

	function getSessions($sessions) {
		if (!ENABLE_LOGIN) {
				return $sessions;
			}
			$rsessions=$this->getRestrictedSessions();
			$nsessions=array();
			foreach ($sessions as $s) {
				$id=$s['name_org'];
				if (!in_array($id, $rsessions)) {
					$nsessions[]=$s;
				}
			}
		return $nsessions;
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
