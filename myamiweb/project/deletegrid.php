<?php

require_once "inc/project.inc.php";
require_once "inc/gridbox.inc.php";
require_once "inc/grid.inc.php";
require_once "inc/util.inc";
require_once "inc/mysql.inc";

$griddata = new grid();

$gridId = $griddata->checkGridExistsbyId($_GET['gid']);

if (!$gridId) {
	header("Location: index.php");
	exit;
} else {
	$curgrid = $griddata->getGridInfo($gridId);
	$title='- delete grid: '.$curgrid['label'];
	$gridId= $_GET['gid'];
	$url = $_SERVER['PHP_SELF']."?gid=".$gridId;
}

$is_admin = checkProjectAdminPrivilege($curgrid['projectId']);
if (privilege('projects') and $is_admin) {
	$title = "Projects";
	login_header($title);
} else {
	redirect(BASE_URL.'accessdeny.php?text=You are only allowed to delete grids in projects you own.');
}

if (!$_POST) {
project_header("Grid $title");
?>
<p>
<form method="POST" name="confirm" action="<?php echo $url ?>">
<table border="0">
<tr>
<td align="center" colspan="2" >
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
	$griddata->deleteGrid($gridId);
}
	header("Location: gridtray.php");
?>
