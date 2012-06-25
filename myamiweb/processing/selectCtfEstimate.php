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

processing_header("CTF Estimation Selection","CTF Estimation Selection Page", $javascript,False);

// Selection Header
echo "<table border='0' width='640'>\n";
echo "<tr><td>\n";
echo "  <h2>CTF Estimation Procedures</h2>\n";
echo "  <h4>\n";
echo "    During CTF estimation the goal is to fit the \n"
	."<a href='http://en.wikipedia.org/wiki/Contrast_transfer_function'>\n"
	."standard CTF equation</a> to the power spectra of the electron micrographs\n";
echo "  </h4>\n";
echo "</td></tr>\n";
echo "</table>\n";


echo "<br/>\n";
echo "<table border='1' class='tableborder' width='640'>\n";

/*
** ACE 2
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAce2.php?expId=25'>ACE 2</a></h3>\n";
echo " <p> ACE 2 is re-implementation of ACE1, but written in objective-C "
	."ACE2 make several improvements over ACE1 including a several speed "
	."enhancements and a robust astigmatism estimate.<br/> "
	."<i>Note:</i> It was designed "
	."around FEI Tecnai FEG data and other have reported problems using this program";
echo "</td></tr>\n";

/*
** CTFFIND and CTFTILT
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/grigorieff_sq_logo.png' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runCtfEstimate.php?expId=25'>CTFFIND and CTFTILT</a></h3>\n";
echo " <p>CTFFIND and CTFTILT use a robust grid search algorithm to find the optimal "
	."CTF parameters. Please see the <a href='http://emlab.rose2.brandeis.edu/ctf'> "
	."Grigorieff lab website</a><img src='img/external.png'> for more information. "
	."</p>\n";
echo "</td></tr>\n";

/*
** ACE 1
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runPyAce.php?expId=$expId'>ACE 1</a></h3>\n";
echo " <p> ACE1 is the original edge detection program for finding the CTF "
	." parameters. Astigmatism estimation never worked quite right in ACE1 and it "
	." has a tendency to give false positives, i.e., a high confidence for a poor fit, "
	." because it will sometimes only try to fit 2 peaks in the powerspectrum. "
	." Nonetheless, ACE1 has been shown to work on a variety of microscopes and imaging methods. "
	."<br/><i>Note:</i> requires MATLAB. "
	."</p>\n";
echo "</td></tr>\n";


/*
** Xmipp CTF
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/xmipp_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runXmippCtf.php?expId=$expId'>Xmipp CTF</a></h3>\n";
echo " <p> this method builds a hierarchical classification of particles"
	." It uses the "
	."<a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/ClassAverages'>Xmipp cl2d</a>"
	."&nbsp;<img src='img/external.png'>"
	." program to perform alignments. "
	."It is a relatively fast method that aligns and classify the images at the same time. "
	."<br/><i>Note:</i> still under development for Appion. "
	."<br/><i>Note:</i> the published ARMA method is disabled. "
	."</p>\n";
echo "</td></tr>\n";


echo "</table>\n";
processing_footer();
exit;

