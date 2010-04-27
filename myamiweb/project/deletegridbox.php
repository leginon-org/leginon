<?php

require "inc/project.inc.php";
require "inc/gridbox.inc.php";
require "inc/grid.inc.php";
require "inc/util.inc";
require "inc/mysql.inc";

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
