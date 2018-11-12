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
$expId = $sessionId;

//Block unauthorized user
checkExptAccessPrivilege($expId,'data');

// --- Set  experimentId
// $lastId = $leginondata->getLastSessionId();
// $sessionId = (empty($_GET[Id])) ? $lastId : $_GET[sessionId];
$sessioninfo = $leginondata->getSessionInfo($sessionId);
$title = $sessioninfo[Name];
//$presets = $leginondata->getDatalabels($sessionId);
$presets = $leginondata->getDataTypes($sessionId);
$preset="hi3";
$preset=$_GET['preset'];
$timings = $leginondata->getTiming($sessionId, $preset);

?>
<html>
<head>
<title>Timing Statistics for session <?php $title; ?></title>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
</head>

<body>
<table border="0" cellpadding=10>
<tr>
 <td>
  <a class="header" HREF="index.php">&lt;index&gt;</a>
 </td>
 <td>
  <a class="header" HREF="3wviewer.php?sessionId=<?php $sessionId; ?>">&lt;view <?php $title; ?>&gt;</a>
 </td>
</tr>
</table>
<table border="0" cellpadding=10>
<?php
//Preset Count and Timing Table
$summary = $leginondata->getSummary($expId);
$timingstats2 = $leginondata->getPresetTiming($expId);
$timingstats = $leginondata->getTimingStats($expId);
//print_r($timingstats);
$tot_time=0;
foreach ((array)$timingstats as $t) {
	$images_time[$t['name']]=$t['time'];
	$images_mean[$t['name']]=$t['mean'];
	$images_stdev[$t['name']]=$t['stdev'];
	$images_min[$t['name']]=$t['min'];
	$images_max[$t['name']]=$t['max'];
	$tot_time += $t['time_in_sec'];
}
if (!empty($summary)) {
	$summary_fields[]="Preset<BR>label";
	$summary_fields[]="mag";
	$summary_fields[]="#images";
	if (!empty($images_time)) {
		//$summary_fields[]="time";
		//$summary_fields[]="min";
		//$summary_fields[]="max";
		$summary_fields[]="readout<br />mean";
		$summary_fields[]="readout<br />stdev";
		$summary_fields[]="between<br />mean";
		$summary_fields[]="between<br />stdev";
	}
	foreach($summary_fields as $s_f) {
		$table_head.="<th>$s_f</th>";
	}
	echo '<td colspan="2">';
	echo divtitle("Images Acquired");
	echo "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	echo "<tr >". $table_head."</tr>";
	foreach($summary as $s) {
		echo formatArrayHtmlRow(
				$s['name'],
				$s['magnification'],
				$s['nb'],
				//$images_time[$s['name']],
				//$images_min[$s['name']],
				//$images_max[$s['name']],
				$images_mean[$s['name']],
				$images_stdev[$s['name']],
				$timingstats2[$s['name']]['mean'],
				$timingstats2[$s['name']]['stdev']
		);
		$tot_imgs += $s['nb'];
	}
	echo "</table>\n";
	echo "<p><b>Total images:</b> $tot_imgs ";

	$totalsecs = $leginondata->getSessionDuration($expId);
	$totaltime = $leginondata->formatDuration($totalsecs);

	echo " <b>Duration:</b> $totaltime";
	echo divtitle("Timing");
	echo "</td>";
	
}
echo "</td>";
echo "</tr>";
echo "<tr>";
?>
<tr valign="top">
	<td colspan="2">
	<?php divtitle("Timing Statistics for session $title "); ?>
	</td>
</tr>
<?php
$presets = array_reverse($presets);
foreach ($presets as $preset) {
//	$preset = $preset['label'];
	if (!$preset)
		continue;
	echo "<tr>";
	echo "<td>";
	echo "- Acquisition Time for Preset $preset"; 
	echo "</td>";
	echo "</tr>";
?>
<tr>
<td>
<a href="timingstatsgraph.php?hg=1&vdata=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[data]</a>
<a href="timingstatsgraph.php?hg=1&vs=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[sql]</a><br>
<a href="timingstatsgraph.php?hg=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>"><img border="0" src="timingstatsgraph.php?w=300&hg=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>"></a>
</td>
<td>
<a href="timingstatsgraph.php?vdata=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[data]</a>
<a href="timingstatsgraph.php?vs=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[sql]</a><br>
<a href="timingstatsgraph.php?Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>"><img border="0" src="timingstatsgraph.php?w=300&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>"></a>
</td>
</tr>
<?php } ?>
</table>
</td>
</tr>
</table>
</body>
</html>
