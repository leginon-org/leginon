<?php
require_once("inc/project.inc.php");
require_once("inc/getleginondata.php");

if (privilege('projects')) {
	$title = "Projects";
	login_header($title);
} else {
	redirect(BASE_URL.'accessdeny.php');
}

$selectedprojectId = null;
if (array_key_exists('cp',$_GET) && $_GET['cp']) {
	$selectedprojectId=$_GET[cp];
}
if (array_key_exists('currentproject',$_POST) && $_POST['currentproject']) {
	$selectedprojectId=$_POST[currentproject];
}
$project = new project();
$projects = $project->getProjects("order",privilege('projects'));
$selectedprojectId = empty($selectedprojectId) ? $projects[0]['projectId'] : $selectedprojectId;
//START TO REMOVE:deprecated
$selectedspecimenId=null;
$selectedgridId=null;
$selectedgridboxId=null;
//END TO REMOVE:deprecated
project_header("Projects", $selectedprojectId,$selectedspecimenId, $selectedgridId, $selectedgridboxId);
$enableimage=(array_key_exists('enableimage',$_POST) && $_POST['enableimage']) ? true : false;
?>
<br>
<p>
<form method="POST" name="projectform" action="<?php echo $_SERVER['PHP_SELF'] ?>">
<input type="hidden" name="projectId" value="">
<input type="submit" name="enableimage" value=" enable image count ">
<table border="0" height="600">
<tr>
<td valign=top >
<table border=0>
<tr><th>Projects Status</th><th>Nb Experiments</th>
<?php
if ($enableimage) {
	echo "<th>Nb Images</th>";
}
echo "</tr>";
$tot_exp=0;
$tot_exp_img=0;
$excludedprojectIds = explode(',',EXCLUDED_PROJECTS);
$excludedprojects = array();
$tot_exp_exclusif=0;
$tot_exp_img_exclusif=0;
foreach ($projects as $p) {
	$experimentIds = $project->getExperiments($p['projectId']);
    $tot_images = 0;
	if ($enableimage) {
		foreach($experimentIds as $name) {
			//getExperimentInfo is in inc/getleginondata.inc
			$expinfo = getExperimentInfo($name);
			$tot_images += $expinfo['Total images'];
		}
	}
	$nbexp = count($experimentIds);
	$tot_exp += $nbexp;
	$tot_exp_img += $tot_images;
	if (!in_array($p['projectId'], $excludedprojectIds)) {
		$tot_exp_exclusif += $nbexp;
		$tot_exp_img_exclusif += $tot_images;
	} else {
		$excludedprojects[]=$p['name'];
	}
	echo "<tr><td>".$p['name']."</a></td><td>".$nbexp."</td>";
	if ($enableimage) {
		echo "<td>".$tot_images."</td>";
	}
	echo "</tr>\n";
}
?>
</table>
<br>
Total Projects: <b><?php echo count($projects); ?></b> Total Exp: <b><?php echo $tot_exp; ?></b>
<?php
if ($enableimage) {
	echo "Total Images: <b>$tot_exp_img</b>";
}
?>
<br>
<?php
if (count($excludedprojects)) {
?>
<p>
Excluded projects: <?php echo implode(', ',$excludedprojects); ?><br>
Total Projects: <b><?php echo count($projects)-count($excludedprojectIds); ?></b> Total Exp: <b><?php echo $tot_exp_exclusif; ?></b>
<?php
}
if ($enableimage) {
	echo "Total Images: <b>$tot_exp_img_exclusif</b>";
}
?>
</p>
</td>
</tr>
</table>
</form>
<?php
project_footer();
?>
