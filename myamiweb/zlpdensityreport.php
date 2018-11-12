<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/leginon.inc";
require_once "inc/project.inc";

$defaultId= 1;
$sessionId= ($_GET['Id']) ? $_GET['Id'] : $defaultId;
$maxrate = (is_numeric($_POST['maxr'])) ? $_POST['maxr'] 
		: (is_numeric($_GET['maxr']) ? $_GET['maxr'] : false);

//Block unauthorized user
checkExptAccessPrivilege($sessionId,'data');

// --- Set  experimentId
// $lastId = $leginondata->getLastSessionId();
// $sessionId = (empty($_GET[Id])) ? $lastId : $_GET[sessionId];
$sessioninfo = $leginondata->getSessionInfo($sessionId);
$title = $sessioninfo['Name'];

?>
<html>
<head>
<title><?php echo $title; ?> ice thickness report</title>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
</head>

<body>
<table border="0" cellpadding=10>
<tr>
 <td>
  <a class="header" HREF="index.php">&lt;index&gt;</a>
 </td>
 <td>
  <a class="header" HREF="3wviewer.php?sessionId=<?php echo $sessionId; ?>">&lt;view <?php echo $title; ?>&gt;</a>
 </td>
</tr>
</table>
<table border="0" cellpadding=10>
<tr valign="top">
	<td colspan="2">
	<?php echo divtitle("Density Report $title Experiment"); ?>
	</td>
</tr>
<?php
echo "<tr>";
echo "<td colspan='2'>";
echo divtitle("ZLP Ice Thickness");
echo "<br>";
$icethicknesspresets = $leginondata->getIceThicknessPresets($sessionId);
if (!empty($icethicknesspresets)) {
	echo "<tr>";
	echo "<td colspan='2'>";
	echo "<table border='0'>\n";
	echo "<tr>";
		echo "<td>";
		echo "<a href='zlp_icegraph.php?Id=$sessionId&vdata=1'>[data]</a>";
		echo "<a href='zlp_icegraph.php?Id=$sessionId&vs=1'>[sql]</a><br>";
		echo "<img border='0' src='zlp_icegraph.php?Id=$sessionId'>";
		echo "</td>\n";
	echo "</tr>\n";
	echo "</table>\n";
	echo "</td>";
	echo "</tr>";
}
$presets = $leginondata->getDataTypes($sessionId);
?>
</tr>
<tr>
<td>
<?php echo divtitle("Image Statistics"); ?>
</td>
</tr>
<?php
foreach ($presets as $preset) {
if (!$leginondata->getRelatedStats($sessionId, $preset))
	continue;
?>
<tr>
<td>
<a href="statsgraph.php?vdata=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[data]</a>
<a href="statsgraph.php?vs=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[sql]</a><br>
<img src="statsgraph.php?Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">
</td>
</tr>
<?php } ?>
</table>
</td>
</tr>
</table>
</body>
</html>
