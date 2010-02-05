<?php
require "config.php";
require "inc/login.inc";
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
	$link->addlink(BASE_URL, 'dbem tool','', '', '');
	$link->addlink('project.php','View Projects','', 'folder', '');
	$link->addlink('gridtray.php','Grid Tray','', 'preparation', '');
	if ($privilege>=3) {
		$link->addlink('user.php','View Users','', 'user', '');
	}
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


class project {

	function project($mysql="") {
		$this->mysql = ($mysql) ? $mysql : new mysql(DB_HOST, DB_USER, DB_PASS, DB_PROJECT);
		if ($this->mysql->checkDBConnection()) {
			$this->install();
		} else {
			$this->mysql->dbError();
		}
	}

	function install() {
		$q='select value '
				.'from install '
				.'where `key`="settable" ';
		list($r)=$this->mysql->getSQLResult($q);
		if ($r['value']==1) {
			return;
		}

		$app = new XMLApplicationImport(DEF_PROJECT_TABLES_FILE);
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

		$table='install';
		$data['key']='settable';
		$data['value']=1;
		$this->mysql->SQLInsert($table, $data);


	}


	function project_tables() {
			$table="projectexperiments";
			$sql='CREATE TABLE `'.$table.'` ('
			.'`projectexperimentId` int(11) NOT NULL auto_increment,'
			.'`projectId` int(11) NOT NULL default "0",'
			.'`name` varchar(100) NOT NULL default "0",'
			.'`experimentsourceId` int(11) NOT NULL default "0",'
			.'PRIMARY KEY  (`projectexperimentId`),'
			.'KEY `projectId` (`projectId`),'
			.'KEY `name` (`name`)'
			.');';
			$tables[$table]=$sql;
			$table="projects";
			$sql='CREATE TABLE `'.$table.'` ('
			.'`projectId` int(11) NOT NULL auto_increment,'
			.'`timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,'
			.'`name` text NOT NULL,'
			.'`short_description` text NOT NULL,'
			.'`long_description` text NOT NULL,'
			.'`category` text NOT NULL,'
			.'`funding` text NOT NULL,'
			.'PRIMARY KEY  (`projectId`)'
			.')';
			$tables[$table]=$sql;
			$table="boxtypes";
			$sql='CREATE TABLE IF NOT EXISTS `'.$table.'` ('
			.'`boxtypeId` int(11) NOT NULL auto_increment,'
			.'`label` text NOT NULL,'
			.'`image` varchar(100) NOT NULL default "",'
			.'`image_tiny` varchar(100) NOT NULL default "",'
			.'PRIMARY KEY  (`boxtypeId`)'
			.'); ';
			$sqldata='INSERT INTO `boxtypes` (`boxtypeId`, `label`, `image`, `image_tiny`) '
			.'VALUES '
			.'(1, "cryo grid box", "grid_box_cryo.jpg", "grid_box_cryo_tiny.jpg"),'
			.'(2, "grid box", "grid_box.jpg", "grid_box_tiny.jpg"),'
			.'(3, "tray", "tray.png", "tray_tiny.png")';
			$tables[$table]=$sql;
			$table="gridboxes";
			$sql='CREATE TABLE IF NOT EXISTS `'.$table.'` ('
			.'`gridboxId` int(11) NOT NULL auto_increment,'
			.'`timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,'
			.'`label` text NOT NULL,'
			.'`boxtypeId` int(11) NULL,'
			.'PRIMARY KEY  (`gridboxId`)'
			.')';
			$tables[$table]=$sql;
			$table="gridlocations";
			$sql='CREATE TABLE IF NOT EXISTS `'.$table.'` ('
			.'`gridlocationId` int(11) NOT NULL auto_increment,'
			.'`gridboxId` int(11) NULL,'
			.'`gridId` int(11) NULL,'
			.'`location` int(11) NOT NULL default "0",'
			.'PRIMARY KEY  (`gridlocationId`)'
			.')';
			$tables[$table]=$sql;
			$table="grids";
			$sql='CREATE TABLE IF NOT EXISTS `'.$table.'` ('
			.'`gridId` int(11) NOT NULL auto_increment,'
			.'`timestamp` timestamp NOT NULL default CURRENT_TIMESTAMP on update CURRENT_TIMESTAMP,'
			.'`label` text NOT NULL,'
			.'`specimenId` int(11) NULL,'
			.'`number` varchar(10) NOT NULL default "0",'
			.'`boxId` int(11) NULL,'
			.'PRIMARY KEY  (`gridId`)'
			.')';
			$tables[$table]=$sql;

			foreach($tables as $table=>$sql) {
			if (!$this->mysql->SQLTableExists($table)) 
				$this->mysql->SQLquery($sql);
				echo $this->mysql->getError();
			}
	}

	function updateProject($projectId, $name, $short_description, $long_description, $category, $funding){

		if (!$this->checkProjectExistsbyId($projectId)) 
			return false;

		$table='projects';
		$data['name']=$name;
		$data['short_description']=$short_description;
		$data['long_description']=$long_description;
		$data['category']=$category;
		$data['funding']=$funding;
		$where['projectId']=$projectId;

		$s = $this->mysql->SQLUpdate($table, $data, $where);
	}

	function deleteProject($projectId) {
		if (!$projectId)
			return false;
		$q[]='delete from projectexperiments where projectId='.$projectId;
		$q[]='delete from projects where projectId='.$projectId;
		$this->mysql->SQLQueries($q);
	}

	function addProject($name, $short_description, $long_description, $category, $funding){

		if (!$name) return 0;

		$table='projects';
		$data['name']=$name;
		$data['short_description']=$short_description;
		$data['long_description']=$long_description;
		$data['category']=$category;
		$data['funding']=$funding;

		$re=$this->checkProjectExistsbyName($name);
		if (empty($re)) {
			$id =  $this->mysql->SQLInsert($table, $data);
			return $id;
		}
	}

	function getLastId() {
		$q='select projectId from projects order by projectId DESC limit 1';
		$RprojectInfo = $this->mysql->SQLQuery($q);
		$projectInfo = mysql_fetch_array($RprojectInfo);
		if (!$lastId=$projectInfo[projectId])
			$lastId=0;
		return $lastId;
	}

	function checkProjectExistsbyName($name) {
		$q=' select projectId from projects where name="'.$name.'"';
		$RprojectInfo = $this->mysql->SQLQuery($q);
		$projectInfo = mysql_fetch_array($RprojectInfo);
		return $projectInfo[projectId];
	}

	function checkProjectExistsbyId($id) {
		$q=' select projectId from projects where projectId="'.$id.'"';
		$RprojectInfo = $this->mysql->SQLQuery($q);
		echo mysql_error();
		$projectInfo = mysql_fetch_array($RprojectInfo);
		$id = $projectInfo[projectId];
		if(empty($id))
			return false;
		else
			return $id;
	}

	function getProjectId($name){
		$q='select projectId from projects where name="'.$name.'"';
	}

	function getProjects($order="",$privilege_level=1){
		$userId = getLoginUserId();
		$q='select p.projectId, p.name, p.short_description from projects p';
		if ($privilege_level <= 2 and $userId)
			$q .= " left join projectowners o "
						."on o.`REF|projects|project` = p.`projectId` "
						."left join ".DB_LEGINON.".UserData u "
						."on u.`DEF_id` = o.`REF|leginondata|UserData|user` "
						."where u.`DEF_id` = ".$userId." ";
		if ($order)
			$q .= " order by p.name ";
		return $this->mysql->getSQLResult($q);
	}

	function getProjectInfo($projectId){
		$info=array();
		$q='select projectId, name as "Name", '
		  .'short_description as "Title", '
		  .'long_description as "Description", '
		  .'concat(substring_index(left(long_description, 120),"\n",2),"...") as `ReducedDescription`, '
		  .'category as "Category", '
		  .'funding as "Funding"  from projects '
		  .'where projectId="'.$projectId.'"';

		$RprojectInfo = $this->mysql->SQLQuery($q);
		$info = mysql_fetch_array($RprojectInfo, MYSQL_ASSOC);
		return $info;
	}

	function updatePIs($ids, $projectId) {
		if (!is_array($ids)) return false;
		$q = "delete "
		    ."from pis "
		    ."where projectId='".$projectId."' " ;
		$this->mysql->SQLQuery($q);
			
		foreach($ids as $id) {
			$q = "insert into pis "
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
		$q = "delete "
			."from pis "
			."where username='".$login."' "
			."and projectId='".$projectId."' " ;
		$this->mysql->SQLQuery($q);
	}

	function deleteAssociate($login, $projectId) {
		if(!$login || !$projectId) {
			return False;
		}
		$q = "delete "
			."from associates "
			."where username='".$login."' "
			."and projectId='".$projectId."' " ;
		$this->mysql->SQLQuery($q);
	}

	function addPI($login, $projectId) {
		if(!$login || !$projectId)
			return False;
		$q = "select projectId "
			."from pis "
			."where username='".$login."' "
			."and projectId='".$projectId."' " ;
		$RpId = $this->mysql->SQLQuery($q);
		$n = mysql_num_rows($RpId);
		if ($n > 0)
			return False;
		$q = "insert into pis "
		    ."(projectId, username) "
		    ."values "
		    ."($projectId, '".$login."')";
		return $this->mysql->SQLQuery($q, true);
	}

	function addAssociate($login, $projectId) {
		if(!$login || !$projectId)
			return False;
		$q = "select projectId "
			."from associates "
			."where username='".$login."' "
			."and projectId='".$projectId."' " ;
		$RpId = $this->mysql->SQLQuery($q);
		$n = mysql_num_rows($RpId);
		if ($n > 0)
			return False;
		$q = "insert into associates "
		    ."(projectId, username) "
		    ."values "
		    ."($projectId, '".$login."')";
		return $this->mysql->SQLQuery($q, true);
	}

	function getPIs($projectId) {
		$q = "select "
		   ."p.`username` "
		   ."from pis p "
		   ."where p.`projectId`='".$projectId."' ";
		return $this->mysql->getSQLResult($q);
	}

	function updateAssociates($ids, $projectId) {
		if (!is_array($ids)) return false;
		$q = "delete "
		    ."from associates "
		    ."where projectId='".$projectId."' " ;
		$this->mysql->SQLQuery($q);
			
		foreach($ids as $id) {
			$q = "insert into associates "
			    ."(projectId, username) "
			    ."values "
			    ."($projectId, '".$id."')";
			$this->mysql->SQLQuery($q, true);

		}
		return true;
	}

	function getAssociates($projectId) {
		$peopleIds = array();
		$q = "select "
		   ."p.`username` "
		   ."from associates p "
		   ."where p.`projectId`='".$projectId."' ";
		return $this->mysql->getSQLResult($q);
	}

	function updateExperiments($ids, $projectId) {
		if (!is_array($ids)) return false;
		$q = "delete "
		    ."from projectexperiments "
		    ."where projectId='".$projectId."' " ;
		$this->mysql->SQLQuery($q);
			
		foreach($ids as $id) {
			$q = "insert into projectexperiments "
			    ."(projectId, name) "
			    ."values "
			    ."($projectId, '".$id."')";
			$this->mysql->SQLQuery($q, true);

		}
		return true;
	}

	function getExperiments($projectId="") {
		$experimentIds = array();
		$q = "select "
		   ."name "
		   ."from projectexperiments p ";
		if ($projectId)
		   $q .= "where p.`projectId`='".$projectId."' ";
		$experimentIds = $this->mysql->getSQLResult($q);
		return $experimentIds;
	}


}

?>
