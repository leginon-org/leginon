<?php
require("inc/project.inc.php");
require("inc/user.inc.php");

if ($_GET[cp])
	$selectedprojectId=$_GET[cp];
if ($_POST[currentproject])
	$selectedprojectId=$_POST[currentproject];
$project = new project();
$user = new user();
$projects = $project->getProjects("order");
$selectedprojectId = empty($selectedprojectId) ? $projects[0][projectId] : $selectedprojectId;
project_header("Projects", $selectedprojectId, $selectedspecimenId, $selectedgridId, $selectedgridboxId);
$enableimage=($_POST['enableimage']) ? true : false;
?>
<br>
<p>
<script>
	function onChangeProject(){
		var cId = document.projectform.currentproject.options[document.projectform.currentproject.selectedIndex].value;
		window.document.projectform.projectId.value=cId;
		var projif = document.getElementById('projectframeId');
		projif.src="getproject.php?projId="+cId;
		var menuif = document.getElementById('menuframeId');
		menuif.src="getmenu.php?pid="+cId;
	}

	function showprojectmanager() {
		var cId = document.projectform.currentproject.options[document.projectform.currentproject.selectedIndex].value;
		var URL = "projectmanager.php?cp="+cId;
		var managerwindow =window.open(URL, 'managerwindow', 'left=10,top=400,height=200,width=190,toolbar=0,scrollbars=0,location=0,statusbar=0,menubar=0,resizable=1,alwaysRaised=yes');
		managerwindow.focus();
	}

</script>
<form method="POST" name="projectform" action="<?php echo $PHP_SELF ?>">
<input type="hidden" name="projectId" value="">
<input type="submit" name="enableimage" value=" enable image count ">
<table border="0" height="600">
<tr>
<td valign=top >
<table border=0>
<tr><th>Projects Status</th><th>Nb Experiments</th>
<?
if ($enableimage) {
	echo "<th>Nb Images</th>";
}
echo "</tr>";
$tot_exp=0;
$excludedprojectIds = explode(',',EXCLUDED_PROJECTS);
$tot_exp_exclusif=0;
$tot_exp_img_exclusif=0;
foreach ($projects as $p) {
	$experimentIds = $project->getExperiments($p[projectId]);
	if ($enableimage) {
		$tot_images = 0;
		foreach($experimentIds as $name) {
			$expinfo = $project->getExperimentInfo($name);
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
Total Projects: <b><?=count($projects)?></b> Total Exp: <b><?=$tot_exp?></b>
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
Excluded projects: <?=implode(', ',$excludedprojects);?><br>
Total Projects: <b><?=(count($projects)-count($excludedprojectIds))?></b> Total Exp: <b><?=$tot_exp_exclusif?></b>
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
<?
project_footer();
?>
