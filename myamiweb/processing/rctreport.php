<?php
require"inc/particledata.inc";
require"inc/leginon.inc";
require"inc/project.inc";
require"inc/processing.inc";
require"inc/summarytables.inc";

$expId= $_GET['expId'];
$rctId= $_GET['rctId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId&rctId=$rctId";
$projectId=getProjectFromExpId($expId);

$particle = new particledata();

$rctrun = $particle->getRctRunDataFromId($rctId);
$javascript = editTextJava();

processing_header("RCT Run Report", "RCT Run Report", $javascript);


// get updated description
if ($_POST['updateDesc'.$rctId]) {
	updateDescription('ApRctRunData', $rctId, $_POST['newdescription'.$rctId]);
	$rctrun['description']=$_POST['newdescription'.$rctId];
}

    // display starting rctrun
$j = "RCT Run: <span class='aptitle'>".$rctrun['runname']."</span> (ID: $rctId)";
$rcttable = apdivtitle($j);

# add edit button to description if logged in
$descDiv = ($_SESSION['username']) ? editButton($rctId, $rctrun['description']) : $rctrun['description'];

$stackcount= commafy($particle->getNumStackParticles($rctrun['REF|ApStackData|tiltstack']));
$stackmpix = $particle->getStackPixelSizeFromStackId($rctrun['REF|ApStackData|tiltstack']);
$stackapix = round($stackmpix*1.0e10,2);
$numpart = commafy($rctrun['numpart']);
$boxsize = $rctrun['boxsize'];

$rcttable.= "<br />\n";
$rcttable .= "<table border='0'><tr><td valign='top'>";

// Parameter Table
$rcttable .= "<table class='tablebubble'>\n";
	if ($numpart)
		$display_keys['Number of Particles'] = "$numpart of $stackcount\n";
	$display_keys['Pixel size'] = $stackapix." &Aring;\n";
	$display_keys['Box size'] = $boxsize." pixels\n";
	$display_keys['Mask radius'] = $rctrun['maskrad']." pixels\n";
	$display_keys['Volume Lowpass filter'] = $rctrun['lowpassvol']." &Aring;\n";
	$display_keys['Particle Highpass filter'] = $rctrun['highpasspart']." &Aring;\n";
	$display_keys['Median filter'] = $rctrun['median']."\n";
	$display_keys['Class numbers'] = $rctrun['classnums']."\n";
	$display_keys['Path name'] = $rctrun['path']."\n";
	$display_keys['Description'] = $descDiv."\n";

	if ($rctrun['fscfile']) {
		$display_keys['FSC Resolution'] = round($rctrun['fsc'],2)." &Aring;\n";
		$display_keys['Rmeasure Resolution'] = round($rctrun['rmeas'],2)." &Aring;\n";
	}
	foreach($display_keys as $k=>$v) {
		$rcttable .= formatHtmlRow($k,$v);
	}
$rcttable .= "</table><br/>\n";
// End Parameter Table


$rcttable .= "</td><td>\n";

// FSC Table
	if ($rctrun['fscfile']) {
		$rcttable .= "<table border='0'>\n";
		$rcttable .= "<tr><td valign='center'>\n";
		$halfint = (int) floor($rctrun['fsc']);
		$rcttable .= "</td><td>\n";
		$fscfile = $rctrun['path']."/".$rctrun['fscfile'];
		$rcttable .= "<a href='fscplot.php?expId=$expId&width=800&height=600&apix=$stackapix&box=$boxsize&fscfile=$fscfile&half=$halfint'>"
		."<img border='0' src='fscplot.php?expId=$expId&width=350&height=250&apix=$stackapix&box=$boxsize"
		."&fscfile=$fscfile&half=$halfint'></a>\n";
		$rcttable .= "</td></tr>\n";
		$rcttable .= "</table><br/>\n";
	}
// End FSC Table

$rcttable .= "</td></tr>\n";
$rcttable .= "</table><br/>\n";


if ($rctrun['REF|ApAlignStackData|alignstack']) {
	$rcttable .= "<table class='tablebubble'><tr><td>\n";
	$rcttable .= "<h4>Alignment information</h4><br/>\n";
	$rcttable .= alignstacksummarytable($rctrun['REF|ApAlignStackData|alignstack'], $mini=True);
	$rcttable .= "</td></tr>\n";
	$rcttable .= "</table><br/>\n";
}
/*if ($rctrun['REF|ApClusteringStackData|clusterstack']) {
	$rcttable .= "<table class='tablebubble'><tr><td>\n";
	$rcttable .= "<h4>Clustering information</h4><br/>\n";
	$rcttable .= clusterstacksummarytable($rctrun['REF|ApAlignStackData|alignstack']);
	$rcttable .= "</td></tr>\n";
	$rcttable .= "</table><br/>\n";
}*/

# get list of gif and png files in directory
$searchstr = $rctrun['path']."/*\.png";
$pngfiles = glob($searchstr);
sort($pngfiles);

$numiter = (int) $rctrun['numiter'];
for ($i = 0; $i <= $numiter; $i++) {
	$j = "RCT Run, <i>iteration ".$i."</i><br/>\n";
	$rcttable .= "<h3>$j</h3>\n";
	$gifsearchstr = $rctrun['path']."/*".$i.".mrc*.gif";
	$giffiles = glob($gifsearchstr);
	foreach ($giffiles as $snapshot) {
		//echo $snapshot."<br/>\n";
		if (file_exists($snapshot)) {
			$rcttable.= "<img src='loadimg.php?rawgif=1&filename=$snapshot' height='128'>\n";
		}
	}
	foreach ($pngfiles as $snapshot) {
		//echo $snapshot."<br/>\n";
		$searchstr = "volume.*".$i."\.mrc\..*.png$";
		$gifsearchstr = "volume.*".$i."\.mrc\..*\.gif$";
		//echo $gifsearchstr."<br/>\n";
		if (eregi($searchstr, $snapshot)) {
			$rcttable.= "<a border='0' href='loadimg.php?filename=$snapshot' target='snapshot'>";
			$rcttable.= "<img src='loadimg.php?h=128&filename=$snapshot' height='128'></a>\n";
		}
	}
	$rcttable.= "<br/>\n";
}

$rcttable.= "<br/>\n";


echo $rcttable;

processing_footer();
exit;

?>
