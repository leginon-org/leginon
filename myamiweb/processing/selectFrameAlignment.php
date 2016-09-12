<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/processing.inc";

$expId = $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

processing_header("Drift Correction Selection","Frame Alignment Selection", $javascript,False);

// Selection Header
echo "<table border='0' width='640'>\n";
echo "<tr><td>\n";
echo "  <h2>Drift Correction and Frame Alignment Procedures</h2>\n";
echo "  <h4>\n";
echo "    Raw frames need to aligned. More in this section coming soon.\n";
echo "</td></tr>\n";
echo "</table>\n";


echo "<br/>\n";
echo "<table border='1' class='tableborder' width='640'>\n";

/*
** MotionCorr - Purdue
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=MakeDDStackForm'>MotionCorr - Purdue</a></h3>\n";
echo " <p>MotionCorr - Purdue is a poorly named drift correction program based on the official MotionCorr2 beta release. See the <a href='https://github.com/jianglab/motioncorr'>Github repository</a>&nbsp; and <a href='http://jiang.bio.purdue.edu/'>"
	."Jiang lab website</a>&nbsp;<img src='img/external.png'> for more information. "
	."</p>\n";
echo "</td></tr>\n";

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=motioncorr2_ucsf'>MotionCorr2 - UCSF</a></h3>\n";
echo " <p>MotionCorr2 - UCSF is the David Agard version of MotionCorr developed in Yifan Cheng's lab at UCSF. It is still in beta and subject to change."
        ."</p>\n";
echo "</td></tr>\n";



processing_footer();
exit;

