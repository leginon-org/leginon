<?php
require "inc/project.inc.php";
require "inc/leginon.inc";
require "inc/gridbox.inc.php";
require "inc/grid.inc.php";

$grid = new grid();
$gridboxdata = new gridbox();

$gridId = ($_GET['gid']) ? $_GET['gid'] : $_POST['gridId'];
$boxId = ($_GET['gbid']) ? $_GET['gbid'] : $_POST['currentgridbox'];

if ($_POST) {
	$boxId = $_POST['currentgridbox'];
	$projectId = $_POST['projectId'];
	$label = $_POST['label'];
	$f_prepdate = $_POST['prepdate'];
	$specimen = $_POST['specimen'];
	$preparation = $_POST['preparation'];
	$number = $_POST['number'];
	$note = $_POST['note'];
	if ($_POST['submitgrid']=='add') {
		$gridId = $grid->addGrid($boxId, $projectId, $label, $f_prepdate, $specimen, $preparation, $number, $note);
	} else if ($_POST['submitgrid']=='update') {
		$grid->updateGrid($gridId, $boxId, $projectId, $label, $f_prepdate, $specimen, $preparation, $number, $note);
	}
} 

if ($boxId && $gridId) {
// --- check if current grid already stored
		$currentgridinfo = $grid->checkGridStored($gridId);
		if ($currentgridinfo) {
			$grid->deleteGridBoxLocation($gridId);
		}
// --- update the new gridbox
		$grid->updateGridbox($gridId, $boxId);
}
	$curgrid = $grid->getGridInfo($gridId);
	$projectId= $curgrid['projectId'];
	$f_prepdate = $curgrid['prepdate'];
	$substrate = $curgrid['substrate'];
	$preparation = $curgrid['preparation'];
	$number = $curgrid['number'];
	$note = $curgrid['note'];
	$boxId = $curgrid['boxId'];
	$projectId = $curgrid['projectId'];
	$label = $curgrid['label'];


if (empty($gridId) || !($grid->checkGridExistsbyName($label, $projectId))) {
	$title='- new grid';
	$action='add';
	$f_prepdate=date("n/j/Y");
} else {
	$title ='- update grid: '.$label;
	$action='update';
}
$projectdata=new project();
$projects=$projectdata->getProjects();

project_header("Projects $title");
?>
<script type="text/javascript">
	function onChangeGridBoxType(){
		document.gform.submit();
	}
</script>

<a href="javascript:history.back()">&laquo; back</a>
<p>
<?php
if ($projects) {
echo '
<font color=red>*</font>
<font face="Arial, Helvetica, sans-serif" size="2">: required fields</font>
';
	include('inc/gridform.inc');
} else {
	echo '<a href="updateproject.php">Create project first</a>';
}
project_footer();
?>
