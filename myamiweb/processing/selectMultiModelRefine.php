<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/processing.inc";

$expId = $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

processing_header("Multi-Model Reconstruction Refinement Software Selection","Multi-Model Refinement Software Selection Page", $javascript,False);

// Selection Header
echo "<table border='0' width='640'>\n";
echo "<tr><td>\n";
echo "  <h2>Multi-Model Reconstruction Refinement Procedures</h2>\n";
echo "  <h4>\n";
echo "    Most initial models establish a preliminary sense of the overall shape of " 
	."the biological specimen. To reveal structural information that can answer specific "
	."biological questions, the model requires refining. In single particle analysis, a refinement "
	."is an iterative procedure, which sequentially aligns the raw particles, assign to them appropriate "
	."spatial orientations (Euler angles) by comparing them against the a model, and then back-projects "
	."them into 3D space to form a new model. Effectively, a full refinement takes as input a raw particle "
	."stack and an initial model and is usually carried out until no further improvement of the structure can "
	."be observed.\n";
echo "  </h4>\n";
echo "</td></tr>\n";
echo "</table>\n";


echo "<br/>\n";
echo "<table border='1' class='tableborder' width='640'>\n";


/*
** Xmipp Maximum Likelihood Reference Free Alignment
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/xmipp_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='selectStackForm.php?expId=$expId&method=xmippml3d&type=multi'>Xmipp 3DML Refinement</a></h3>\n";
echo " <p> this method is the most robust, but takes some time to complete."
	." It uses the "
	."<a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/MLalign2D'>Xmipp ml_align2d</a>"
	."&nbsp;<img src='img/external.png'>"
	." program to perform alignments. "
	."</p><p>\n"
	."This method is unbiased and very thorough, but also the slowest of the methods (~days). "
	."Maximum likelihood also does a course search, integer pixels shifts and ~5 degree angle increments, "
	."so it is best to get templates with this method and use ref-based alignment to get better alignment parameters" 
	."</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";



echo "</table>\n";
processing_footer();
exit;

