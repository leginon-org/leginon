<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
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
echo "<table border='0' width='640'>\n";
echo "<tr><td>\n";
echo "  <h2>Particle Picking Programs</h2>\n";
echo "  <h4>\n";
echo "    Particle picking consists of providing a x,y coordinates of "
		." objects from a micrograph. The usually fall into four categories: "
		." (1) template picking, (2) mathematical function, (3) machine learning, "
		." (4) manual picking\n";
echo "  </h4>\n";
echo "</td></tr>\n";
echo "</table>\n";


echo "<br/>\n";
echo "<table border='1' class='tableborder' width='640'>\n";

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
echo " <p> This picker simply tries to pick circular objects with high contrast in the image"
	." using the mathematical function called the "
	."<a href='https://en.wikipedia.org/wiki/Difference_of_Gaussians'>Difference of "
	."Gaussians (DoG) method</a>&nbsp;<img src='img/external.png'>. "
	."<br/><br/>The <a href='http://www.ncbi.nlm.nih.gov/pmc/articles/PMC2768396/'> original research article is here</a>."
	."</p>\n";
	
echo "</td></tr>\n";

/*
** FindEM Template Picking
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/findem.png' height='48'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=TemplatePickerForm'>FindEM Template Picking</a></h3>\n";
echo " <p> FindEM was largely considered the winner of the 2003 particle picking challenge. "
	." It uses the fast local correlation function (FLCF), which has been re-implemented in many "
	." other particle picking programs. (Note: Neil Voss has made some significant changes to the original "
	." FindEM so it runs faster in Appion.)"
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
echo " <p> A manual picker was create for editing existing picks or picking particles from scratch. "
	."It uses the familiar Leginon image viewer to display images and allow users to manually click "
	."on objects in the images."
	."</p>\n";
	
echo "</td></tr>\n";

/*
** DoG Picker 2
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/dogpicker2.jpg' height='100'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=DogPicker2Form'>DoG Picker 2</a></h3>\n";
echo " <p> This is an updated version of DoG picker that runs the same dog picker, but instead of "
	." thresholding the difference of Gaussians map it does an additional cross-correlation of the map "
	." to a circle of the picking size. Neil found out that this provides more consistent picking "
	." in data sets with a variety of situations, most commonly high density objects (e.g., crud, "
	." ice chucks) appear in some micrographs but not others. "
	."</p>\n";
	
echo "</td></tr>\n";

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
// It should be hidden until it can be tested at AMI. The HIDE_FEATURE flag can be set
// in config.php in the myamiweb directory.
if (!HIDE_FEATURE)
{
	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/signature.jpg' height='50'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='runSignature.php?expId=$expId'>Signature</a></h3>\n";
	echo " <p> Signature employs a hierarchical screening procedure to identify molecular particles "
		."<br/><br/>The <a href='http://dx.doi.org/10.1016/j.jsb.2006.06.001'> original research article is here</a>."
		."</p>\n";
	echo "</td></tr>\n";
}

/*
** Tilt Pickers
*/
$maxangle = $particle->getMaxTiltAngle($sessionId);
if ($maxangle > 5) {
	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/appionlogo.jpg' height='100'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='runTiltAligner.php?expId=$expId'>Tilt Picker</a></h3>\n";
	echo " <p> Tilt Aligner is a manual tilt picker for RCT and OTR "
	."It uses the familiar Leginon image viewer to display images and allow users to manually click "
	."on objects in the images."	
	."<br/><br/>The <a href='http://www.ncbi.nlm.nih.gov/pmc/articles/PMC2768396/'> original research article is here</a>."
		."</p>\n";
	echo "</td></tr>\n";
	
	
	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/autotiltpicker.png' height='100'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='runTiltAutoAligner.php?expId=$expId'>Auto Tilt Aligner</a></h3>\n";
	echo " <p> Tilt Aligner is a automatic tilt picker for RCT and OTR "
	."Using particle picks from any of the untilted pickers above, auto tilt aligner will match "
	."particles between two micrographs"
	."<br/><br/>The <a href='http://www.ncbi.nlm.nih.gov/pmc/articles/PMC2768396/'> original research article is here</a>."
		."</p>\n";
	echo "</td></tr>\n";	

}

/*
** Appion Loop Again
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' height='100'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runLoopAgain.php?expId=$expId'>Repeat Picking from Another Session</a></h3>\n";
echo " <p> This tool is for when you have some particle picker settings used in another session and want to "
	." use the exact same parameters for a picker in the session."
	."</p>\n";
	
echo "</td></tr>\n";


echo "</table>\n";
processing_footer();
exit;

