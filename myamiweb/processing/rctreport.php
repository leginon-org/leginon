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
$pngfiles=array();
$rctrundir= opendir($rctrun['path']);
while ($f = readdir($rctrundir)) {
	if (eregi('^volume.*\.mrc\.[0-9]\.png$', $f))
		$pngfiles[] = $f;
}
sort($pngfiles);

    // display starting rctrun
$j = "RCT Run ID: $rctId";
$rcttable = apdivtitle($j);

# add edit button to description if logged in
$descDiv = ($_SESSION['username']) ? editButton($rctId, $rctrun['description']) : $rctrun['description'];

$stackcount= $particle->getNumStackParticles($rctrun['REF|ApStackData|tiltstack']);
$stackmpix = $particle->getStackPixelSizeFromStackId($rctrun['REF|ApStackData|tiltstack']);
$stackapix = format_angstrom_number($stackmpix);

$rcttable.= "<br />\n";
$rcttable.= "<b>num part:</b> $stackcount<br />\n";
$rcttable.= "<b>pixel size:</b> $stackapix<br />\n";
$rcttable.= "<b>box size:</b> $rctrun[boxsize]<br />\n";
//$rcttable.= "<b>resolution:</b> $density[resolution]<br />\n";
$rcttable.= "<b>Filename:</b><br />$rctrun[path]<br />\n";
$rcttable.= "<b>Description:</b><br />$descDiv<br />\n";

$numiter = (int) $rctrun['numiter'];
for ($i = 0; $i <= $numiter; $i++) {
	$j = "RCT Run iteration ".$i."<br/>\n";
	$rcttable .= apdivtitle($j);
	foreach ($pngfiles as $snapshot) {
		$searchstr = "^volume.*".$i."\.mrc\.[0-9]\.png$";
		if (eregi($searchstr, $snapshot)) {
			$snapfile = $rctrun['path'].'/'.$snapshot;
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
