<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require ("inc/leginon.inc");

$defaultId= 1445;
$sessionId= ($_GET[Id]) ? $_GET[Id] : $defaultId;
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
$title = $sessioninfo[Name];

?>
<html>
<head>
<title><?=$title?> ice thickness report</title>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
</head>

<body>
<table border="0" cellpadding=10>
<tr>
 <td>
  <A class="header" HREF="index.php">&lt;index&gt;</A>
 </td>
 <td>
  <A class="header" HREF="3wviewer.php?sessionId=<?=$sessionId?>">&lt;view <?=$title?>&gt;</A>
 </td>
</tr>
</table>
<table border="0" cellpadding=10>
<tr valign="top">
	<td colspan="2">
	<?= divtitle("Density Report $title Experiment"); ?>
	</td>
</tr>
<?
echo "<tr>";
echo "<td colspan='2'>";
echo divtitle("Ice Thickness");
echo "<br>";
$icethicknesspresets = $leginondata->getIceThicknessPresets($sessionId);
if (!empty($icethicknesspresets)) {
	echo "<tr>";
	echo "<td colspan='2'>";
	echo "<table border='0'>\n";
	foreach($icethicknesspresets as $preset) {
	echo "<tr>";
		echo "<td>";
		echo "<a href='icegraph.php?Id=$sessionId&vdata=1&preset=".$preset['name']."'>[data]</a><br>";
		echo "<img border='0' src='icegraph.php?Id=$sessionId&preset=".$preset['name']."'>";
		echo "</td>\n";
	echo "</tr>\n";
	}
	echo "</table>\n";
	echo "</td>";
	echo "</tr>";
}
$presets = $leginondata->getDatatypes($sessionId);
?>
</tr>
<tr>
<td>
<?=divtitle("Image Statistics");?>
</td>
</tr>
<?
foreach ($presets as $preset) {
if (!$leginondata->getRelatedStats($sessionId, $preset))
	continue;
?>
<tr>
<td>
<a href="statsgraph.php?vdata=1&Id=<?=$sessionId?>&preset=<?=$preset?>">[data]</a><br>
<img src="statsgraph.php?Id=<?=$sessionId?>&preset=<?=$preset?>">
</td>
</tr>
<?
}
?>
</table>
</td>
</tr>
</table>
</body>
</html>
