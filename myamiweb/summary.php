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
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
<STYLE type="text/css">
DIV.comment_section { text-align: justify; 
		margin-top: 5px;
		font-size: 10pt}
DIV.comment_subsection { text-indent: 2em;
		font-size: 10pt;
		margin-top: 5px ;
		margin-bottom: 15px ;
	}
</STYLE>
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
<table border="0" cellpadding=10>
<tr valign="top">
	<td colspan="2">
	<?= divtitle("Summary of $title Experiment"); ?>
	</td>
</tr>
<tr valign="top">
	<td>
<?
$sessioninfo = $leginondata->getSessionInfo($expId);
if (!empty($sessioninfo)) {
	echo divtitle("Experiment Information");
	echo "<table border='0'>\n";
	$i=0;
	foreach($sessioninfo as $k=>$v) {
		echo formatHtmlRow($k, $v);
	}
	echo "</table>\n";
}
echo "</td>";
$summary = $leginondata->getSummary($expId);
if (!empty($summary)) {
	echo "<td>";
	echo divtitle("Images Acquired");
	echo "<table border='0'>\n";
	echo "<tr>"
		."<th>Preset label</th><th> # images</th>"
		."</tr>";
	foreach($summary as $s) {
		echo formatHtmlRow($s['name'], $s['nb']);
		$tot_imgs += $s[nb];
	}
	echo "</table>\n";
	echo "<p>Total images:<b>$tot_imgs</b>";
	echo "</td>";
	
}
?>
</tr>
<tr>
<td colspan="2">
<?
$comments = $leginondata->getComments($expId);
if (!empty($comments)) {
	echo divtitle("Comments");
	foreach ($comments as $c) {
		$name = ($c['name']) ? " - ".$c['name']." wrote: " : ":";
		echo '<div class="comment_section">';
		echo "<span style='color: #777777'>".$c['timestamp']."</span>".$name;
		echo '<div class="comment_subsection"><p style="margin: 0px 0px 10px 0px ">';
		echo $c['comment'];
		echo "</div>";
		echo "</div>";
	}
}
?>
</td>
</tr>
</table>
</body>
</html>
