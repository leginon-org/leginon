<?php
require_once "../config.php";
require_once "inc/login.inc";
require_once "inc/dbemauth.php";
require_once "inc/menu.inc.php";
require_once "inc/util.inc";
require_once "inc/xmlapplicationimport.inc";

function menu($privilege=1) {
	$link = new iconlink();
	$link->align = 'center';
	$link->cols = 1;
	$link->onimg = "_on.png";
	$link->offimg = "_off.png";
	$link->setImagePath('img/');
	$link->addlink('project.php','View Projects','', 'folder', '');
	$link->addlink('gridtray.php','Grid Tray','', 'preparation', '');
	$link->Display();
}

function project_header($title="", $javascript="") {
	global $_SERVER, $projectauth;

		if (!ereg('login.php', $_SERVER['PHP_SELF'])) {
		}
	$username = $login_check[0];
	$privilege = privilege('users');
	$onload = (empty($javascript)) ? '' : 'onload="'.$javascript.'"';
	$url = "ln=".urlencode($_SERVER['REQUEST_URI']);

	echo '<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
	<html>
	<head>
			<link rel="icon" href="img/favicon.ico" type="image/x-icon">
			<link rel="shorcut icon" href="img/favicon.ico" type="image/x-icon">
			<link rel="StyleSheet" type="text/css" href="css/project.css" >
	';
	if (!empty($title))
		 	echo '<title>',$title,'</title>';
	echo '
	</head>
	<body alink="#00CCCC" vlink="#006699" link="#006699" '.$onload.' >
	';
	echo '
	<table border="0">
	<tr>
	<td rowspan="2" width="100" nowrap="nowrap" align="center">
	';
	echo '
	<img src="img/project_logo.png" alt="[ Logo ]">
	';
	echo'
	</td>
	<td>
	';
	if ($username) {
		echo '<a class="header" href="logout.php">[Logout '.$username.']</a>';
	}
	echo '
	</td>
	</tr>
	<tr>
	<td>
	';
	echo '<h3>',$title,'</h3>';
	echo '
	</td>
	</tr>
	';
	echo '
	<tr>
	<td width="100" valign="top" align="center">
	<div style="border: 1px solid #999999" >
	<!-- Begin Menu //-->
	';
	echo menu($privilege);
	echo '
	<!-- End Menu //-->

	</div>
	</td>

	        <td>
	';
}

function project_footer() {
	echo '
	        </td>
	</tr>
	</table>
	</body>
	</html>';
}

function getmenuURL($projectId="", $specimenId="", $gridId="", $gridBoxId="", $userId="") {
	$getids=array();
	if (!empty($projectId)) 
		$getids[]='pid='.$projectId;
	if (!empty($specimenId)) 
		$getids[]='sid='.$specimenId;
	if (!empty($gridId)) 
		$getids[]='gid='.$gridId;
	if (!empty($gridBoxId)) 
		$getids[]='gbid='.$gridBoxId;
	if (!empty($userId)) 
		$getids[]='uid='.$userId;
	$getids_str=implode('&',$getids);
	return "getmenu.php?".$getids_str;
}


/* CLASS */
class project {
	var $error = array (
				 "projectname_exists"=>"Project Name already exists.",
				 "projectname_empty"=>"Project Name can't be empty",
				 "short_description_empty"=>"Short Description can't be empty."
				);
				 
	function project($mysql="") {
		$this->mysql = ($mysql) ? $mysql : new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
		
		if (!$this->mysql->checkDBConnection())
			$this->mysql->dbError();
	}
	
	// This install function is for setup wizard.
	function install($defaultProjectSchema) {

		$app = new XMLApplicationImport($defaultProjectSchema);
		$sqldef = $app->getSQLDefinitionQueries();
		$fieldtypes = $app->getFieldTypes();
		if ($this->mysql->checkDBConnection())
			$this->mysql->SQLAlterTables($sqldef, $fieldtypes);
		$sqldata = $app->getSQLDataQueries();
		//--- insert data;
		foreach ((array)$sqldata as $table=>$queries) {
			foreach($queries as $query) {

					$this->mysql->SQLQuery($query,true);
			}
		}
	}

	function updateProject($projectId, $name, $short_description, $long_description, $category, $funding){

		if (!$name) 
			return $this->error['projectname_empty'];
			
		if(!$short_description)
			return $this->error['short_description_empty'];
			
		$id = $this->checkProjectExistsbyName($name);
		
		// if the project id is different than the id we searched.
		// this means there is already ahve a project with same name.

		if(($id != $projectId) && (!empty($id)))
			return $this->error['projectname_exists'];		
		
		$table='projects';
		$data['name']=$name;
		$data['short_description']=$short_description;
		$data['long_description']=$long_description;
		$data['category']=$category;
		$data['funding']=$funding;
		$where['projectId']=$projectId;

		$this->mysql->SQLUpdate($table, $data, $where);
	}

	function deleteProject($projectId) {
		if (!$projectId)
			return false;
		$q[]='DELETE FROM projectexperiments WHERE projectId='.$projectId;
		$q[]='DELETE FROM projects WHERE projectId='.$projectId;
		$this->mysql->SQLQueries($q);
	}

	/*
	 * function addProject
	 * return error message if require fields not exist
	 */
	function addProject($name, $short_description, $long_description, $category, $funding){

		if (!$name) 
			return $this->error['projectname_empty'];
			
		if(!$short_description)
			return $this->error['short_description_empty'];
			
		$id = $this->checkProjectExistsbyName($name);
		if(!empty($id))
			return $this->error['projectname_exists'];

		$table='projects';
		$data['name']=$name;
		$data['short_description']=$short_description;
		$data['long_description']=$long_description;
		$data['category']=$category;
		$data['funding']=$funding;

		$this->mysql->SQLInsert($table, $data);

	}

	function checkProjectExistsbyName($name) {
		$q=' SELECT projectId FROM projects WHERE name="'.$name.'"';
		$RprojectInfo = $this->mysql->SQLQuery($q);
		$projectInfo = mysql_fetch_array($RprojectInfo);
		return $projectInfo['projectId'];
	}

	function checkProjectExistsbyId($id) {
		$q=' SELECT projectId FROM projects WHERE projectId="'.$id.'"';
		$RprojectInfo = $this->mysql->SQLQuery($q);
		echo mysql_error();
		$projectInfo = mysql_fetch_array($RprojectInfo);
		$id = $projectInfo['projectId'];
		if(empty($id))
			return false;
		else
			return $id;
	}

	function getProjects($order="",$privilege_level=1){
		$userId = getLoginUserId();
		$q='SELECT p.projectId, p.name, p.short_description FROM projects p';
		if ($privilege_level <= 2 and $userId !== true and $userId) {
			$q .= " left join projectowners o "
						."on o.`REF|projects|project` = p.`projectId` "
						."left join ".DB_LEGINON.".UserData u "
						."on u.`DEF_id` = o.`REF|leginondata|UserData|user` "
						."WHERE u.`DEF_id` = ".$userId." ";
		}
		if ($order)
			$q .= " order by p.name ";
		return $this->mysql->getSQLResult($q);
	}

	function getProjectInfo($projectId){
		$info=array();
		$q='SELECT projectId, name as "Name", '
		  .'short_description as "Title", '
		  .'long_description as "Description", '
		  .'concat(substring_index(left(long_description, 120),"\n",2),"...") as `ReducedDescription`, '
		  .'category as "Category", '
		  .'funding as "Funding"  FROM projects '
		  .'WHERE projectId="'.$projectId.'"';

		$RprojectInfo = $this->mysql->SQLQuery($q);
		$info = mysql_fetch_array($RprojectInfo, MYSQL_ASSOC);
		return $info;
	}

	function updatePIs($ids, $projectId) {
		if (!is_array($ids)) return false;
		$q = "DELETE "
		    ."FROM pis "
		    ."WHERE projectId='".$projectId."' " ;
		$this->mysql->SQLQuery($q);
			
		foreach($ids as $id) {
			$q = "INSERT INTO pis "
			    ."(projectId, username) "
			    ."values "
			    ."($projectId, '".$id."')";
			$this->mysql->SQLQuery($q, true);

		}
		return true;
	}

	function deletePI($login, $projectId) {
		if(!$login || !$projectId) {
			return False;
		}
		$q = "DELETE "
			."FROM pis "
			."WHERE username='".$login."' "
			."and projectId='".$projectId."' " ;
		$this->mysql->SQLQuery($q);
	}

	function deleteAssociate($login, $projectId) {
		if(!$login || !$projectId) {
			return False;
		}
		$q = "DELETE "
			."FROM associates "
			."WHERE username='".$login."' "
			."and projectId='".$projectId."' " ;
		$this->mysql->SQLQuery($q);
	}

	function addPI($login, $projectId) {
		if(!$login || !$projectId)
			return False;
		$q = "SELECT projectId "
			."FROM pis "
			."WHERE username='".$login."' "
			."and projectId='".$projectId."' " ;
		$RpId = $this->mysql->SQLQuery($q);
		$n = mysql_num_rows($RpId);
		if ($n > 0)
			return False;
		$q = "INSERT INTO pis "
		    ."(projectId, username) "
		    ."values "
		    ."($projectId, '".$login."')";
		return $this->mysql->SQLQuery($q, true);
	}

	function addAssociate($login, $projectId) {
		if(!$login || !$projectId)
			return False;
		$q = "SELECT projectId "
			."FROM associates "
			."WHERE username='".$login."' "
			."and projectId='".$projectId."' " ;
		$RpId = $this->mysql->SQLQuery($q);
		$n = mysql_num_rows($RpId);
		if ($n > 0)
			return False;
		$q = "INSERT INTO associates "
		    ."(projectId, username) "
		    ."values "
		    ."($projectId, '".$login."')";
		return $this->mysql->SQLQuery($q, true);
	}

	function getPIs($projectId) {
		$q = "SELECT "
		   ."p.`username` "
		   ."FROM pis p "
		   ."WHERE p.`projectId`='".$projectId."' ";
		return $this->mysql->getSQLResult($q);
	}

	function updateAssociates($ids, $projectId) {
		if (!is_array($ids)) return false;
		$q = "DELETE "
		    ."FROM associates "
		    ."WHERE projectId='".$projectId."' " ;
		$this->mysql->SQLQuery($q);
			
		foreach($ids as $id) {
			$q = "INSERT INTO associates "
			    ."(projectId, username) "
			    ."values "
			    ."($projectId, '".$id."')";
			$this->mysql->SQLQuery($q, true);

		}
		return true;
	}

	function getAssociates($projectId) {
		$peopleIds = array();
		$q = "SELECT "
		   ."p.`username` "
		   ."FROM associates p "
		   ."WHERE p.`projectId`='".$projectId."' ";
		return $this->mysql->getSQLResult($q);
	}

	function getProjectOwners($projectId) {
		$q='SELECT concat(u.firstname," ",u.lastname) `full name`, '
			.'u.firstname as firstname, '
			.'u.lastname as lastname, '
			.'u.`DEF_id` userId '
			.'FROM projectowners o '
			.'left join '.DB_LEGINON.'.UserData u '
			.'on o.`REF|leginondata|UserData|user` = u.`DEF_id` '
			.'WHERE o.`REF|projects|project` = '.$projectId." ";
		return $this->mysql->getSQLResult($q);
	}

	function updateOwners($ids, $projectId) {
		if (!is_array($ids)) return false;
		$q = "DELETE "
		    ."FROM projectowners "
		    ."WHERE `REF|projects|project`='".$projectId."' " ;
		$this->mysql->SQLQuery($q);
			
		foreach($ids as $id) {
			$q = "INSERT INTO projectowners "
			    ."(`REF|projects|project`, `REF|leginondata|UserData|user`) "
			    ."values "
			    ."($projectId, '".$id."')";
			$this->mysql->SQLQuery($q, true);
		}
		return true;
	}

	function addProjectOwner($userId,$projectId) {
		$q = "INSERT INTO projectowners "
	    ."(`REF|projects|project`, `REF|leginondata|UserData|user`) "
	    ."values "
	    ."(".$projectId.", ".$userId.")";
		$this->mysql->SQLQuery($q, true);
		return true;
	}

	function removeProjectOwner($users,$projectId) {
		if (!is_array($users)) return false;
		foreach ($users as $userId) {
			$q = "DELETE FROM projectowners "
				."WHERE `REF|leginondata|UserData|user` = ".$userId." "
				."and `REF|projects|project`= ".$projectId." ";
			echo $q;
			#$this->mysql->SQLQuery($q, true);
		}
		return true;
	}

	function getExperiments($projectId="") {
		$experimentIds = array();
		$q = "SELECT "
		   ."projectexperimentId, name "
		   ."FROM projectexperiments p ";
		if ($projectId)
		   $q .= "WHERE p.`projectId`='".$projectId."' ";

		$experimentIds = $this->mysql->getSQLResult($q);
		return $experimentIds;
	}

}

?>
