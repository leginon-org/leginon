<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');
require('inc/project.inc');

// --- Set  experimentId
$lastId = $leginondata->getLastSessionId();
$expId = (empty($_GET[expId])) ? $lastId : $_GET[expId];
$sessioninfo = $leginondata->getSessionInfo($expId);
$title = $sessioninfo[Name];

$projectdata = new project();
$projectdb = $projectdata->checkDBConnection();
if($projectdb) {
	$currentproject = $projectdata->getProjectFromSession($sessioninfo['Name']);
	$proj_link= '<a class="header" target="project" href="'.$PROJECT_URL."getproject.php?pId=".$currentproject['projectId'].'">'.$currentproject['name'].'</a>';
}


?>
<html>
<head>
<title><?php echo $title; ?> summary</title>
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
<script>
function init() {
	this.focus();
}
</script>
</head>

<body onload="init();" >
<table border=0 cellpadding=10>
<tr>
 <td>
  <A class="header" HREF="index.php">&lt;index&gt;</A>
 </td>
 <td>
  <A class="header" HREF="3wviewer.php?expId=<?php echo $expId; ?>">&lt;view <?php echo $title; ?>&gt;</A>
 </td>
</tr>
</table>
<table border="0" cellpadding=10>
<tr valign="top">
	<td colspan="2">
	<?php echo divtitle("Summary of $title Experiment"); ?>
	</td>
</tr>
	<?=($currentproject) ? '<tr><td><span class="datafield0">Project: </span>'.$proj_link.'</td></tr>' :'' ?>
<tr valign="top">
	<td>
<?php
$sessioninfo = $leginondata->getSessionInfo($expId);
if (!empty($sessioninfo)) {
	echo divtitle("Experiment Information");
	echo "<table border='0'>\n";
	$i=0;
	foreach($sessioninfo as $k=>$v) {
		if (eregi('timestamp', $k))
			continue;
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
echo "</td>";
echo "</tr>";
echo "<tr>";
echo "<td valign='top' colspan='1'>";
echo divtitle("Drift ");
echo "<a href='driftreport.php?Id=$expId'>report &raquo;</a>";
echo "<table border='0'>\n";
	echo "<tr>";
		echo "<td>";
	echo "<a href='avgdriftgraph.php?vd=1&Id=$expId'>[data]</a>";
	echo "<a href='avgdriftgraph.php?vs=1&Id=$expId'>[sql]</a><br>";
	echo "<a href='avgdriftgraph.php?Id=$expId'>";
	echo "<img border='0' src='avgdriftgraph.php?w=256&Id=$expId'>";
	echo "</a>";
		echo "</td>";
	echo "</tr>";
echo "</table>\n";
echo "</td>";
echo "<td valign='top' >";
echo divtitle("Temperature");
$channels = "&ch0=1&ch1=1&ch2=1&ch4=1&ch5=1&ch6=1&ch7=1&opt=1";
echo "<a href='temperaturereport.php?Id=$expId$channels'>report &raquo;</a>";
echo "<table border='0'>\n";
	echo "<tr>";
		echo "<td>";
	echo "<a href='temperaturegraph.php?vd=1&Id=$expId$channels'>[data]</a>";
	echo "<a href='temperaturegraph.php?vs=1&Id=$expId$channels'>[sql]</a><br>";
	echo "<a href='temperaturegraph.php?Id=$expId$channels'>";
	echo "<img border='0' src='temperaturegraph.php?w=256&Id=$expId$channels'>";
	echo "</a>";
		echo "</td>";
	echo "</tr>";
echo "</table>\n";
echo "</td>";
echo "</tr>";
$presets = $leginondata->getDatatypes($expId);
	echo "<tr>";
	echo "<td colspan='2'>";
	echo divtitle("Image Stats");
	$r = $leginondata->getImageStats($expId);
if ($r) {
	echo "<a href='imagestatsreport.php?Id=$expId'>report &raquo;</a>";
	echo "<table border='0'>\n";
	$n=0;
	echo "<tr>";
	foreach ($presets as $preset) {
		$sessionId=$expId;
		
		if ($n%3==0) {
			echo "</tr>";
			echo "<tr>";
		}
		$n++;
?>
	<td>
	Preset: <?php echo $preset; ?>
	<a href="imagestatsgraph.php?hg=1&vdata=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[data]</a>
	<a href="imagestatsgraph.php?hg=1&vs=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[sql]</a><br>
	<a href="imagestatsgraph.php?hg=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>"><img border="0"  src="imagestatsgraph.php?hg=1&w=210&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>"></a>
	</td>
<?php
	}
echo "</tr>";
echo "</table>";
} else echo "no Image Stats information available";
echo "</td>";
echo "</tr>";
$icethicknesspresets = $leginondata->getIceThicknessPresets($expId);
	echo "<tr>";
	echo "<td colspan='2'>";
	echo divtitle("Ice Thickness");
	if (!empty($icethicknesspresets)) {
	echo "<table border='0'>\n";
	echo "<tr>";
		echo "<td>";
		echo "<a href='densityreport.php?Id=$expId'>report &raquo;</a>";
		echo "</td>";
	echo "</tr>";
	echo "<tr>";
	foreach($icethicknesspresets as $preset) {
		echo "<td>";
		echo "<a href='icegraph.php?Id=$expId&vdata=1&preset=".$preset['name']."'>[data]</a>";
		echo "<a href='icegraph.php?Id=$expId&vs=1&preset=".$preset['name']."'>[sql]</a><br>";
		echo "<a href='icegraph.php?Id=$expId&preset=".$preset['name']."'>";
		echo "<img border='0' src='icegraph.php?Id=$expId&w=256&preset=".$preset['name']."'>";
		echo "</a>\n";
		echo "</td>\n";
	}
	echo "</tr>\n";
	echo "</table>\n";
} else echo "no Ice Thickness information available";
	echo "</td>";
	
?>
</tr>
<tr>
<td colspan="2">
<?php
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
<tr>
<td colspan="2">
<?php
$minconf = (is_numeric($_POST['mconf'])) ? $_POST['mconf'] 
		: (is_numeric($_GET['mconf']) ? $_GET['mconf'] : false);

echo divtitle("CTF");
require('inc/ctf.inc');
$sessionId=$expId;
$ctf = new ctfdata();
if ($ctf->hasCtfData($sessionId)) {

	echo "<a href='ctfreport.php?Id=$sessionId'>report &raquo;</a>\n";
	?>
	<form method="POST" action="<?php echo $_SERVER['REQUEST_URI']; ?>">
		minimum allowed confidence:<input class="field" name="mconf" type="text" size="5" value="<?php echo $minconf; ?>">
	</form>
	<?php
	$urlmconf = ($minconf) ? "&mconf=$minconf" : "";

	$display_keys = array ( 'preset', 'nb', 'min', 'max', 'avg', 'stddev', 'img');
	$fields = array('defocus1', 'defocus2', 'confidence', 'confidence_d');
	$bestctf = $ctf->getBestStats($fields, $sessionId, $minconf);
	foreach($bestctf as $field=>$data) {
		foreach($data as $k=>$v) {
			$preset = $bestctf[$field][$k]['name'];
			$cdf = '<a href="ctfgraph.php?&hg=1&Id='.$sessionId.'&s=1&f='.$field.'&preset='.$preset.''.$urlmconf.'">'
				.'<img border="0" src="ctfgraph.php?w=150&hg=1&Id='.$sessionId.'&s=1&f='.$field.'&preset='.$preset.''.$urlmconf.'"></a>';
			$bestctf[$field][$k]['img'] = $cdf;
		}
	}
	echo "<br>";
	$display_keys = array ( 'name', 'nb', 'min', 'max', 'avg', 'stddev', 'img');
	echo display_stats($bestctf, $display_keys);
	
}
else {
echo "no CTF information available";
}
?>

</td>
</tr>
<tr>
<td colspan="2">
<?php
echo divtitle("Particles");
require('inc/particledata.inc');
$sessionId=$expId;
$particle = new particledata();
if ($particle->hasParticleData($sessionId)) {
	$particlerun=$particle->getLastParticleRun($sessionId);
	$particlestats=$particle->getStats($particlerun);
	$particlestatsimg = '<a href="particlegraph.php?hg=1&run='.$particlerun.'">'
		.'<img border="0" '
		.'src="particlegraph.php?w=150&hg=1&run='
		.$particlerun.'"></a>';
	$particlestats['img']= $particlestatsimg;
//	echo $particlerun;
	echo "<BR>";
//	print_r($particlestats);
	$display_keys = array ( 'totparticles', 'min', 'max', 'avg', 'stddev', 'img');
	$particletable=$particle->displayParticleStats($particlestats, $display_keys, $particlerun);
	echo $particletable;
}
else {
echo "no Particle information available";
}


?>
</td>
</tr>
</table>
</body>
</html>
