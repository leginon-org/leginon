<?php
/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
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
echo "  <h2>Automated Masking Procedures</h2>\n";
echo "  <h4>\n";
echo "    Region masks can be created on images using automated methods. Automatically created masks can be assesed manually to accept or reject the result.  " 
	."During stack creation, particle selections within the assessed masks will not be considered for creating the stack. \n";
echo "  </h4>\n";
echo "</td></tr>\n";
echo "</table>\n";


echo "<br/>\n";
echo "<table border='1' class='tableborder' width='640'>\n";

/*
** Auto Masking
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' width='64'>\n";
echo "</td><td>\n";
//echo "  <h3><a href='runAutoMasker.php?expId=$expId'>Auto Masking</a></h3>\n";
$form = "AutoMaskForm";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=$form'>Auto Masking</a></h3>\n";
echo " <p> This is the <a href='https://github.com/hbradlow/em_hole_finder'>
	em_hole_finder.</a>&nbsp;<img src='img/external.png'> "
	."Written by Henry Bradlow. This procedure computes masks of carbon holes in electron micrographs. "
	."</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";

/*
** DBSCAN Auto Masking
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' width='64'>\n";
echo "</td><td>\n";
//echo "  <h3><a href='runDBMaskAutoMasker.php?expId=$expId'>DB Mask Auto Masking</a></h3>\n";
$form = "DBMaskAutoMaskForm";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=$form'>DBSCAN Auto Masking</a></h3>\n";
echo " <p> Written by Jake Bruggeman. "
        ."</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";









/*
** Crud Finding
*/
echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runMaskMaker.php?expId=$expId'>Crud Finding</a></h3>\n";
echo "<p>This is one of the original projection-matching refinement protocols, as implemented in "
	."<a href='http://blake.bcm.tmc.edu/eman/eman1/'>EMAN.</a>&nbsp;<img src='img/external.png'> It has been successfully "
	."tested on many different samples. Within each iteration, the raw particles are classified according to the angular "
	."sampling of projection directions, then iteratively aligned within each class to reduce the model bias. "
	."Further classification and particle 'filtering' has been incorporated using a SPIDER protocol that identifies "
	."and removes the particles with the highest variance (and therefore least correspondence) in the class using the "
	."<a href='http://www.wadsworth.org/spider_doc/spider/docs/man/cas.html'>"
	."CA S</a>&nbsp;<img src='img/external.png'> correspondence analysis operation in spider."
	."</p>\n";
echo "</td></tr>\n";

echo "</table>\n";
processing_footer();
exit;

