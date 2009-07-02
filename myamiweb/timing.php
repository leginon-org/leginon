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

// --- Set  experimentId
// $lastId = $leginondata->getLastSessionId();
// $sessionId = (empty($_GET[Id])) ? $lastId : $_GET[sessionId];
$sessioninfo = $leginondata->getSessionInfo($sessionId);
$title = $sessioninfo[Name];
//$presets = $leginondata->getDatalabels($sessionId);
$presets = $leginondata->getDatatypes($sessionId);
$preset="hi3";
$preset=$_GET['preset'];
$timings = $leginondata->getTiming($sessionId, $preset);

?>
<html>
<head>
<title>Timing Statistics for session <?=$title; ?></title>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
</head>

<body>
<table border="0" cellpadding=10>
<tr>
 <td>
  <a class="header" HREF="index.php">&lt;index&gt;</a>
 </td>
 <td>
  <a class="header" HREF="3wviewer.php?sessionId=<?=$sessionId; ?>">&lt;view <?=$title; ?>&gt;</a>
 </td>
</tr>
</table>
<table border="0" cellpadding=10>
<tr valign="top">
	<td colspan="2">
	<?=divtitle("Timing Statistics for session $title "); ?>
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
<a href="timingstatsgraph.php?hg=1&vdata=1&Id=<?=$sessionId; ?>&preset=<?=$preset; ?>">[data]</a>
<a href="timingstatsgraph.php?hg=1&vs=1&Id=<?=$sessionId; ?>&preset=<?=$preset; ?>">[sql]</a><br>
<a href="timingstatsgraph.php?hg=1&Id=<?=$sessionId; ?>&preset=<?=$preset; ?>"><img border="0" src="timingstatsgraph.php?w=300&hg=1&Id=<?=$sessionId; ?>&preset=<?=$preset; ?>"></a>
</td>
<td>
<a href="timingstatsgraph.php?vdata=1&Id=<?=$sessionId; ?>&preset=<?=$preset; ?>">[data]</a>
<a href="timingstatsgraph.php?vs=1&Id=<?=$sessionId; ?>&preset=<?=$preset; ?>">[sql]</a><br>
<a href="timingstatsgraph.php?Id=<?=$sessionId; ?>&preset=<?=$preset; ?>"><img border="0" src="timingstatsgraph.php?w=300&Id=<?=$sessionId; ?>&preset=<?=$preset; ?>"></a>
</td>
</tr>
<?php } ?>
</table>
</td>
</tr>
</table>
</body>
</html>
