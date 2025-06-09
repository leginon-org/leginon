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
<title><?php echo $title; ?> drift report</title>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
</head>

<body>
<table border=0 cellpadding=10>
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
	<td colspan="3">
	<?php echo divtitle("Laser Phase Plate Report $title Experiment"); ?>
	</td>
</tr>
<?php
$expId = $sessionId;
$xtiltpresets = $leginondata->getImageShiftPresets($expId);
if (!empty($xtiltpresets)) {
	foreach($xtiltpresets as $preset) {
		$stats = $leginondata->getImageScopeXYValues($expId,$preset['name'],'phase plate plane shift',True);
		if (!$stats['x']['stddev']) continue;
		echo "<tr><td colspan='3'>";
		echo divtitle("Phase Plate Plane Shift (Xtilt) of Image Acquire by Preset ".$preset['name']);
		echo "</td></tr>";
		echo "<tr><td colspan='3'>";
		$allxlink = "<a href='lppdata.php?Id=$expId&preset=".$preset['name']."&vdata=1'>";
		$allxlink .= "[all lpp-related scope data for preset ".$preset['name']."]</a>\n";
		echo $allxlink ;
		echo "<br>";
		foreach (array_keys($stats) as $key) 
			printf('%s mean= %.2f stddev= %.2f </br>',$key, $stats[$key]['avg']*1e6,$stats[$key]['stddev']*1e6);
		echo "</td></tr><td>";
		echo "<a href='xtiltgraph.php?Id=$expId&vdata=1&preset=".$preset['name']."'>[data]</a>";
		echo "<a href='xtiltgraph.php?Id=$expId&vs=1&preset=".$preset['name']."'>[sql]</a>";
		echo "<br>";
		echo "<a href='xtiltgraph.php?Id=$expId&preset=".$preset['name']."'>";
		echo "<img border='0' src='xtiltgraph.php?Id=$expId&w=256&preset=".$preset['name']."'>";
		echo "</a>\n";
		echo "</td>";
		echo "<td>";
		echo "<a href='xtiltgraph.php?Id=$expId&hg=1&haxis=x&vdata=1&preset=".$preset['name']."'>[data]</a>";
		echo "<a href='xtiltgraph.php?Id=$expId&hg=1&haxis=x&vs=1&preset=".$preset['name']."'>[sql]</a><br>";
		echo "<a href='xtiltgraph.php?Id=$expId&hg=1&haxis=x&preset=".$preset['name']."'>";
		echo "<img border='0' src='xtiltgraph.php?Id=$expId&hg=1&haxis=x&w=256&preset=".$preset['name']."'>";
		echo "</a>\n";
		echo "</td>\n";
	}
} else echo "no Laser Phase Plate information available";
	echo "</td>";
?>
</tr>
</table>
</body>
</html>
