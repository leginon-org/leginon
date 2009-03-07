<?php
require"inc/particledata.inc";
require"inc/leginon.inc";
require"inc/project.inc";
require"inc/processing.inc";

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

# get list of png files in directory
//$pngfiles=array();
//$rctrundir= opendir($rctrun['path']);
$searchstr = $rctrun['path']."/*.png";
//echo $searchstr."<br/>\n";
$pngfiles = glob($searchstr);
//print_r($pngfiles)."<br/>\n";
//while ($f = readdir($rctrundir)) {
//	if (eregi('^volume.*\.mrc\.[0-9]\.png$', $f))
//		$pngfiles[] = $f;
//}
sort($pngfiles);

    // display starting rctrun
$j = "RCT Run: <span class='aptitle'>".$rctrun['runname']."</span> (ID: $rctId)";
$rcttable = apdivtitle($j);

# add edit button to description if logged in
$descDiv = ($_SESSION['username']) ? editButton($rctId, $rctrun['description']) : $rctrun['description'];

$stackcount= commafy($particle->getNumStackParticles($rctrun['REF|ApStackData|tiltstack']));
$stackmpix = $particle->getStackPixelSizeFromStackId($rctrun['REF|ApStackData|tiltstack']);
$stackapix = format_angstrom_number($stackmpix);
$numpart = commafy($rctrun['numpart']);

$rcttable.= "<br />\n";

$rcttable .= "<table border='0'><tr><td valign='top'>";

// Parameter Table
$rcttable .= "<table class='tablebubble'>\n";
	// Particle count
	$rcttable .= "<tr><td valign='center'>\n";
	$rcttable .= "<b>Number of Particles:</b>\n";
	$rcttable .= "</td><td valign='center' colspan='2'>\n";
	if ($numpart)
		$rcttable .= "$numpart of $stackcount\n";
	else
		$rcttable .= "$stackcount\n";
	$rcttable .= "</td></tr>\n";

	// Pixel size
	$rcttable .= "<tr><td valign='center'>\n";
	$rcttable .= "<b>Pixel size:</b>\n</td><td valign='center' colspan='2'>\n$stackapix\n";
	$rcttable .= "</td></tr>\n";

	$boxsize = $rctrun['boxsize'];
	$rcttable .= "<tr><td valign='center'>\n";
	$rcttable .= "<b>Box size:</b>\n</td><td valign='center' colspan='2'>\n$boxsize\n";
	$rcttable .= "</td></tr>\n";

	if ($rctrun['fscfile']) {
		// show resolution info
		$rcttable .= "<tr><td valign='center'>\n";
		$rcttable .= "<b>FSC Resolution:</b>\n</td><td valign='center'>\n".round($rctrun['fsc'],2)." &Aring;\n";

		$rcttable .= "<tr><td valign='center'>\n";
		$rcttable .= "<b>Rmeasure Resolution:</b>\n</td><td valign='center'>\n".round($rctrun['rmeas'],2)." &Aring;\n";
		$rcttable .= "</td></tr>\n";
	}

	$rcttable .= "<tr><td valign='center'>\n";
	$rcttable .= "<b>Path name:</b>\n</td><td valign='center' colspan='2'>\n$rctrun[path]\n";
	$rcttable .= "</td></tr>\n";

	$rcttable .= "<tr><td valign='center'>\n";
	$rcttable .= "<b>Description:</b>\n</td><td valign='center' colspan='2'>\n$descDiv\n";
	$rcttable .= "</td></tr>\n";
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

$numiter = (int) $rctrun['numiter'];
for ($i = 0; $i <= $numiter; $i++) {
	$j = "RCT Run, <i>iteration ".$i."</i><br/>\n";
	$rcttable .= "<h3>$j</h3>\n";
	foreach ($pngfiles as $snapshot) {
		//echo $snapshot."<br/>\n";
		$searchstr = "volume.*".$i."\.mrc\..*.png$";
		if (eregi($searchstr, $snapshot)) {
			//$snapfile = $rctrun['path'].'/'.$snapshot;
			$snapfile = $snapshot;
			$rcttable.= "<a border='0' href='loadimg.php?filename=$snapfile' target='snapshot'>";
			$rcttable.= "<img src='loadimg.php?w=120&filename=$snapfile' width='120'></a>\n";
		}
	}
	$rcttable.= "<br/>\n";
}

$rcttable.= "<br/>\n";


echo $rcttable;

processing_footer();
exit;

?>
