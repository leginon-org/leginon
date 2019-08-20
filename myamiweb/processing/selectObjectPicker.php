<?php
/**
 *	The Leginon software is Copyright under
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/processing.inc";

$particle = new particledata();
$expId = $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
$javascript = "";

processing_header("Select Particle Picker","Particle Picker Selection Page", $javascript, False);

// Selection Header
echo "<table border='0'>\n";
echo "<tr><td>\n";
echo "  <h2>Particle Picking Programs</h2>\n";
echo "  <h4>\n";
echo "    Particle picking consists of providing a x,y coordinates of "
		." objects from a micrograph. The usually fall into four categories:\n "
		." (1) template picking, (2) mathematical function, (3) machine learning, "
		." (4) manual picking\n";
echo "  </h4>\n";
echo "</td></tr>\n";
echo "</table>\n";


echo "<br/>\n";
echo "<table border='1' class='tableborder' style='white-space: normal' >\n";

/*
	if (!HIDE_FEATURE)
	{
		if ($cdone || $cadone) {
			$action = "Shape/Size Analysis";
			$nrun[] = array(
				'name'=>"<a href='analyzeTracedObject.php?expId=$sessionId'>Size analysis</a>",			);
		}
	}
*/

/*
** DoG Picker
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/dogpicker.jpg' height='100'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=DogPickerForm'>DoG Picker</a></h3>\n";
echo " <p> This picker simply tries to pick circular objects with high contrast in the image\n"
	." using the mathematical function called the "
	."<a href='https://en.wikipedia.org/wiki/Difference_of_Gaussians'>Difference of "
	."Gaussians (DoG) method</a>\n&nbsp;<img src='img/external.png'>. \n"
	."<br/><br/>The <a href='http://www.ncbi.nlm.nih.gov/pmc/articles/PMC2768396/'> original research article is here</a>."
	."</p>\n";

echo "</td></tr>\n";

/*
** DoG Picker 2
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/dogpicker2.jpg' height='100'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=DogPicker2Form'>DoG Picker 2</a></h3>\n";
echo " <p> This is an updated version of DoG picker that runs the same dog picker,\n but instead of "
	." thresholding the difference of Gaussians map it does an additional cross-correlation of the map "
	." to a circle of the picking size. \nNeil found out that this provides more consistent picking "
	." in data sets with a variety of situations,\n most commonly high density objects (e.g., crud, "
	." ice chucks)\n appear in some micrographs but not others.\n "
	."</p>\n";

echo "</td></tr>\n";

/*
** Gautomatch
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' height='100'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=gautomatchForm'>Gautomatch Picking</a></h3>\n";
echo " <p>  Gautomatch is a GPU accelerated program for accurate,\n fast, flexible and fully "
	."automatic particle picking from cryo‐EM micrographs with or without templates.\n</p>\n";

echo "</td></tr>\n";



/*
** FindEM Template Picking
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/findem.png' height='48'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=TemplatePickerForm'>FindEM Template Picking</a></h3>\n";
echo " <p> FindEM was largely considered the winner of the 2003 particle picking challenge. \n"
	." It uses the fast local correlation function (FLCF),\n which has been re-implemented in many "
	." other particle picking programs. \n(Note: Neil Voss has made some significant changes to the original "
	." FindEM so it runs faster in Appion.)\n"
	."<br/><br/>The <a href='http://www.ncbi.nlm.nih.gov/pubmed/15065677'> original research abstract is here</a>."
	."</p>\n";

echo "</td></tr>\n";

/*
** Appion Manual Picker
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' height='100'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runManualPicker.php?expId=$expId'>Appion Manual Picker</a></h3>\n";
echo " <p> A manual picker was create for editing existing picks or picking particles from scratch.\n "
	."It uses the familiar Leginon image viewer to display images and allow users to manually click "
	."on objects in the images.\n"
	."</p>\n";

echo "</td></tr>\n";




/*
** Tilt Pickers
*/
$maxangle = $particle->getMaxTiltAngle($expId);
if ($maxangle > 5) {
	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/appionlogo.jpg' height='100'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='runTiltAligner.php?expId=$expId'>Tilt Picker</a></h3>\n";
	echo " <p> Tilt Aligner is a manual tilt picker for RCT and OTR "
	."It uses the familiar Leginon image viewer to display images and allow users to manually click "
	."on objects in the images.\n"
	."<br/><br/>The <a href='http://www.ncbi.nlm.nih.gov/pmc/articles/PMC2768396/'> original research article is here</a>."
		."</p>\n";
	echo "</td></tr>\n";


	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/autotiltpicker.png' height='100'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='runTiltAutoAligner.php?expId=$expId'>Auto Tilt Aligner</a></h3>\n";
	echo " <p> Tilt Aligner is a automatic tilt picker for RCT and OTR.\n "
	."Using particle picks from any of the untilted pickers above,\n auto tilt aligner will match "
	."particles between two micrographs.\n"
	."<br/><br/>The <a href='http://www.ncbi.nlm.nih.gov/pmc/articles/PMC2768396/'> original research article is here</a>."
		."</p>\n";
	echo "</td></tr>\n";

}

/*
** Contour Picker
*/
if (!HIDE_FEATURE)
{
	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/appionlogo.jpg' height='100'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='runContourPicker.php?expId=$expId'>Object Tracing</a></h3>\n";
	echo " <p> "
		."</p>\n";
	echo "</td></tr>\n";
}

// The signature feature is added with issue #368, however was not tested prior to 2.0 release.
// It is no longer supported

/*
** Appion Loop Again
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' height='100'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runLoopAgain.php?expId=$expId'>Repeat Picking from Another Session</a></h3>\n";
echo " <p> This tool is for when you have some particle picker settings used in another session\n and want to "
	." use the exact same parameters for a picker in the session.\n"
	."</p>\n";

echo "</td></tr>\n";


echo "</table>\n";
processing_footer();
exit;

