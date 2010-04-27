<?php

require "inc/project.inc.php";
require "inc/mysql.inc";
require "inc/util.inc";


$project = new project();

$projectId = $project->checkProjectExistsbyId($_GET['projectId']);
if (!$projectId) {
	header("Location: index.php");
	exit;
} else {
	$curproject = $project->getProjectInfo($projectId);
	$title='- delete project: '.$curproject['Name'];
	$projectId= $_GET['projectId'];
	$url = $_SERVER['PHP_SELF']."?projectId=".$projectId;
}

if (!$_POST) {
project_header("Project $title");

?>
<p>
<form method="POST" name="confirm" action="<?php echo $url ?>">
<table border=0 >
<tr>
<td align=center colspan=2 >
<h3>Are you sure ? </h3>
</td>
</tr>
<tr>
<td>
<input type="submit" name="yes" value = " Yes " >
</td>
<td>
<input type="submit" name="no" value = " No " >
<td>
</tr>
	
</table>
</form>

<?
project_footer(); 
exit;
} else if ($_POST['yes']) {
	$project->deleteProject($projectId);
}
	header("Location: index.php");
?>
