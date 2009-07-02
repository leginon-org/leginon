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
	<td colspan="2">
	<?php echo divtitle("Drift Report $title Experiment"); ?>
	</td>
</tr>
<?php
echo "<tr>";
echo "<td colspan='2'>";
echo divtitle("Avg. drift rate at end of measurement cycle");
echo "<br>";
?>
<form method="POST" action="<?php echo $_SERVER['REQUEST_URI']; ?>">
	max rate:<input class="field" name="maxr" type="text" size="5" value="<?php echo $maxrate; ?>">
</form>
<?php
$urlrate = ($maxrate) ? "&maxr=$maxrate" : "";
echo "<a href='avgdriftgraph.php?vd=1&Id=$sessionId'>[data]</a>";
echo "<a href='avgdriftgraph.php?vs=1&Id=$sessionId'>[sql]</a><br>";
echo "<img src='avgdriftgraph.php?Id=$sessionId$urlrate'>";
echo "<br>";
echo "<br>";
echo "<img src='avgdriftgraph.php?hg=1&Id=$sessionId$urlrate'>";
echo "</td>\n";
?>
</tr>
<tr>
<td>
<?php echo divtitle("Total time spent drifting"); ?>
</td>
</tr>
<tr>
<td>
<a href="drifttimegraph.php?vd=1&Id=<?php echo $sessionId; ?>">[data]</a>
<a href="drifttimegraph.php?vs=1&Id=<?php echo $sessionId; ?>">[sql]</a><br>
<img src="drifttimegraph.php?Id=<?php echo $sessionId; ?>">
</td>
</tr>
</table>
</td>
</tr>
</table>
</body>
</html>
