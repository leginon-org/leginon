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
echo"	<table border=3 class=tableborder>
				<tr>
					<td valign='TOP'>\n";
			echo "<img border='0' src='tomoaligngraph.php?w=512&&h=256&aId=$alignId&expId=$expId&type=rot'><br/>\n";
echo"</td></tr><tr><td valign='TOP'>\n";
echo "<img border='0' src='tomoaligngraph.php?w=512&&h=256&aId=$alignId&expId=$expId&type=shiftx'><br/>\n";
echo"</td></tr><tr><td valign='TOP'>\n";
echo "<img border='0' src='tomoaligngraph.php?w=512&&h=256&aId=$alignId&expId=$expId&type=shifty'><br/>\n";
echo"</td></tr><tr><td valign='TOP'>\n";
echo "<a href='tomoalignmovie.php?aId=$alignId&expId=$expId'>Alignment Movie</a>";
echo "</table>\n";
if ($_POST) {
	foreach ($refinedata as $t)
		$particle->updateTableDescriptionAndHiding($_POST,'ApProtomoAlignerParamsData',$t['alignerid']);
}

echo $particle->displayHidingOption($expId,$refinedata,$refinedata,$showhidden);
	//Report parameters
	$s = $refinedata[0];
	$exclude_fields = array('DEF_id','DEF_timestamp','modelid','image','number','rotation','shift x','shift y');
	for ($i=1;$i < $s[count]; $i++) $exclude_fields[]=$i;
	$title = "Protomo alignment cycle parameters";
	$particle->displayParameters($title,$s,$exclude_fields,$expId);
	$html .= "<br>\n";
	echo $html;
echo $particle->displayHidingOption($expId,$allcycles,$showncycles,$showhidden);
// --- 

processing_footer();
?>
