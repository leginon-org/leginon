<?
require "inc/project.inc.php";
require "inc/leginon.inc";
require "inc/utilpj.inc.php";

$project = new project();

$projectId = ($_GET['id']) ? $_GET['id'] : $_POST['projectId'];
if (empty($projectId) || !($project->checkProjectExistsbyId($projectId))) {
	$title='- new project';
	$action='add';
} else {
	$curproject = $project->getProjectInfo($projectId);
	$title='- update project: '.$curproject['Name'];
	$action='update';
}

if ($_POST['submit']) {
	list($name, $short_description, $long_description, $category, $funding) =
		from_POST('name', 'short_description', 'long_description', 'category', 'funding');
	if ($_POST['submit']=='add')
		$projectId = $project->addProject($name, $short_description, $long_description, $category, $funding);
	else if ($_POST['submit']=='update')
		$project->updateProject($projectId, $name, $short_description, $long_description, $category, $funding);
		$location = ($_GET['ln']) ? $_GET['ln'] : "index.php";
		header("location: $location");
} 
project_header("Projects $title");
?>


<a href="<?=$_GET['ln'];?>">[ &laquo; back ]</a>
<p>
<font color=red>*</font>
<font face="Arial, Helvetica, sans-serif" size="2">: required fields</font>
<?php
include 'inc/projectform.inc.php';
project_footer();
?>
