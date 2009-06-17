<?php
require"inc/particledata.inc";
require"inc/leginon.inc";
require"inc/project.inc";
require"inc/processing.inc";
require"inc/summarytables.inc";

$expId= $_GET['expId'];
$otrId= $_GET['otrId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId&otrId=$otrId";
$projectId=getProjectFromExpId($expId);

$particle = new particledata();

$otrrun = $particle->getOtrRunDataFromId($otrId);
$javascript = editTextJava();

processing_header("OTR Run Report", "OTR Run Report", $javascript);


// get updated description
if ($_POST['updateDesc'.$otrId]) {
	updateDescription('ApOtrRunData', $otrId, $_POST['newdescription'.$otrId]);
	$otrrun['description']=$_POST['newdescription'.$otrId];
}

    // display starting otrrun
$j = "OTR Run: <span class='aptitle'>".$otrrun['runname']."</span> (ID: $otrId)";
$otrtable = apdivtitle($j);

# add edit button to description if logged in
$descDiv = ($_SESSION['username']) ? editButton($otrId, $otrrun['description']) : $otrrun['description'];

$stackcount= commafy($particle->getNumStackParticles($otrrun['REF|ApStackData|tiltstack']));
$stackmpix = $particle->getStackPixelSizeFromStackId($otrrun['REF|ApStackData|tiltstack']);
$stackapix = round($stackmpix*1.0e10,2);
$numpart = commafy($otrrun['numpart']);
$boxsize = $otrrun['boxsize'];

$otrtable.= "<br />\n";
$otrtable .= "<table border='0'><tr><td valign='top'>";

// Parameter Table
$otrtable .= "<table class='tablebubble'>\n";
	if ($numpart)
		$display_keys['Number of Particles'] = "$numpart of $stackcount\n";
	$display_keys['Pixel size'] = $stackapix." &Aring;\n";
	$display_keys['Box size'] = $boxsize." pixels\n";
	$display_keys['Mask radius'] = $otrrun['maskrad']." pixels\n";
	$display_keys['Volume Lowpass filter'] = $otrrun['lowpassvol']." &Aring;\n";
	$display_keys['Particle Highpass filter'] = $otrrun['highpasspart']." &Aring;\n";
	$display_keys['Median filter'] = $otrrun['median']."\n";
	$display_keys['Class numbers'] = $otrrun['classnums']."\n";
	$display_keys['Path name'] = $otrrun['path']."\n";
	$display_keys['Description'] = $descDiv."\n";

	if ($otrrun['fscfile']) {
		$display_keys['FSC Resolution'] = round($otrrun['fsc'],2)." &Aring;\n";
		$display_keys['Rmeasure Resolution'] = round($otrrun['rmeas'],2)." &Aring;\n";
	}
	foreach($display_keys as $k=>$v) {
		$otrtable .= formatHtmlRow($k,$v);
	}
$otrtable .= "</table><br/>\n";
// End Parameter Table


$otrtable .= "</td><td>\n";

// FSC Table
	if ($otrrun['fscfile']) {
		$otrtable .= "<table border='0'>\n";
		$otrtable .= "<tr><td valign='center'>\n";
		$halfint = (int) floor($otrrun['fsc']);
		$otrtable .= "</td><td>\n";
		$fscfile = $otrrun['path']."/".$otrrun['fscfile'];
		$otrtable .= "<a href='fscplot.php?expId=$expId&width=800&height=600&apix=$stackapix&box=$boxsize&fscfile=$fscfile&half=$halfint'>"
		."<img border='0' src='fscplot.php?expId=$expId&width=350&height=250&apix=$stackapix&box=$boxsize"
		."&fscfile=$fscfile&half=$halfint'></a>\n";
		$otrtable .= "</td></tr>\n";
		$otrtable .= "</table><br/>\n";
	}
// End FSC Table

$otrtable .= "</td></tr>\n";
$otrtable .= "</table><br/>\n";


if ($otrrun['REF|ApAlignStackData|alignstack']) {
	$otrtable .= "<table class='tablebubble'><tr><td>\n";
	$otrtable .= "<h4>Alignment information</h4><br/>\n";
	$otrtable .= alignstacksummarytable($otrrun['REF|ApAlignStackData|alignstack'], $mini=True);
	$otrtable .= "</td></tr>\n";
	$otrtable .= "</table><br/>\n";
}
/*if ($otrrun['REF|ApClusteringStackData|clusterstack']) {
	$otrtable .= "<table class='tablebubble'><tr><td>\n";
	$otrtable .= "<h4>Clustering information</h4><br/>\n";
	$otrtable .= clusterstacksummarytable($otrrun['REF|ApAlignStackData|alignstack']);
	$otrtable .= "</td></tr>\n";
	$otrtable .= "</table><br/>\n";
}*/

# get list of gif and png files in directory
$searchstr = $otrrun['path']."/*\.png";
$pngfiles = glob($searchstr);
sort($pngfiles);

$numiter = (int) $otrrun['numiter'];
for ($i = 0; $i <= $numiter; $i++) {
	$j = "OTR Run, <i>iteration ".$i."</i><br/>\n";
	$otrtable .= "<h3>$j</h3>\n";
	$gifsearchstr = $otrrun['path']."/".$otrrun['classnums']."/*".$i.".mrc*.gif";
	$giffiles = glob($gifsearchstr);
	foreach ($giffiles as $snapshot) {
		//echo $snapshot."<br/>\n";
		if (file_exists($snapshot)) {
			$otrtable.= "<img src='loadimg.php?rawgif=1&filename=$snapshot' height='128'>\n";
		}
	}
	$pngsearchstr = $otrrun['path']."/".$otrrun['classnums']."/*".$i.".mrc*.png";
	$pngfiles = glob($pngsearchstr);
	foreach ($pngfiles as $snapshot) {
		if (file_exists($snapshot)) {
			$otrtable.= "<a border='0' href='loadimg.php?filename=$snapshot' target='snapshot'>";
			$otrtable.= "<img src='loadimg.php?h=128&filename=$snapshot' height='128'></a>\n";
		}
	}
	$otrtable.= "<br/>\n";
}

$otrtable.= "<br/>\n";

$euleriter = (int) $otrrun['euleriter'];
for ($i = 1; $i <= $euleriter; $i++) {
	$j = "OTR Run, <i>Euler refinement iteration ".$i."</i><br/>\n";
	$otrtable .= "<h3>$j</h3>\n";
	$gifsearchstr = $otrrun['path']."/".$otrrun['classnums']."/*".$i.".mrc*.gif";
	$giffiles = glob($gifsearchstr);
	foreach ($giffiles as $snapshot) {
		//echo $snapshot."<br/>\n";
		if (file_exists($snapshot)) {
			$otrtable.= "<img src='loadimg.php?rawgif=1&filename=$snapshot' height='128'>\n";
		}
	}
	foreach ($pngfiles as $snapshot) {
		//echo $snapshot."<br/>\n";
		$searchstr = "apshVolume.*".$i."\.mrc\..*.png$";
		$gifsearchstr = "apshVolume.*".$i."\.mrc\..*\.gif$";
		//echo $gifsearchstr."<br/>\n";
		if (eregi($searchstr, $snapshot)) {
			$otrtable.= "<a border='0' href='loadimg.php?filename=$snapshot' target='snapshot'>";
			$otrtable.= "<img src='loadimg.php?h=128&filename=$snapshot' height='128'></a>\n";
		}
	}
	$otrtable.= "<br/>\n";
}


echo $otrtable;

processing_footer();
exit;

?>
