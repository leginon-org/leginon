<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/leginon.inc";
require_once "inc/project.inc";

login_header(PROJECT_TITLE);

if (defined('PROCESSING')) {
	$ptcl = (@require_once "inc/particledata.inc") ? true : false;
}


// --- Set  experimentId
$lastId = $leginondata->getLastSessionId();
$expId = (empty($_GET['expId'])) ? $lastId : $_GET['expId'];
$sessioninfo = $leginondata->getSessionInfo($expId);
$title = $sessioninfo['Name'];

//Block unauthorized user
checkExptAccessPrivilege($expId,'data');

$projectdata = new project();
$projectdb = $projectdata->checkDBConnection();
if($projectdb) {
	$currentproject = $projectdata->getProjectFromSession($sessioninfo
['Name']);
	$proj_link= '<a class="header" target="project" href="'.PROJECT_URL."getproject.php?projectId=".$currentproject['projectId'].'">'.$currentproject['name'].'</a>';
}


?>
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
	<?php ($currentproject) ? '<tr><td><span class="datafield0">Project: </span>'.$proj_link.'</td></tr>' :'' ?>
<tr valign="top">
	<td>
<?php
$sessioninfo = $leginondata->getSessionInfo($expId);
if (!empty($sessioninfo)) {
	echo divtitle("Experiment Information");
	echo "<table border='0'>\n";
	$i=0;
	foreach($sessioninfo as $k=>$v) {
		if (preg_match('%Purpose%i', $k))
			continue;
		if (preg_match('%timestamp%i', $k))
			continue;
		echo formatHtmlRow($k, $v);
	}
	echo "</table>\n";
}

function editSessionPurposeTable($expId, $purposev) {
	// Edit and update Session description
	global $leginondata;
	if ( !empty($_POST['purpose']) && $purposev != $_POST['purpose'] ) {
		$leginondata->updateSessionPurpose($expId, $_POST['purpose']);
		$purposev = $_POST['purpose'];
	}
	$display .= '
		<table border="0" cellpadding="0" >
			<tr><td>
			<form name="purposeform" method="POST" action="'.$_SERVER['REQUEST_URI'].'">
				<table border="0" cellpadding="0" >
					<tr valign="bottom" width=50>
						<td>
						<td rowspan="1" ><b>Purpose:</b><br>
							<textarea class="textarea" name="purpose" rows="1" cols="40" wrap="virtual"
									>'.$purposev.'</textarea>
						</td><td>
							<input class="bt1" type="button" name="save purpose" value="Save" onclick=\'javascript:document.purposeform.submit()\'/>
						</td>
					</tr>
				</table>
			</form>
			</td></tr>
		</table>
		';
	return $display;
}

function staticSessionPurposeTable($expId, $purposev) {
	$display .= ' '
			.'<table border="0"> '
			.formatHtmlRow('Purpose', $purposev)
		.'</table>';
	return $display;
}
	
if (hasExptAdminPrivilege($expId,$privilege_type='data')) {
	echo editSessionPurposeTable($expId, $sessioninfo['Purpose']);
} else {
	echo staticSessionPurposeTable('Purpose',$sessioninfo['Purpose']);
}

echo "</td>";
$tot_imgs = $leginondata->getNumImages($expId);

echo "<td>";
if ($tot_imgs) {
	//print_r($timingstats);
	echo divtitle("Images Acquired");
	echo "<a href='timing.php?Id=$expId'>report &raquo;</a>";
	echo "<p><b>Total images:</b> $tot_imgs </p>";

	$totalsecs = $leginondata->getSessionDuration($expId);
	$totaltime = $leginondata->formatDuration($totalsecs);

	echo "<p> <b>Duration:</b> $totaltime</p>";
	echo divtitle("Timing");
	echo "<a href='timing.php?Id=$expId'>report &raquo;</a>";
}
echo "</td>";
echo "</tr>";
echo "<tr>";
echo "<td valign='top' colspan='1'>";
echo divtitle("Drift ");
echo "<a href='driftreport.php?Id=$expId&maxr=50'>report &raquo;</a>";
echo "<table border='0'>\n";
	echo "<tr>";
		echo "<td>";
	echo "<a href='avgdriftgraph.php?vd=1&Id=$expId'>[data]</a>";
	echo "<a href='avgdriftgraph.php?vs=1&Id=$expId'>[sql]</a><br>";
	echo "<a href='avgdriftgraph.php?Id=$expId&maxr=50'>";
	echo "<img border='0' src='img/placeholder_scatter.png'>";
	echo "</a>";
		echo "</td>";
	echo "</tr>";
echo "</table>\n";
echo "</td>";
echo "<td valign='top' >";
echo divtitle("Temperature");
echo "</td>";
echo "</tr>";
$presets = $leginondata->getDataTypes($expId);
	echo "<tr>";
	echo "<td colspan='2'>";
	echo divtitle("Image Stats");
if (true) {
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
	<a href="imagestatsgraph.php?vdata=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[data]</a>
	<a href="imagestatsgraph.php?vs=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[sql]</a><br>
	<a href="imagestatsgraph.php?Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>"><img border="0"  src="img/placeholder_scatter.png"></a>
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
		echo "Preset: ".$preset['name']."<a href='icegraph.php?Id=$expId&vdata=1&preset=".$preset['name']."'>[data]</a>";
		echo "<a href='icegraph.php?Id=$expId&vs=1&preset=".$preset['name']."'>[sql]</a><br>";
		echo "<a href='icegraph.php?Id=$expId&preset=".$preset['name']."'>";
		echo "<img border='0' src='img/placeholder_hist.png'>";
		echo "</a>\n";
		echo "</td>\n";
	}
	echo "</tr>\n";
	echo "</table>\n";
} else echo "no Ice Thickness information available";
	echo "</td>";



$icethicknesszlp = $leginondata->getZeroLossIceThickness($expId); # see if anything was collected
	echo "<tr>";
	echo "<td colspan='2'>";
	echo divtitle("ZLP Ice Thickness");
	if (!empty($icethicknesszlp)) {
		echo "<table border='0'>\n";
		echo "<tr>";
		echo "<td>";
		echo "<a href='zlpdensityreport.php?Id=$expId'>report &raquo;</a>";
		echo "</td>";
	echo "</tr>";
	echo "<tr>";
	echo "<tr>";
		echo "<td>";
		echo "<a href='zlp_icegraph.php?Id=$expId&vdata=1'>[data]</a>";
		echo "<a href='zlp_icegraph.php?Id=$expId&vs=1'>[sql]</a><br>";
		echo "<a href='zlp_icegraph.php?Id=$expId&w=1024&h=512'>";
		echo "<img border='0' src='img/placeholder_hist.png'>";
		echo "</a>\n";
		echo "</td>\n";
		echo "</tr>\n";
		echo "<tr>";
		echo "<td>";
		echo "<a href='zlp_icegraph2.php?Id=$expId&w=1024&h=512'>";
		echo "<img border='0' src='img/placeholder_scatter.png'>";
		echo "</a>\n";
		echo "</td>\n";
		echo "</tr>\n";
		echo "</table>\n";

	} else echo "no ZLP Ice Thickness information available";
		echo "</td>";

	
$icethicknessobj = $leginondata->getObjIceThickness($expId); # see if anything was collected
	echo "<tr>";
	echo "<td colspan='2'>";
	echo divtitle("Objective Scattering Ice Thickness");
	if (!empty($icethicknessobj)) {
		echo "<table border='0'>\n";
		echo "<tr>";
		echo "<td>";
		echo "<a href='objdensityreport.php?Id=$expId'>report &raquo;</a>";
		echo "</td>";
	echo "</tr>";
	echo "<tr>";
	echo "<tr>";
		echo "<td>";
		echo "<a href='obj_icegraph.php?Id=$expId&vdata=1'>[data]</a>";
		echo "<a href='obj_icegraph.php?Id=$expId&vs=1'>[sql]</a><br>";
		echo "<a href='obj_icegraph.php?Id=$expId&w=1024&h=512'>";
		echo "<img border='0' src='img/placeholder_hist.png'>";
		echo "</a>\n";
		echo "</td>\n";
		echo "</tr>\n";

		echo "<tr>";
		echo "<td>";
		echo "<a href='obj_icegraph2.php?Id=$expId&w=1024&h=512'>";
		echo "<img border='0' src='img/placeholder_scatter.png'>";
		echo "</a>\n";
		echo "</td>\n";
		echo "</tr>\n";

		echo "</table>\n";

	} else { 
		echo "no Objective Scattering Ice Thickness information available";
		echo "<a href='obj_icegraph.php?Id=$expId&vdata=1'>[data]</a>";
		echo "<a href='obj_icegraph.php?Id=$expId&vs=1'>[sql]</a><br>";

		echo "</td>";

		}


#############
#	echo "<tr>";
#	echo "<td colspan='2'>";
#	echo divtitle("Ice Thickness");
#	if (!empty($icethicknesszlp)) {
#		echo "<td>";
#		echo "<a href='zlp_icegraph.php?Id=$expId&vdata=1'>[data]</a>";
#		echo "<a href='zlp_icegraph.php?Id=$expId&vs=1'>[sql]</a><br>";
#		//echo "<a href='zlp_icegraph.php?Id=$expId?h=256'>";
#		echo "<a href='zlp_icegraph.php?Id=$expId&w=256&h=256'>";
#		echo "<img border='0' src='img/placeholder_scatter.png'>";
#		echo "</a>\n";
#		echo "</td>\n";
#	}
################
	
?>

</tr>
<?php
$imageshiftpresets = $leginondata->getImageShiftPresets($expId);
echo "<tr>";
echo "<td colspan='2'>";
echo divtitle("Image Shift");
if (!empty($imageshiftpresets)) {
	echo "<table border='0'>\n";
	echo "<tr>";
		echo "<td>";
		echo "<a href='imageshiftreport.php?Id=$expId'>report &raquo;</a>";
		echo "</td>";
	echo "</tr>";
	foreach($imageshiftpresets as $preset) {
		echo "<tr>";
		echo "<td>";
		echo "Preset: ".$preset['name']." <a href='imageshiftgraph.php?Id=$expId&vdata=1&preset=".$preset['name']."'>[data]</a>";
		echo "<a href='imageshiftgraph.php?Id=$expId&vs=1&preset=".$preset['name']."'>[sql]</a> x vs y<br>";
		echo "<a href='imageshiftgraph.php?Id=$expId&preset=".$preset['name']."'>";
		echo "<img border='0' src='img/placeholder_scatter.png'>";
		echo "</a>\n";
		echo "</td>\n";
		echo "<td>";
		echo "Preset: ".$preset['name']."<a href='imageshiftgraph.php?Id=$expId&hg=1&haxis=x&vdata=1&preset=".$preset['name']."'>[data]</a>";
		echo "<a href='imageshiftgraph.php?Id=$expId&hg=1&haxis=x&vs=1&preset=".$preset['name']."'>[sql]</a> x-axis<br>";
		echo "<a href='imageshiftgraph.php?Id=$expId&hg=1&haxis=x&preset=".$preset['name']."'>";
		echo "<img border='0' src='img/placeholder_hist.png'>";
		echo "</a>\n";
		echo "</td>\n";
		echo "<td>";
		echo "Preset: ".$preset['name']."<a href='imageshiftgraph.php?Id=$expId&hg=1&vdata=1&preset=".$preset['name']."'>[data]</a>";
		echo "<a href='imageshiftgraph.php?Id=$expId&hg=1&vs=1&preset=".$preset['name']."'>[sql]</a> y-axis<br>";
		echo "<a href='imageshiftgraph.php?Id=$expId&hg=1&preset=".$preset['name']."'>";
		echo "<img border='0' src='img/placeholder_hist.png'>";
		echo "</a>\n";
		echo "</td>\n";
		echo "</tr>\n";
	}
	echo "</table>\n";
} else echo "no Image Shift information available";
	echo "</td>";
	
?>
</tr>
<?php
	echo "<tr>";
	echo "<td colspan='2'>";
	echo divtitle("Autofocus Results");
	if (true) {
		echo "<table border='0'>\n";
		echo "<tr>";
		echo "<td>";
		echo "<a href='autofocusgraph.php?Id=$expId&vd=1'>[data]</a>";
		echo "<a href='autofocusgraph.php?Id=$expId&vs=1'>[sql]</a><br>";
		echo "<a href='autofocusgraph.php?Id=$expId'>";
		echo "<img border='0' src='img/placeholder_scatter.png'>";
		echo "</a>\n";
		echo "</td><td>\n";
		echo "<a href='zheightgraph.php?Id=$expId&vd=1'>[data]</a><br>";
		echo "<a href='zheightgraph.php?Id=$expId'>";
		echo "<img border='0' src='img/placeholder_map.png'>";
		echo "</td>\n";
		echo "</tr>\n";
		echo "</table>\n";
} else echo "no Autofocus information available";
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
      .'&preset='.$preset.'"><img border="0" src="img/placeholder_hist.png"></a>';
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
$minres = (is_numeric($_POST['mres'])) ? $_POST['mres'] 
		: (is_numeric($_GET['mres']) ? $_GET['mres'] : false);

if ($ptcl) {
echo divtitle("CTF");
$sessionId=$expId;
$particle = new particledata();
if ($particle->hasCtfData($sessionId)) {

	echo "<a href='processing/ctfreport.php?expId=$sessionId'>report &raquo;</a>\n";
	?>
	<form method="POST" action="<?php echo $_SERVER['REQUEST_URI']; ?>">
		maximum allowed CTF appion resolution (&Aring;) for phase shift graph:<input class="field" name="mres" type="text" size="5" value="<?php echo $minres; ?>">
	</form>
	<?php

	$urlmres = ($minres) ? "&mres=$minres" : "";

	if (true) {
		//phase shift progression
		echo '</td></tr><tr><td>'."\n";
		echo 'Phase shift by phase plate';
		$phasegraph = '<a href="processing/phaseshiftgraph.php?expId='.$sessionId.'&hg=0'
							.'&s=1'.$urlmres.'">'
							.'<img border="0" src="img/placeholder_scatter.png"></a>';
		echo '</td></tr><tr><td>'."\n";
		echo $phasegraph;
		echo "<a href='processing/phaseshiftgraph.php?vd=1&s=1&hg=0&expId=$expId".$urlmres."'>[data]</a>";
		echo '</td></tr><tr><td>'."\n";

		//Summary table
		echo "<a href='processing/ctfreport.php?expId=$sessionId'>See summary in report &raquo;</a>\n";
	}
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
if (true) {
		echo "<a href='processing/prtlreport.php?expId=$sessionId'>report &raquo;</a>\n";
} 
else {
        echo "no Particle information available";
}

?>
</td>
</tr>
</table>
<?php
login_footer();
?>
