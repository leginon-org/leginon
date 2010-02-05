<?php
require "inc/project.inc.php";
require "inc/leginon.inc";
require "inc/utilpj.inc.php";
if (privilege('projects')) {
	$title = "Projects";
	login_header($title);
} else {
	$redirect=$_SERVER['PHP_SELF'];
	redirect(BASE_URL.'login.php?ln='.$redirect);
}

$project = new project();

if ($_GET['cp']) {
	$selectedprojectId=$_GET['cp'];
}
if ($_POST['currentproject']) {
	$selectedprojectId=$_POST['currentproject'];
}
$projects = $project->getProjects("order",privilege('projects'));

if($projects) {
foreach ((array)$projects as $k=>$proj) {
	$pId = $proj['projectId'];
	$is_proj_admin = checkProjectAdminPrivilege($pId);
	if ($is_proj_admin) {
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
project_header($title);
?>
<form method="POST" name="projectform" action="<?=$_SERVER['PHP_SELF'] ?>">
<input type="hidden" name="projectId" value="">
<?
if ($is_proj_admin) {
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
