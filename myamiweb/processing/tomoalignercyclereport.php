<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
  
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

$projectId = getProjectId();

$javascript = "<script src='../js/viewer.js'></script>\n";
$javascript.= editTextJava();

processing_header("Alignment Iteration Report","Tilt Series Alignment Report Page", $javascript);

// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";

$particle = new particledata();
$runinfo = $particle->getTomoAlignmentInfo($alignId);
$refinedata = $particle->getProtomoAlignmentInfo($alignId);
// All alignment run have aligner record except when the tomogram is uploaded
$rundir = $runinfo['path'];
if ($refinedata) {
	$refnum = $refinedata[0]['imgref'];
	if ( !is_null($refnum)) $is_protomo = true;
	// I use this page for all aligner report so chances are there is no refinedata
	// Therefore the report can be either one cycle of an Protomo alignrun or the whole
	// imod align run depending on if reference number (unique to protomo) can be found
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
	if (hasPatternInArrayKeys($_POST,'/updateDesc/')) {
		foreach ($refinedata as $t)
			$particle->updateTableDescriptionAndHiding($_POST,'ApTomoAlignerParamsData',$t['alignerid']);
	}
	echo $particle->displayHidingOption($expId,$refinedata,$refinedata,$showhidden);
		//Report parameters
		$s = $refinedata[0];
	if ($is_protomo) {
		$title = "Alignment cycle parameters";
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
} else {
	$html .= "<p><a href='tomoalignmovie.php?aId=$alignId&expId=$expId'>Alignment Movie</a></p>";
	$html .= "<b>No Other Alignment Information</b><p>";
	echo $html;
}
processing_footer();
?>
