<?php
require_once "inc/project.inc.php";
require_once "inc/user.inc.php";
require_once "inc/leginon.inc";
require_once "inc/utilpj.inc.php";
if (privilege('projects')) {
	$title = "Projects";
	login_header($title);
} else {
	$redirect=$_SERVER['PHP_SELF'];
	redirect(BASE_URL.'login.php?ln='.$redirect);
}

$project = new project();
$userdata = new user();

if ($_GET['cp']) {
	$selectedprojectId=$_GET['cp'];
}
if ($_POST['currentproject']) {
	$selectedprojectId=$_POST['currentproject'];
}
$projects = $project->getProjects("order",privilege('projects'));

if($projects) {
foreach ((array)$projects as $k=>$proj) {
	$projectId = $proj['projectId'];
	$is_proj_admin = checkProjectAdminPrivilege($projectId);
	if ($is_proj_admin) {
		$projects[$k]['edit']="<a href='updateproject.php?projectId=$projectId'><img alt='edit' border='0' src='img/edit.png'></a>";
		$projects[$k]['del']="<a href='deleteproject.php?projectId=$projectId'><img alt='delete' border='0' src='img/del.png'></a>";
		$projectowners = $project->getProjectOwners($projectId);
		if (count($projectowners)) {
			$projects[$k]['owner']=$projectowners[0]['full name'];
			$ownerdetails = $userdata->getUserInfo($projectowners[0]['userId']);
			$projects[$k]['institution']=(is_array($ownerdetails)) ? $ownerdetails['institution']:'';
		}
	}
	$experimentIds = $project->getExperiments($projectId);
	if (is_array($experimentIds)) {
		$nb=count($experimentIds);
		$last=current($experimentIds);
	}
	$info = $leginondata->getSessionInfo($last['leginonId']);
	$expId = $info['SessionId'];
	$last_str =  ($last) ? "last: <a class='header' href='".SUMMARY_URL.$expId."'>".$last['name']."</a>" : "";
	$exp_str = "experiment";
	if ($nb>1)
		$exp_str .="s";
	$projects[$k]['experiment']=$nb." ".$exp_str."<br>".$last_str;
	$projects[$k]['name']="<a href='getproject.php?projectId=$projectId'>".$proj['name']."</a>";
	
}
}
project_header($title);
?>
<form method="POST" name="projectform" action="<?=$_SERVER['PHP_SELF'] ?>">
<input type="hidden" name="projectId" value="">
<?
if (privilege('projects') > 3) {
	echo "<a class='header' href='updateproject.php'>Add a new project</a>";
	$columns=array('edit'=>'');
} else {
	$columns = array();
}
$columns=array_merge($columns, array(
	'name'=>'Name'));
if ($is_proj_admin) {
	$columns=array_merge($columns, array(
		'owner'=>'Owner',
		'institution'=>'Institution'));
}
$columns=array_merge($columns, array(
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
