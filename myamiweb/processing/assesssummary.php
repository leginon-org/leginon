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
$projectId=$_POST['projectId'];

$javascript="<script src='../js/viewer.js'></script>\n";

processing_header("Assessment Summary","Assessment Summary Page", $javascript);

echo"<form name='viewerform' method='POST' ACTION='$formAction'>
<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

$sessiondata=getSessionList($projectId,$sessionId);

// --- Get Stack Data
$particle = new particledata();

$totimgs = $particle->getNumImgsFromSessionId($sessionId);
$viewerimgs = $particle->getNumViewerPrefImages($sessionId);
$assessedimgs = $particle->getNumAssessedImages($sessionId);
$totalassessimgs = $particle->getNumTotalAssessImages($sessionId);

$rejectimgs = $particle->getNumRejectAssessedImages($sessionId);
$hiddenimgs = $particle->getNumHiddenImages($sessionId);
$totalrejectimgs = $particle->getNumTotalRejectImages($sessionId);

$keepimgs = $particle->getNumKeepAssessedImages($sessionId);
$exemplarimgs = $particle->getNumExemplarImages($sessionId);
$totalkeepimgs = $particle->getNumTotalKeepImages($sessionId);


echo "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
echo "<TR><td>Particle Picked Images: </TD><td>".$totimgs."</TD></tr>\n";
echo "<TR><TD COLSPAN='2' BGCOLOR='#CCCCCC'></TD></tr>";
echo "<TR><td>Assessed Images: </TD><td>".$assessedimgs." (".round(100.0*$assessedimgs/$totimgs,1)."%)</TD></tr>\n";
echo "<TR><td>Hidden/Exemplar Images: </TD><td>".$viewerimgs." (".round(100.0*$viewerimgs/$totimgs,1)."%)</TD></tr>\n";
echo "<TR><td><B>Total Assess Images:</B> </TD><td>".$totalassessimgs." (".round(100.0*$totalassessimgs/$totimgs,1)."%)</TD></tr>\n";
echo "<TR><TD COLSPAN='2' BGCOLOR='#CCCCCC'></TD></tr>";
echo "<TR><td>Rejected Images: </TD><td>".$rejectimgs." (".round(100.0*$rejectimgs/$totimgs,1)."%)</TD></tr>\n";
echo "<TR><td>Hidden Images: </TD><td>".$hiddenimgs." (".round(100.0*$hiddenimgs/$totimgs,1)."%)</TD></tr>\n";
echo "<TR><td><B>Total Rejected Images:</B> </TD><td>".$totalrejectimgs." (".round(100.0*$totalrejectimgs/$totimgs,1)."%)</TD></tr>\n";
echo "<TR><TD COLSPAN='2' BGCOLOR='#CCCCCC'></TD></tr>";
echo "<TR><td>Keep Images: </TD><td>".$keepimgs." (".round(100.0*$keepimgs/$totimgs,1)."%)</TD></tr>\n";
echo "<TR><td>Exemplar Images: </TD><td>".$exemplarimgs." (".round(100.0*$exemplarimgs/$totimgs,1)."%)</TD></tr>\n";
echo "<TR><td><B>Total Keep Images:</B> </TD><td>".$totalkeepimgs." (".round(100.0*$totalkeepimgs/$totimgs,1)."%)</TD></tr>\n";

echo "</table>";

processing_footer();
?>
