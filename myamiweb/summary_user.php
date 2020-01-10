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
	$currentproject = $projectdata->getProjectFromSession($sessioninfo['Name']);
	$proj_link= '<a class="header" target="project" href="'.PROJECT_URL."getproject.php?projectId=".$currentproject['projectId'].'">'.$currentproject['name'].'</a>';
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
	
echo "<link rel='stylesheet' href='css/neiladd.css' />";

?>
<script>
function init() {
	this.focus();
}

</script>
</head>

<body onload="init();" >
<table>

</table>
<table>
<tr valign="top">
	<td colspan=3>
	<?php echo divtitle("Summary of $title Experiment"); ?>
	</td>
</tr>
<tr>
 <td colspan=3>
  <a class="header" HREF="index.php">&lt;back to main page&gt;</a>
  &nbsp;
  <a class="header" HREF="3wviewer.php?expId=<?php echo $expId; ?>">&lt;view images <?php echo $title; ?>&gt;</a>
 </td>
</tr>
<tr><td colspan=3><br/></td></tr>
<?php $proj_html=($currentproject) ? '<tr><td><span class="datafield0">Project: </span>'.$proj_link.'</td></tr>'."\n" :''; echo $proj_html ?>


<?php

//echo print_r($currentproject);
//echo "<br/><br/>";

//echo print_r($sessioninfo);
//echo "<br/><br/>";

$instrumentinfos = $leginondata->getInstrumentInfo($sessioninfo['InstrumentId']);
$instrumentinfo = $instrumentinfos[0];
//echo print_r($instrumentinfo);
//echo "<br/><br/>";

$cam_id_array = str_getcsv($sessioninfo['CameraId']);
//echo print_r($cam_id_array);
//echo "<br/><br/>";
$camerainfos = array();
foreach($cam_id_array as $camid) {
	$camidnum = intval($camid);
	$caminfos = $leginondata->getInstrumentInfo($camidnum);
	$caminfo = $caminfos[0];
	$camerainfos[] = $caminfo;
}
//echo print_r($camerainfos);

//$camerainfo =  $leginondata->getInstrumentInfo($sessioninfo['CameraId'])[0];
//echo print_r($camerainfo);

echo "<tr valign='top'><td>";

//
// Project Summary
//

$projid = $currentproject['projectId'];
$projectlink = "<a href='$proj_link'>$projid</a>";
echo divtitle("Project (id $projectlink)");

if (hasExptAdminPrivilege($expId,$privilege_type='data')) {
	$txt = editSessionPurposeTable($expId, $sessioninfo['Purpose']);
} else {
	$txt = staticSessionPurposeTable('Description: ',$sessioninfo['Purpose']);
}

echo opendivbubble();
echo "<hr/>".$currentproject['name']."<br/><hr/>".$txt;
echo "</div>";

//
// Session Summary
//

echo divtitle("Session Information (id <a HREF='3wviewer.php?expId=$expId'>$expId</a>)");

$fields = array('User', 'Begin Time', 'End Time', 'Total Duration', 'Image path');
echo "<table class='paleBlueRows'>";
foreach($fields as $k) {
	$v = $sessioninfo[$k];
	echo formatHtmlRow($k, $v);
}
echo "</table>\n";

//
// Instrumentation
//

echo divtitle("Instrumentation");
$fields = array('Instrument', );
echo "<table class='paleBlueRows'>";
echo "<tr><td colspan=2 style='font-weight: bold; color: #3F4F4F; font-size: 110%'>Microscope "
."<span style='font-size: 70%'<(id ".$instrumentinfo['DEF_id'].")</span></td></tr>";
echo formatHtmlRow($instrumentinfo['name'], $instrumentinfo['description']);
echo formatHtmlRow("Cs", number_format($instrumentinfo['cs']*1000,3)." mm");

$i = 0;
foreach($camerainfos as $caminfo) {
	$i++;
	echo "<tr><td colspan=2 style='font-weight: bold; color: #3F4F4F; font-size: 110%'>Camera #$i "
	."<span style='font-size: 70%'<(id ".$caminfo['DEF_id'].")</span></td></tr>";
	echo formatHtmlRow($caminfo['name'], $caminfo['description']);
}
echo "</table>\n";

//
// Drift Report
//

echo divtitle("Drift ");
echo "<a href='driftreport.php?Id=$expId&maxr=50'>report &raquo;</a>";
echo "<table border='0'>\n";
	echo "<tr>";
		echo "<td>";
	echo "<a href='avgdriftgraph.php?vd=1&Id=$expId'>[data]</a>";
	echo "<a href='avgdriftgraph.php?vs=1&Id=$expId'>[sql]</a><br>";
	echo "<a href='avgdriftgraph.php?Id=$expId&maxr=50'>";
	echo "<img border='0' src='avgdriftgraph.php?w=256&Id=$expId&maxr=50'>";
	echo "</a>";
		echo "</td>";
	echo "</tr>";
echo "</table>\n";

//
// Contrast Transfer Function
//
		
if ($ptcl) {
	echo divtitle("Contrast Transfer Function");
	$particle = new particledata();
	if ($particle->hasCtfData($expId)) {
		echo "<a href='processing/ctfreport.php?expId=$expId'>"
			."&lt; view full CTF report &gt;</a>\n";

		echo "<h3>CTF Resolution during Leginon run</h3>\n";
		echo "<a href='processing/ctfgraph.php?hg=0&expId=$expId&s=1&"
			."f=resolution_appion&w=1920&h=1080'>\n";
		echo "<img border='0' width='640' height='360' src='processing/ctfgraph.php?"
			."w=640&h=360&hg=0&expId=$expId&s=1&f=resolution_appion'></a>\n";
		
		echo "<h3>Astigmatism Distribution</h3>";
		echo "<a href='processing/ctfgraph.php?hg=0&expId=$expId&s=1&"
			."f=astig_distribution&w=1080&h=1080'>\n";
		echo "<img border='0' width='360' height='360' src='processing/ctfgraph.php?"
			."w=640&h=360&hg=0&expId=$expId&s=1&f=astig_distribution' alt='please wait...'></a>\n";

		echo "<h3>CTF Resolution at 0.5 cutoff</h3>";
		echo "<a href='processing/ctfgraph.php?hg=1&expId=$expId&s=1&xmin=1&xmax=30&"
			."f=resolution_50_percent&w=1920&h=1080'>\n";
		echo "<img border='0' width='640' height='360' src='processing/ctfgraph.php?"
			."w=640&h=360&hg=1&expId=$expId&s=1&xmin=1&xmax=30&f=resolution_50_percent' "
			."alt='please wait...'></a>\n";
	} else {
		echo "no CTF information available";
	}
}

//########################################################################################
//########################################################################################
//########################################################################################
//########################################################################################

echo "</td><td>";

//
// Imaging Summary
//

$summary = $leginondata->getSummary($expId);
if (!empty($summary)) {
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
	//echo print_r($summary);
	$summary_fields[]="Preset<br/>label";
	$summary_fields[]="Mag (X)";
	$summary_fields[]="Dose<br/>(e<sup>-</sup>/&Aring;<sup>2</sup>)";
	$summary_fields[]="Pixel<br/>size (&Aring;)";
	$summary_fields[]="Dimensions";
	$summary_fields[]="Binning";
	$summary_fields[]="Image<br/>count";
	foreach($summary_fields as $s_f) {
		$table_head.="<th>$s_f</th>";
	}
	echo "<td>";
	echo divtitle("Imaging Summary");
	echo "<table class='paleBlueRows'>\n";
	echo "<tr>". $table_head."</tr>";
	$maxpresetscore = 0.0;
	$maxpresetid = -1;
	$maxpresetarray = array();
	foreach($summary as $s) {
		if($s['dose'] > 0) {
			$dose = number_format($s['dose']/1e20,3);
		} else { $dose = ""; }
		$pixelsize = 0.0;
		$imageinfo = $leginondata->getImageInfoFromPreset($s['presetId']);
		//echo print_r($imageinfo);
		//echo "<br/><br/>";
		$pixelsize = 1e10*$imageinfo['pixelsize']*$imageinfo['binning'];
		if ($pixelsize > 50) {
			$apix = number_format($pixelsize,1);
		} else {
			$apix = number_format($pixelsize,3);
		}
		$dims = $imageinfo['dimx'].'x'.$imageinfo['dimy'];
		if ($imageinfo['binning'] == 1) {
			$presetscore = $imageinfo['dimx']*$imageinfo['dimy']*$s['nb']/$pixelsize;
		} else { $presetscore=0; }
		if ($presetscore > $maxpresetscore) {
			$maxpresetscore = $presetscore;
			$maxpresetid = $s['presetId'];
			$maxpresetarray = $s;
		}
		echo formatArrayHtmlRow(
				$s['name'],
				$s['magnification'],
				$dose,
				$apix,
				$dims,
				$imageinfo['binning'],
				$s['nb']
		);
		$tot_imgs += $s['nb'];
	}
	echo "</table>\n";

	echo "<p><b>Total images:</b> $tot_imgs ";

	$totalsecs = $leginondata->getSessionDuration($expId);
	$totaltime = $leginondata->formatDuration($totalsecs);

	echo "&nbsp;&nbsp;<b>Duration:</b> $totaltime";	
}

//
// Ice Thickness
//

$icethicknesspresets = $leginondata->getIceThicknessPresets($expId);
	echo divtitle("Ice Thickness from HoleFinder");
	if (!empty($icethicknesspresets)) {
	echo "<table border='0'>\n";
	echo "<tr>";
		echo "<td>";
		echo "<a href='densityreport.php?Id=$expId'>report &raquo;</a>";
		echo "</td>";
	echo "</tr>";
	echo "<tr>";
	foreach($icethicknesspresets as $preset) {
		echo "<tr>";
		echo "<td>";
		echo "Preset: ".$preset['name']."</br>";
		echo "<a href='icegraph.php?Id=$expId&vdata=1&preset=".$preset['name']."'>[data]</a>";
		echo "<a href='icegraph.php?Id=$expId&vs=1&preset=".$preset['name']."'>[sql]</a><br/>";
		echo "<a href='icegraph.php?Id=$expId&w=1920&h=1080&preset=".$preset['name']."'>";
		echo "<img border='0' src='icegraph.php?Id=$expId&w=640&h=360&preset=".$preset['name']."'>";
		echo "</a>\n";
		echo "</td>\n";
		echo "</tr>\n";
	}
	echo "</table>\n";
} else echo "no Ice Thickness information available";

$icethicknesszlp = $leginondata->getZeroLossIceThickness($expId); # see if anything was collected
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
		//echo "<a href='zlp_icegraph.php?Id=$expId?h=256'>";
		echo "<a href='zlp_icegraph.php?Id=$expId&w=1920&h=1080'>";
		echo "<img border='0' src='zlp_icegraph.php?Id=$expId&w=640&h=360'>";
		echo "</a>\n";
		echo "</td>\n";
		echo "</tr>\n";
		echo "<tr>";
		echo "<td>";
		echo "<a href='zlp_icegraph2.php?Id=$expId&w=1920&h='>";
		echo "<img border='0' src='zlp_icegraph2.php?Id=$expId&w=640&h=360'>";
		echo "</a>\n";
		echo "</td>\n";
		echo "</tr>\n";
		echo "</table>\n";

	} else echo "no ZLP Ice Thickness information available";

	
$icethicknessobj = $leginondata->getObjIceThickness($expId); # see if anything was collected
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
		//echo "<a href='zlp_icegraph.php?Id=$expId?h=256'>";
		echo "<a href='obj_icegraph.php?Id=$expId&w=1920&h=1080'>";
		echo "<img border='0' src='obj_icegraph.php?Id=$expId&w=640&h=360'>";
		echo "</a>\n";
		echo "</td>\n";
		echo "</tr>\n";

		echo "<tr>";
		echo "<td>";
		echo "<a href='obj_icegraph2.php?Id=$expId&w=1920&h=1080'>";
		echo "<img border='0' src='obj_icegraph2.php?Id=$expId&w=640&h=360'>";
		echo "</a>\n";
		echo "</td>\n";
		echo "</tr>\n";

		echo "</table>\n";
		echo "<a href='obj_icegraph.php?Id=$expId&vdata=1'>[data]</a>";
		echo "<a href='obj_icegraph.php?Id=$expId&vs=1'>[sql]</a><br>";
		
		
	} else { 
		echo "no Objective Scattering Ice Thickness information available";
	}

echo "<tr valign='top'><td colspan=3>";
echo divtitle("Session Notes");
echo "</td></tr>";

//
// Comments
//

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
echo "<tr valign='top'><td colspan=3>";
echo divtitle("Experimental Methods");

$imageinfo = $leginondata->getImageInfoFromPreset($maxpresetid);
$presetdata = $leginondata->getAllPresetData($maxpresetid);
$defdata = $leginondata->getMinMaxDefocusForPreset($presetdata['name'], $expId);

//echo print_r($defdata);
//echo "<br/><br/>";
//echo print_r($presetdata);

$dunno = "<span style='font-weight: bold; color: #aa0000'>????</span>";
$microscope = $imageinfo['scope'];
$kv = intval($imageinfo['high tension']/1000);
$camera = $imageinfo['camera'];
$pixelsize = number_format($imageinfo['pixelsize']*1e10,4); ;
$mag = number_format($presetdata['magnification'],0);
$dosepersec = number_format($maxpresetarray['dose']/$presetdata['exposure time']/1e17, 2);
$exposure = number_format($presetdata['exposure time']/1000,2);
$totaldose = number_format($maxpresetarray['dose']/1e20,2);
$frametime = number_format($presetdata['frame time']/1000,2);
$numframes = intval(round($presetdata['exposure time']/$presetdata['frame time'],0));
$numimages = $maxpresetarray['nb'];
$defmin = number_format(-1e6*$defdata['maxdef'], 1);
$defmax = number_format(-1e6*$defdata['mindef'], 1);

echo opendivbubble();

echo "<p style='font-size: 125%'>";

echo "$microscope operated at $kv kV with a $camera imaging system collected at ${mag}X nominal magnification.
The calibrated pixel size of $pixelsize &Aring; was used for processing.";

echo "</p><br/><p style='font-size: 125%'>";

echo "Movies were collected using Leginon (Suloway et al., 2005) at a dose
rate of $dosepersec e<sup>-</sup>/&Aring;<sup>2</sup>/s with a total exposure of $exposure seconds,
for an accumulated dose of $totaldose e<sup>-</sup>/&Aring;<sup>2</sup>. Intermediate frames were recorded
every $frametime seconds for a total of $numframes frames per micrograph. A total of $numimages images were
collected at a nominal defocus range of $defmin &ndash; $defmax &mu;m.";

echo "</p>";
echo "</div>";

if (defined("ACKNOWLEDGEMENTS")) {
	echo divtitle("Acknowledgements");
	
	echo "";
	
	echo opendivbubble();
	
	echo '<table style="margin=50px; border=1px;" ><tr><td>
	<p style="font-size: 125%">';
	
	echo ACKNOWLEDGEMENTS;
	echo '</p>
	</td></tr></table>';
	echo "</div>";
	
	
	echo "<br/><br/>";
	echo "</td></tr>";
}
?>

</td>
</tr>
</table>
<?php
login_footer();
?>
