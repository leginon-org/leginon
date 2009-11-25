<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/leginon.inc";

$defaultId= 1445;
$sessionId= ($_GET['Id']) ? $_GET['Id'] : $defaultId;
$maxrate = (is_numeric($_POST['maxr'])) ? $_POST['maxr'] 
		: (is_numeric($_GET['maxr']) ? $_GET['maxr'] : false);

if ($driftdata = $leginondata->getDriftDataFromSessionId($sessionId)) {
foreach ($driftdata as $drift) {
	$id = $drift['imageId'];
	$data[$id] = $drift;
}

foreach ($data as $drift) {
	$id = $drift['imageId'];
	$t  = $drift['time'];
}
}
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
	<?php echo divtitle("Image Shift Report $title Experiment"); ?>
	</td>
</tr>
<?php
$expId = $sessionId;
$imageshiftpresets = $leginondata->getImageShiftPresets($expId);
if (!empty($imageshiftpresets)) {
	foreach($imageshiftpresets as $preset) {
		$stats = $leginondata->getImageShift($expId,$preset['name'],True);
		if (!$stats['x']['stddev']) continue;
		echo "<tr><td colspan='3'>";
		echo divtitle("Image Shift of Image Acquire by ".$preset['name']." Preset");
		foreach (array_keys($stats) as $key) 
			printf('%s mean= %.2f stddev= %.2f </br>',$key, $stats[$key]['avg']*1e6,$stats[$key]['stddev']*1e6);
		echo "</td></tr>";
		echo "<tr>";
		echo "<td>";
		echo "<a href='imageshiftgraph.php?Id=$expId&vdata=1&preset=".$preset['name']."'>[data]</a>";
		echo "<a href='imageshiftgraph.php?Id=$expId&vs=1&preset=".$preset['name']."'>[sql]</a><br>";
		echo "<a href='imageshiftgraph.php?Id=$expId&preset=".$preset['name']."'>";
		echo "<img border='0' src='imageshiftgraph.php?Id=$expId&w=256&preset=".$preset['name']."'>";
		echo "</a>\n";
		echo "</td>\n";
		echo "<td>";
		echo "<a href='imageshiftgraph.php?Id=$expId&hg=1&haxis=x&vdata=1&preset=".$preset['name']."'>[data]</a>";
		echo "<a href='imageshiftgraph.php?Id=$expId&hg=1&haxis=x&vs=1&preset=".$preset['name']."'>[sql]</a><br>";
		echo "<a href='imageshiftgraph.php?Id=$expId&hg=1&haxis=x&preset=".$preset['name']."'>";
		echo "<img border='0' src='imageshiftgraph.php?Id=$expId&hg=1&haxis=x&w=256&preset=".$preset['name']."'>";
		echo "</a>\n";
		echo "</td>\n";
		echo "<td>";
		echo "<a href='imageshiftgraph.php?Id=$expId&hg=1&vdata=1&preset=".$preset['name']."'>[data]</a>";
		echo "<a href='imageshiftgraph.php?Id=$expId&hg=1&vs=1&preset=".$preset['name']."'>[sql]</a><br>";
		echo "<a href='imageshiftgraph.php?Id=$expId&hg=1&preset=".$preset['name']."'>";
		echo "<img border='0' src='imageshiftgraph.php?Id=$expId&hg=1&w=256&preset=".$preset['name']."'>";
		echo "</a>\n";
		echo "</td>\n";
		echo "</tr>\n";
	}
} else echo "no Image Shift information available";
	echo "</td>";
?>
</tr>
</table>
</body>
</html>
