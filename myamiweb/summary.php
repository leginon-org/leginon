<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');

// --- Set  experimentId
$lastId = $leginondata->getLastSessionId();
$expId = (empty($_GET[expId])) ? $lastId : $_GET[expId];
$sessioninfo = $leginondata->getSessionInfo($expId);
$title = $sessioninfo[Name];

?>
<html>
<head>
<title><?=$title?> summary</title>
<link rel="stylesheet" type="text/css" href="css/leginon.css"> 
</head>

<body>
<table border=0 cellpadding=10>
<tr>
 <td>
  <A class="header" HREF="index.php">&lt;index&gt;</A>
 </td>
 <td>
  <A class="header" HREF="3wviewer.php?expId=<?=$expId?>">&lt;view <?=$title?>&gt;</A>
 </td>
</tr>
</table>
<hr>
<h2>Summary of <?=$title?> Experiment</h2>
<?
$sessioninfo = $leginondata->getSessionInfo($expId);
if (!empty($sessioninfo)) {
	echo "<h3>Experiment Information</h3>";
	echo "<table border='0' cellspacing='1' >\n";
	$i=0;
	foreach($sessioninfo as $k=>$v) {
		echo "<tr>\n";
		$class = ($i%2==0) ? 'ti1' : 'ti2';
		echo "<td class='$class'>";
		echo $k;
		echo "</td>";
		$class = ($i%2==0) ? 'dt1' : 'dt2';
		echo "<td class='$class'>";
		echo $v;
		echo "</td>";
		echo "</tr>\n";
		$i++;
	}
	echo "</table>\n";
}
$summary = $leginondata->getSummary($expId);
if (!empty($summary)) {
	echo "<h3>Images Acquired</h3>";
	echo "<table border='0' cellspacing='1' >\n";
	echo "<tr>"
		."<th>Preset label</th><th> # images</th>"
		."</tr>";
	foreach($summary as $k=>$v) {
		echo "<tr>\n";
		$class = ($k%2==0) ? 'ti1' : 'ti2';
		echo "<td class='$class'>";
		echo $v[name];
		echo "</td>";
		$class = ($k%2==0) ? 'dt1' : 'dt2';
		echo "<td class='$class'>";
		echo $v[nb];
		echo "</td>";
		echo "</tr>\n";
		$tot_imgs += $v[nb];
	}
	echo "</table>\n";
	echo "<p>Total images:<b>$tot_imgs</b>";
	
}
?>
</body>
</html>
