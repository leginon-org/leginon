<?php
require "inc/project.inc.php";
require "inc/leginon.inc";
require "inc/utilpj.inc.php";

$privilege = privilege();
if ($privilege == 2 ) {
	$title = "project administration";
	login_header($title);
} else {
	if ($privilege == 1) {
		$title = "project summary";
		login_header($title);
	} else {
		$redirect=$_SERVER['PHP_SELF'];
		redirect(BASE_URL.'login.php?ln='.$redirect);
	}
}

$project = new project();

$filename="defaultprojecttables20081002.xml";
$app = new XMLApplicationImport($filename);
$sqldef = $app->getSQLDefinitionQueries();
$fieldtypes = $app->getFieldTypes();
$sqldata = $app->getSQLDataQueries();
$fieldvalues = $app->getFieldValues();
$changes=$project->mysql->SQLAlterTables($sqldef, $fieldtypes);
if (is_array($sqldata)) {
	foreach ($sqldata as $table=>$queries) {
		foreach($queries as $query) {
				$project->mysql->SQLQuery($query,true);
		}
	}
}


if ($_GET['cp']) {
	$selectedprojectId=$_GET['cp'];
}
if ($_POST['currentproject']) {
	$selectedprojectId=$_POST['currentproject'];
}

$projects = $project->getProjects("order");
$is_admin = ($privilege == 2);

if($projects) {
foreach ((array)$projects as $k=>$proj) {
	$pId = $proj['projectId'];
	if ($is_admin) {
		$projects[$k]['edit']="<a href='updateproject.php?id=$pId'><img alt='edit' border='0' src='img/edit.png'></a>";
		$projects[$k]['del']="<a href='deleteproject.php?id=$pId'><img alt='delete' border='0' src='img/del.png'></a>";
	}
	$experimentIds = $project->getExperiments($pId);
	if (is_array($experimentIds)) {
		$nb=count($experimentIds);
		$last=current($experimentIds);
	}
	$info = $leginondata->getSessionInfo($last);
	$expId = $info['SessionId'];
	$last_str =  ($last) ? "last: <a class='header' href='".SUMMARY_URL.$expId."'>".$last['name']."</a>" : "";
	$exp_str = "experiment";
	if ($nb>1)
		$exp_str .="s";
	$projects[$k]['institution']=$info['institution'];
	$projects[$k]['experiment']=$nb." ".$exp_str."<br>".$last_str;
	$projects[$k]['name']="<a href='getproject.php?pId=$pId'>".$proj['name']."</a>";
	
}
}
project_header("Projects");
?>
<form method="POST" name="projectform" action="<?=$_SERVER['PHP_SELF'] ?>">
<input type="hidden" name="projectId" value="">
<?
if ($is_admin) {
	echo "<a class='header' href='updateproject.php'>Add a new project</a>";
	$columns=array('edit'=>'','del'=>'');
} else {
	$columns = array();
}
$columns=array_merge($columns, array(
	'name'=>'Name',
	'short_description'=>'Description',
	'experiment'=>'Experiment'));
$display_header=false;

if($projects)
	echo data2table($projects, $columns, $display_header);
?>
</form>
<?php
project_footer();
?>
