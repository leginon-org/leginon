
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

writeTop("NoRef Class Report","Reference-free Classification Summary Page", $javascript);

echo"<form name='viewerform' method='POST' ACTION='$formAction'>
<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
echo "</FORM>\n";

// --- Get NoRef Data
$particle = new particledata();

# find each noref entry in database
$norefIds = $particle->getNoRefIds($sessionId);
$norefruns=count($norefIds);

foreach ($norefIds as $norefid) {
	//print_r ($norefid);
	echo divtitle("NoRef Id: $norefid[DEF_id]");

	# get list of noref parameters from database
	$s = $particle->getNoRefParams($norefid['DEF_id']);

	echo "<table border='0' >\n";
	foreach($s as $k=>$v) {
		echo formatHtmlRow($k,$v);
	}

	$norefpath = $s[norefPath].$s[name]."/";

	$classIds = $particle->getNoRefClassRuns($norefid['DEF_id']);
	$classnum = count($classIds);
	foreach ($classIds as $classid) {
		$classfile = $norefpath.$classid[classFile].".img";
		$totimg = $classid[num_classes];
		$endimg = $classid[num_classes]-1;
		echo "
		<tr><td bgcolor='#ffcccc' colspan=2>
			Averaged into $totimg classes: &nbsp;&nbsp;&nbsp;
			<a href='viewstack.php?file=$classfile&endimg=$endimg'>View Class Averages</a>
		</td></tr>";
		//echo "<tr><td bgcolor='#ff4444'>"; print_r ($classid); echo "</td></tr>";
		//foreach($classid as $k=>$v) {
		//	echo formatHtmlRow($k,$v);
		//}
	}
/*
	$display_keys['description']=$s['description'];
	$display_keys['path']=$s['norefPath'];
	$display_keys['name']=$s['name'];
	$display_keys['lp filt']=$s['lp_filt'];
	foreach($display_keys as $k=>$v) {
	        echo formatHtmlRow($k,$v);
	}
*/
	echo"</TABLE>\n";
	echo"<P>\n";
}
writeBottom();
?>
