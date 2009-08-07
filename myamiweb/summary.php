<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/leginon.inc";
require "inc/project.inc";
if (defined('PROCESSING')) {
	$ptcl = (@require "inc/particledata.inc") ? true : false;
}


// --- Set  experimentId
$lastId = $leginondata->getLastSessionId();
$expId = (empty($_GET['expId'])) ? $lastId : $_GET['expId'];
$sessioninfo = $leginondata->getSessionInfo($expId);
$title = $sessioninfo['Name'];

$projectdata = new project();
$projectdb = $projectdata->checkDBConnection();
if($projectdb) {
	$currentproject = $projectdata->getProjectFromSession($sessioninfo['Name']);
	$proj_link= '<a class="header" target="project" href="'.$PROJECT_URL."getproject.php?pId=".$currentproject['projectId'].'">'.$currentproject['name'].'</a>';
}


?>
<html>
<head>
<title><?=$title; ?> summary</title>
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
  <a class="header" HREF="index.php">&lt;index&gt;</a>
 </td>
 <td>
  <a class="header" HREF="3wviewer.php?expId=<?php echo $expId; ?>">&lt;view <?php echo $title; ?>&gt;</a>
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
	echo "<td>";
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
	echo "<p>Total images:<b>$tot_imgs</b>";
	if ($tot_time)
		echo " time:<b>".sec2time($tot_time)."</b>";
	echo divtitle("Timing");
	echo "<a href='timing.php?Id=$expId'>Timing report &raquo;</a>";
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
<?
$defocusresults = $leginondata->getFocusResultData($expId, 'both','all','ok');
	echo "<tr>";
	echo "<td colspan='2'>";
	echo divtitle("Autofocus Results");
	if (!empty($defocusresults)) {
		echo "<table border='0'>\n";
		echo "<tr>";
		echo "<td>";
		echo "<a href='autofocusgraph.php?Id=$expId&vd=1'>[data]</a>";
		echo "<a href='autofocusgraph.php?Id=$expId&vs=1'>[sql]</a><br>";
		echo "<a href='autofocusgraph.php?Id=$expId'>";
		echo "<img border='0' src='autofocusgraph.php?Id=$expId&w=256'>";
		echo "</a>\n";
		echo "</td>\n";
		echo "</tr>\n";
		echo "</table>\n";
} else echo "no Autofocus information available";
	echo "</td>";
	echo "</tr>";
	echo "<tr>";
	echo '<td colspan="2">';
	foreach ($presets as $preset) {
		$presetinfo=$leginondata->getPresetFromSessionId($sessionId, $preset);
		$displaystat=false;
		foreach ((array)$presetinfo as $row) {
			$displaystat=($row['defocus range min'] && $row['defocus range max']) ? true:false;
			if ($displaystat)
			break;
		}
		if (!$displaystat)
				continue;
		$cstats=$leginondata->getDefocus($sessionId, $preset, true);
		$cstats['preset']=$preset;
		$img='<a href="defocusgraph.php?hg=1&vdata=1&Id='.$sessionId
				.'&preset='.$preset.'">[data]</a> '
				.'<a href="defocusgraph.php?hg=1&vs=1&Id='.$sessionId
				.'&preset='.$preset.'">[sql]</a><br />'
				.'<a href="defocusgraph.php?hg=1&Id='.$sessionId
				.'&preset='.$preset.'"><img border="0"  src="defocusgraph.php?hg=1&w=210'
				.'&Id='.$sessionId.'&preset='.$preset.'"></a>';
		$cstats['img']=$img;
		$ds['defocus'][]=$cstats;
	}
	$display_keys = array ( 'preset', 'nb', 'min', 'max', 'avg', 'stddev', 'img');
	if ($ptcl) {
		echo displayCTFstats($ds, $display_keys);
	}
?>
</td>
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

if ($ptcl) {
echo divtitle("CTF");
$sessionId=$expId;
$particle = new particledata();
if ($particle->hasCtfData($sessionId)) {

	echo "<a href='processing/ctfreport.php?expId=$sessionId'>report &raquo;</a>\n";
	?>
	<form method="POST" action="<?php echo $_SERVER['REQUEST_URI']; ?>">
		minimum allowed confidence:<input class="field" name="mconf" type="text" size="5" value="<?php echo $minconf; ?>">
	</form>
	<?php

	$urlmconf = ($minconf) ? "&mconf=$minconf" : "";

	$display_keys = array ( 'preset', 'nb', 'min', 'max', 'avg', 'stddev', 'img');
	$fields = array('defocus1', 'confidence', 'confidence_d','difference');
	$bestctf = $particle->getBestStats($fields, $sessionId, $minconf);
	
	if ($bestctf) {
		foreach($bestctf as $field=>$data) {
			foreach($data as $k=>$v) {
				$preset = $bestctf[$field][$k]['name'];
				if ($field !='difference') {
					$cdf='<a href="processing/ctfgraph.php?&hg=1&Id='.$sessionId
							.'&s=1&f='.$field.'&preset='.$preset.''.$urlmconf.'">'
							.'<img border="0" src="processing/ctfgraph.php?w=150&hg=1&Id='.$sessionId
							.'&s=1&f='.$field.'&preset='.$preset.''.$urlmconf.'"></a>';
				} else {	
					$cdf='<a href="processing/autofocacegraph.php?&hg=0&Id='.$sessionId
							.'&s=1&f='.$field.'&preset='.$preset.''.$urlmconf.'">'
							.'<img border="0" src="processing/autofocacegraph.php?w=150&hg=0&Id='.$sessionId
							.'&s=1&f='.$field.'&preset='.$preset.''.$urlmconf.'"></a>';
				}
				$bestctf[$field][$k]['img'] = $cdf;
			}
		}
		echo '<a href="processing/showctfdata.php?Id='.$sessionId.''.$urlmconf.'&vd=1">[data]</a>';
		echo '<a href="processing/showctfdata.php?Id='.$sessionId.''.$urlmconf.'&vs=1">[sql]</a>';
		$display_keys = array ( 'name', 'nb', 'min', 'max', 'avg', 'stddev', 'img');
		echo displayCTFstats($bestctf, $display_keys);
		} else { echo "Database Error"; }
	} else {
		echo "no CTF information available";
	}
}
?>

</td>
</tr>
<tr>
<td colspan="2">
<?php
echo divtitle("Particles");
$sessionId=$expId;
if ($ptcl && $particle->hasParticleData($sessionId)) {
	$inspectcheck=($_POST['onlyinspected']=='on') ? 'CHECKED' : '';
	$mselexval=(is_numeric($_POST['mselex'])) ? $_POST['mselex'] 
			: (is_numeric($_GET['mselex']) ? $_GET['mselex'] : false);
	echo"<FORM NAME='prtl' method='POST' action='".$_SERVER['REQUEST_URI']."'>
	     <INPUT TYPE='CHECKBOX' name='onlyinspected' $inspectcheck onclick='javascript:document.prtl.submit()'>Don't use particles from discarded images<BR>
	     <INPUT CLASS='field' NAME='mselex' TYPE='text' size='5' VALUE='$mselexval'>Minimum correlation value
	     </form>\n";
	$numinspected=$particle->getNumAssessedImages($sessionId);
	echo"Inpected images: $numinspected, ";
	if ($numinspected>0)
		echo'<a href="showinspectdata.php?Id='.$sessionId.'&vd=1">[inspected data]</a>'."\n";
	$display_keys = array ( 'totparticles', 'numimgs', 'min', 'max', 'avg', 'stddev', 'img');
	$particleruns=$particle->getParticleRunIds($sessionId);
	echo $particle->displayParticleStats($particleruns, $display_keys, $inspectcheck, $mselexval);

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
