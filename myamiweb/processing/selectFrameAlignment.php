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
echo "    Direct detector movie frames can be aligned \n";
echo "  </h4>\n";
echo "</td></tr>\n";
echo "</table>\n";


echo "<br/>\n";
echo "<table border='1' class='tableborder' width='640'>\n";

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=motioncor2_ucsf'>MotionCor2</a></h3>\n";
echo " <p>MotionCor2 is an improved version of MotionCorr developed in David Agard lab at UCSF. The main new features are: (a) bad pixel correction from frames; (b) patch average support; (c) dose-weighted sum image output. The implementation here is based on the version released in August of 2016."
        ."</p>\n";
echo "</td></tr>\n";

/*
** MotionCorr - Purdue
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=MakeDDStackForm'>MotionCorr - Purdue</a></h3>\n";
echo " <p>MotionCorr - Purdue is a drift correction program contributed by Wen Jiang that extended the original MotionCorr written by Xueming Li with running sum average and frame flipping. See the <a href='https://github.com/jianglab/motioncorr'>Github repository</a>&nbsp; and <a href='http://jiang.bio.purdue.edu/'>"
	."Jiang lab website</a>&nbsp;<img src='img/external.png'> for more information. "
	."</p>\n";
echo "</td></tr>\n";

echo "</table>\n";

processing_footer();
exit;

