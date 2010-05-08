<?php

require_once "inc/project.inc.php";

if (privilege('gridboxes')>2) {
	$title = "Grid boxes";
	login_header($title);
} else {
	redirect(BASE_URL.'accessdeny.php?text=Only Superusers and Administrators can delete gridboxes.');
}

require_once "inc/gridbox.inc.php";
require_once "inc/grid.inc.php";
require_once "inc/util.inc";
require_once "inc/mysql.inc";

$gridboxdata = new gridbox();

$gridboxId = $gridboxdata->checkGridBoxExistsbyId($_GET['gridboxId']);
if (!$gridboxId) {
	header("Location: gridtray.php");
	exit;
} else {
	$curgridbox = $gridboxdata->getGridBoxInfo($gridboxId);
	$title='- delete : '.$curgridbox['label'];
	$url = $_SERVER['PHP_SELF']."?gridboxId=".$gridboxId;
}

if (!$_POST) {
project_header("Grid Box $title");

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

<?php
project_footer(); 
exit;
} else if ($_POST['yes']) {
	$gridboxdata->deleteGridBox($gridboxId);
}
header("Location: gridtray.php");
?>
