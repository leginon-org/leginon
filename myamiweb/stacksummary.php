<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require ('inc/leginon.inc');
require ('inc/particledata.inc');
require ('inc/project.inc');
require ('inc/viewer.inc');
require ('inc/processing.inc');
  
// check if coming directly from a session
$expId = $_GET['expId'];
if ($expId) {
        $sessionId=$expId;
        $formAction=$_SERVER['PHP_SELF']."?expId=$expId";
}
else {
        $sessionId=$_POST['sessionId'];
        $formAction=$_SERVER['PHP_SELF'];
}
$projectId=$_POST['projectId'];

$javascript="<script src='js/viewer.js'></script>\n";

writeTop("Stack Report","Stack Summary Page", $javascript);

echo"<form name='viewerform' method='POST' ACTION='$formAction'>
<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
echo "</FORM>\n";

// --- Get Stack Data
$particle = new particledata();

# find each stack entry in database
$stackIds = $particle->getStackIds($sessionId);
foreach ($stackIds as $stackid) {
        echo divtitle("Stack Id: $stackid[stackid]");
	echo "<table border='0'>\n";
	# get list of stack parameters from database
        $s=$particle->getStackParams($stackid[stackid]);
	$nump=commafy($particle->getNumStackParticles($stackid[stackid]));
	# get pixel size of stack
	$apix=($particle->getPixelSizeFromStackId($stackid[stackid]))*1e10;
	$apix=($s['bin']) ? $apix*$s['bin'] : $apix;
	$apix.=" A/pixel";

	# get box size
	$boxsz=($s['bin']) ? $s['boxSize']/$s['bin'] : $s['boxSize'];
	$boxsz.=" pixels";

	$pflip = ($s['phaseFlipped']==1) ? "Yes" : "No";
	if ($s['aceCutoff']) $pflip.=" (ACE > $s[aceCutoff])";
	$display_keys['description']=$s['description'];
	$display_keys['# prtls']=$nump;
	$display_keys['path']=$s['stackPath'];
	$display_keys['name']=$s['name'];
	$display_keys['box size']=$boxsz;
	$display_keys['pixel size']=$apix;
	$display_keys['phase flipped']=$pflip;
	if ($s['selexonCutoff']) $display_keys['selexon min']=$s['selexonCutoff'];
	if ($s['minDefocus']) $display_keys['min defocus']=$s['minDefocus'];
	if ($s['maxDefocus']) $display_keys['max defocus']=$s['maxDefocus'];
	$display_keys['density']=($s['inverted']==1) ? 'light on dark background':'dark on light background';
	$display_keys['file type']=$s['fileType'];
	foreach($display_keys as $k=>$v) {
	        echo formatHtmlRow($k,$v);
	}
	echo"</TABLE>\n";
	echo"<P>\n";
}
writeBottom();
?>
