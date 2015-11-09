<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	refinement selection form
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/processing.inc";

$expId = $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

processing_header("Automated Masking Software Selection","Automated Masking Software Selection", $javascript,False);

// Selection Header
echo "<table border='0' width='640'>\n";
echo "<tr><td>\n";
echo "  <h2>Local Classification Procedures</h2>\n";
echo "  <h4>\n";
echo "This tool is used to discover local change of structure of particle image or volume set";
echo "  </h4>\n";
echo "</td></tr>\n";
echo "</table>\n";


echo "<br/>\n";
echo "<table border='1' class='tableborder' width='640'>\n";

/*
** Maskiton
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='maskiton.php?expId=$expId'>Maskiton</a></h3>\n";
echo " <p> This is the <a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/ProjectionMatchingRefinement'>
	Xmipp projection-matching refinement protocol.</a>&nbsp;<img src='img/external.png'> The classification of "
	."raw particles is done using the <a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/Projection_matching'>
	angular projection matching</a>&nbsp;<img src='img/external.png'>&nbsp;"
	."operation in Xmipp. The user is given the option of employing an algebraic reconstruction technique "
	."(ART), weighted back-projection (WBP) or Fourier interpolation method to recontruct the computed classes from "
	."projection-matching. One big advantage to this protocol is speed. Because all Euler angle and alignment parameters "
	."are saved for each iteration of angular projection-matching, the later iterations localize the search space "
	."to an increasingly narrow region and, therefore, take significantly less cpu time to complete. "
	."</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";

echo "</table>\n";
processing_footer();
exit;

