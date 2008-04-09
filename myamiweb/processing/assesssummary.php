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

writeTop("Assessment Summary","Assessment Summary Page", $javascript);

echo"<form name='viewerform' method='POST' ACTION='$formAction'>
<INPUT TYPE='HIDDEN' NAME='lastSessionId' VALUE='$sessionId'>\n";

$sessiondata=displayExperimentForm($projectId,$sessionId,$expId);

// --- Get Stack Data
$particle = new particledata();

echo"<P>\n";
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
echo "<TR><TD>Particle Picked Images: </TD><TD>".$totimgs."</TD></TR>\n";
echo "<TR><TD COLSPAN='2' BGCOLOR='#CCCCCC'></TD></TR>";
echo "<TR><TD>Assessed Images: </TD><TD>".$assessedimgs." (".round(100.0*$assessedimgs/$totimgs,1)."%)</TD></TR>\n";
echo "<TR><TD>Hidden/Exemplar Images: </TD><TD>".$viewerimgs." (".round(100.0*$viewerimgs/$totimgs,1)."%)</TD></TR>\n";
echo "<TR><TD><B>Total Assess Images:</B> </TD><TD>".$totalassessimgs." (".round(100.0*$totalassessimgs/$totimgs,1)."%)</TD></TR>\n";
echo "<TR><TD COLSPAN='2' BGCOLOR='#CCCCCC'></TD></TR>";
echo "<TR><TD>Rejected Images: </TD><TD>".$rejectimgs." (".round(100.0*$rejectimgs/$totimgs,1)."%)</TD></TR>\n";
echo "<TR><TD>Hidden Images: </TD><TD>".$hiddenimgs." (".round(100.0*$hiddenimgs/$totimgs,1)."%)</TD></TR>\n";
echo "<TR><TD><B>Total Rejected Images:</B> </TD><TD>".$totalrejectimgs." (".round(100.0*$totalrejectimgs/$totimgs,1)."%)</TD></TR>\n";
echo "<TR><TD COLSPAN='2' BGCOLOR='#CCCCCC'></TD></TR>";
echo "<TR><TD>Keep Images: </TD><TD>".$keepimgs." (".round(100.0*$keepimgs/$totimgs,1)."%)</TD></TR>\n";
echo "<TR><TD>Exemplar Images: </TD><TD>".$exemplarimgs." (".round(100.0*$exemplarimgs/$totimgs,1)."%)</TD></TR>\n";
echo "<TR><TD><B>Total Keep Images:</B> </TD><TD>".$totalkeepimgs." (".round(100.0*$totalkeepimgs/$totimgs,1)."%)</TD></TR>\n";

echo "</TABLE>";

writeBottom();
?>
