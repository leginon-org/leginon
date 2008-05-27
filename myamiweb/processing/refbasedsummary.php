<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	List of the reference-based alignment runs
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
$projectId=$_POST['projectId'];

$javascript="<script src='../js/viewer.js'></script>\n";

processing_header("Reference-Based Alignment Summary","Reference-Based Alignment Summary", $javascript);

echo"<form name='viewerform' method='POST' ACTION='$formAction'>
<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);
echo "</FORM>\n";

// --- Get Refali Data
$particle = new particledata();
$refaliIds = $particle->getRefAliIds($sessionId);
$refaliruns = count($refaliIds);

$stackIds = $particle->getStackIds($sessionId);
$stackruns=count($stackIds);

// --- list out the alignment runs
echo"<P>\n";
foreach ($refaliIds as $refid) {
  # get list of alignment parameters from database
  $r = $particle->getRefAliParams($refid['DEF_id']);
  $s = $particle->getStackParams($r['REF|ApStackData|stack']);
  $t = $particle->getTemplatesFromId($r['REF|ApTemplateImageData|refTemplate']);
	echo divtitle("REF ALIGN: <FONT class='aptitle'>".$r['name']
		."</FONT> (ID: <FONT class='aptitle'>".$refid[DEF_id]."</FONT>)");
  //echo divtitle("Refali Run Id: $refid[DEF_id]");
  // --- get iteration info
  $iters = $particle->getRefAliIters($refid['DEF_id']);
  $numiters = count($iters);
  
  echo "<TABLE BORDER='0'>\n";
  //$display_keys['name']=$r['name'];
  $display_keys['description'] = "<B>".$r['description']."</B>";
  $display_keys['time']=$r['DEF_timestamp'];
  $display_keys['path']=$r['path'];
  //$display_keys['template']=$t['path'].'/'.$t['templatename'];
  $display_keys['# particles']=$r['num_particles'];
  $display_keys['lp filt']=$r['lp']." &Aring;";
  $display_keys['mask diams']=$r['imask_diam']." <I>(in)</I> / ".$r['mask_diam']." <I>(out)</I>";
  $display_keys['xy search range']=$r['xysearch'];
  $display_keys['c-symmetry']=$r['csym'];
  $display_keys['stack run name']=$s['shownstackname'];

  foreach($display_keys as $k=>$v) {
    echo formatHtmlRow($k,$v);
  }
  echo "<TR><TD BGCOLOR='#FFCCCC' COLSPAN=2>
    $numiters iterations: &nbsp;&nbsp;&nbsp;
    <A HREF='refbasediters.php?refaliId=$refid[DEF_id]'>View Iterations</a>
    </TD></TR>";
  echo"</TABLE>\n";
  echo "</FORM>\n";
  echo"<P>\n";
}

processing_footer();
?>
