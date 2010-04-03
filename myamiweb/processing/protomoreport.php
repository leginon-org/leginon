<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
  
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
$alignId = $_GET['aId'];
if ($alignId) $formAction.="&aId=$alignId";

if ($_GET['showHidden']) {
	$showhidden = True;
	$formAction.="&showHidden=1";
}

$projectId = (int) getProjectFromExpId($expId);

$javascript = "<script src='../js/viewer.js'></script>\n";
$javascript.= editTextJava();

processing_header("Protomo Alignment Iteration Report","Tilt Series Alignment Report Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

$particle = new particledata();
$runinfo = $particle->getTomoAlignmentInfo($alignId);
$refinedata = $particle->getProtomoAlignmentInfo($alignId);
$rundir = $runinfo['path'];
$refnum = $refinedata[0]['imgref'];
// I use this page for all aligner report so chances are there is no refinedata
// Therefore the report can be either one cycle of an Protomo alignrun or the whole
// imod align run depending on if reference number (unique to protomo) can be found
if ( !is_null($refnum)) $is_protomo = true;
$refnum = (int) ($refnum);
echo"	<table border=3 class=tableborder>";
echo"<tr><td valign='TOP'>\n";
echo "<a href='tomoalignmovie.php?aId=$alignId&expId=$expId'>Alignment Movie</a>";
echo"</td></tr><tr><td valign='TOP'>\n";
echo "<img border='0' src='tomoaligngraph.php?w=512&&h=256&aId=$alignId&expId=$expId&ref=$refnum&type=rot'><br/>\n";
echo"</td></tr><tr><td valign='TOP'>\n";
echo "<img border='0' src='tomoaligngraph.php?w=512&&h=256&aId=$alignId&expId=$expId&ref=$refnum&type=shiftx'><br/>\n";
echo"</td></tr><tr><td valign='TOP'>\n";
echo "<img border='0' src='tomoaligngraph.php?w=512&&h=256&aId=$alignId&expId=$expId&ref=$refnum&type=shifty'><br/>\n";

echo"</td></tr>\n";
echo "</table>\n";
if ($_POST) {
	foreach ($refinedata as $t)
		$particle->updateTableDescriptionAndHiding($_POST,'ApTomoAlignerParamsData',$t['alignerid']);
}
echo $particle->displayHidingOption($expId,$refinedata,$refinedata,$showhidden);
	//Report parameters
	$s = $refinedata[0];
if ($is_protomo) {
	$title = "Protomo alignment cycle parameters";
} else {
	$title = "Alignment parameters";
}
$exclude_fields = array('DEF_id','DEF_timestamp','modelid','image','number','rotation','shift x','shift y');
for ($i=1;$i < $s[count]; $i++) $exclude_fields[]=$i;
$particle->displayParameters($title,$s,$exclude_fields,$expId);
$html .= "<br>\n";
echo $html;
echo $particle->displayHidingOption($expId,$allcycles,$showncycles,$showhidden);
// --- 

processing_footer();
?>
