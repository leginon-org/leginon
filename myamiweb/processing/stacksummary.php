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

$javascript="<script src='../js/viewer.js'></script>\n";

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
	$s=$particle->getStackParams($stackid[stackid]);
	echo divtitle("STACK: <FONT COLOR='#993333'>".$s['stackRunName']
		."</FONT> (ID: <FONT COLOR='#993333'>".$stackid[stackid]."</FONT>)");
	echo "<table border='0'>\n";
	# get list of stack parameters from database
	$nump=commafy($particle->getNumStackParticles($stackid[stackid]));
	# get pixel size of stack
	$apix=($particle->getStackPixelSizeFromStackId($stackid[stackid]))*1e10;
	$apix.=" &Aring;/pixel";
	$apix=format_angstrom_number($apix)."/pixel";

	# get box size
	$boxsz=($s['bin']) ? $s['boxSize']/$s['bin'] : $s['boxSize'];
	$boxsz.=" pixels";

	$pflip = ($s['phaseFlipped']==1) ? "Yes" : "No";
	if ($s['aceCutoff']) $pflip.=" (ACE > $s[aceCutoff])";
	$display_keys['description']=$s['description'];
	$display_keys['# prtls']=$nump;
	$stackfile = $s['path']."/".$s['name'];
	$display_keys['path']=$s['path'];
	$display_keys['name']="<A TARGET='stackview' HREF='viewstack.php?file=$stackfile'>".$s['name']."</A>";
	$display_keys['box size']=$boxsz;
	$display_keys['pixel size']=$apix;
	$display_keys['phase flipped']=$pflip;
	if ($s['correlationMin']) $display_keys['correlation min']=$s['correlationMin'];
	if ($s['correlationMax']) $display_keys['correlation max']=$s['correlationMax'];
	if ($s['minDefocus']) $display_keys['min defocus']=$s['minDefocus'];
	if ($s['maxDefocus']) $display_keys['max defocus']=$s['maxDefocus'];
	$display_keys['density']=($s['inverted']==1) ? 'light on dark background':'dark on light background';
	$display_keys['normalization']=($s['normalized']==1) ? 'On':'Off';
	$display_keys['file type']=$s['fileType'];
	foreach($display_keys as $k=>$v) {
	        echo formatHtmlRow($k,$v);
	}
	echo"</TABLE>\n";
	echo"<P>\n";
}
writeBottom();
?>
