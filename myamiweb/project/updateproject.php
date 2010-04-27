<?
require "inc/project.inc.php";
require "inc/leginon.inc";
require "inc/utilpj.inc.php";

$project = new project();

$projectId = ($_GET['projectId']) ? $_GET['projectId'] : $_POST['projectId'];
if (empty($projectId) || !($project->checkProjectExistsbyId($projectId))) {
	$title='- new project';
	$action='add';
} else {
	$curproject = $project->getProjectInfo($projectId);

	$name = $curproject['Name'];
	$category = $curproject['Category'];
	$funding = $curproject['Funding'];
	$short_description = $curproject['Title'];
	$long_description = $curproject['Description'];
	
	$title='- update project: '.$name;
	$action='update';
}

if ($_POST['submit']) {
	foreach($_POST as $k=>$v){
			$v = trim($v);
			$$k = addslashes($v);
	}		
		
	if ($_POST['submit']=='add')
		$result = $project->addProject($name, $short_description, $long_description, $category, $funding);
	else if ($_POST['submit']=='update')
		$result = $project->updateProject($projectId, $name, $short_description, $long_description, $category, $funding);
		$location = ($_GET['ln']) ? $_GET['ln'] : "index.php";

} 
project_header("Projects $title");
?>

<a href="<?=$_GET['ln'];?>">[ &laquo; back ]</a>

<p>

<?php 
if ($_POST['submit']) {
	if (!empty($result)) {
		echo '<p><font face="Arial, Helvetica, sans-serif" size="4" color="#FF2200">'.$result.'</font></p>';
	}
	else{
		echo '<p><font face="Arial, Helvetica, sans-serif" size="4" color="#FF2200">Your update has been submitted.</font></p>';
	}
}
?>

<font color=red>*</font>
<font face="Arial, Helvetica, sans-serif" size="2">: required fields</font>

<?php 
include 'inc/projectform.inc.php';
project_footer();
?>
