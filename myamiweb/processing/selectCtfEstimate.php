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

processing_header("CTF Estimation Selection","CTF Estimation Selection Page", $javascript,False);

// Selection Header
echo "<table border='0' width='640'>\n";
echo "<tr><td>\n";
echo "  <h2>CTF Estimation Procedures</h2>\n";
echo "  <h4>\n";
echo "    During CTF estimation the goal is to fit the \n"
	."<a href='http://en.wikipedia.org/wiki/Contrast_transfer_function'>\n"
	."standard CTF equation</a> "
	."<font size='-2'>(wikipedia)&nbsp;<img src='img/external.png'></font>\n"
	."to the power spectra of the electron micrographs\n";
echo "  </h4>\n";
echo "</td></tr>\n";
echo "</table>\n";


echo "<br/>\n";
echo "<table border='1' class='tableborder' width='640'>\n";

/*
** CTFFIND and CTFTILT
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/grigorieff_sq_logo.png' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runCtfEstimate.php?expId=$expId'>CTFFIND v3</a></h3>\n";
echo " <p>CTFFIND uses a robust grid search algorithm to find the optimal "
	."CTF parameters. Please see the <a href='http://grigoriefflab.janelia.org/ctf'> "
	."Grigorieff lab website</a>&nbsp;<img src='img/external.png'> for more information. "
	."</p>\n";
echo "</td></tr>\n";

/*
** CTFFIND4
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/grigorieff_sq_logo.png' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=CtfFind4'>CTFFIND v4</a></h3>\n";
echo " <p>CTFFIND uses a robust grid search algorithm to find the optimal "
	."CTF parameters. Please see the <a href='http://grigoriefflab.janelia.org/ctf'> "
	."Grigorieff lab website</a>&nbsp;<img src='img/external.png'> for more information. "
	."</p>\n";
echo "</td></tr>\n";

/*
** ACE 2
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAce2.php?expId=$expId'>ACE 2</a></h3>\n";
echo " <p> ACE 2 is an unpublished re-implementation of ACE1, but written in objective-C "
	."ACE2 make several improvements over ACE1 including a several speed "
	."enhancements and a robust astigmatism estimate.<br/> "
	."<i>Note:</i> It was designed "
	."around FEI Tecnai FEG data and other have reported problems using this program";
echo "</td></tr>\n";

/*
** ACE 1
*/
if (!HIDE_MATLAB)
{
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
}


/*
** Phasor CTF
*/

echo "<tr><td width='100' align='center'>\n";
		echo "  <img src='img/PhasorCTF.png' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runPhasorCtf.php?expId=$expId'>Phasor CTF</a></h3>\n";
echo " <p>Phasor is a kitchen sink program. It tries several different methods "
	." to find the CTF from ACE1/2 and CTFFIND and uses the result with the highest "
	." resolution"
	."</p>\n";
echo "</td></tr>\n";

/*
** CTF Refine
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/CTF_Refine_Logo.png' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runCtfRefine.php?expId=$expId'>CTF Refine</a></h3>\n";
$simplexUrl = "http://en.wikipedia.org/wiki/Simplex_algorithm";
echo " <p>Uses the <a href='$simplexUrl'>simplex algorithm</a> to refine the 2d parameters of the CTF "
	." (i.e., the angle astigmatism and amount of astigmatism) and then keeps "
	."  the value with the highest CTF resolution "
	."</p>\n";
echo "</td></tr>\n";

/*
** Interactive CTF
*/

if (!HIDE_FEATURE)
{
	echo "<tr><td width='100' align='center'>\n";
			echo "  <img src='img/interactiveCtf_logo.png' width='96'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='runInteractCtf.php?expId=$expId'>Interactive CTF</a></h3>\n";
echo " <p> <b>Experimental</b> manual CTF estimation program, currently has way too many "
	."buttons and no documentation "
	."</p>\n";
	echo "</td></tr>\n";
}

/*
** Xmipp CTF
*/
if (!HIDE_FEATURE)
{
	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/xmipp_logo.png' width='64'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='runXmippCtf.php?expId=$expId'>Xmipp CTF</a></h3>\n";
	echo " <p> It uses the "
		."<a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/Ctf_estimate_from_micrograph_v3'>Xmipp Ctf Estimate</a>"
		."&nbsp;<img src='img/external.png'>"
		." program to search for the CTF parameters. "
		."<br/><i>Note:</i> still under development for Appion. "
		."<br/><i>Note:</i> the published ARMA method is disabled. "
		."</p>\n";
	echo "</td></tr>\n";
}

echo "</table>\n";

//CTFTilt Estimation works and uploads, but fails alot; there is a warning
if (!HIDE_FEATURE)
{
	$particle = new particledata();
	$maxangle = $particle->getMaxTiltAngle($expId);
	if ($maxangle > 5) {
		// Selection Header
		echo "<table border='0' width='640'>\n";
			echo "<tr><td>\n";
			echo "  <h2>CTF Estimation Procedures specialized for tilted images</h2>\n";
			echo "</td></tr>\n";
		echo "</table>\n";

		echo "<br/>\n";
		echo "<table border='1' class='tableborder' width='640'>\n";

			echo "<tr><td width='100' align='center'>\n";
			echo "  <img src='img/grigorieff_sq_logo.png' width='96'>\n";
			echo "</td><td>\n";
			echo "  <h3><a href='runCtfEstimate.php?expId=$expId&ctftilt=1'>CTFTILT</a></h3>\n";
			echo " <p>CTFTILT uses the same robust grid search algorithm to find the optimal "
				."CTF parameters, but also includes estimate of the tilt angle. "
				."Please see the <a href='http://grigoriefflab.janelia.org/ctf'> "
				."Grigorieff lab website</a><img src='img/external.png'> for more information. "
				."</p>\n";
			echo "</td></tr>\n";
		echo "</table>\n";
	}
}


processing_footer();
exit;

