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

session_destroy();
$expId = $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

processing_header("More Tilt-Series Processing","More Tilt-Series Processing Page", $javascript,False);

// Selection Header
echo "<table border='0' width='640'>\n";
echo "<tr><td>\n";
echo "  <h2>Additional Tilt-Series and Tomogram Procedures</h2>\n";
echo "  <h4>\n";
echo "    Here you will find additional tools for further processing of \n"
	."your tilt-series and tomography data.";
echo "</td></tr>\n";
echo "</table>\n";


echo "<br/>\n";
echo "<table border='1' class='tableborder' width='640'>\n";

/*
** TomoCTF Defocus Estimation
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <a href='runAppionLoop.php?expId=$expId&form=Protomo2TomoCTFEstimate'><img src='img/tomoctf.png' width='120'></a>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=Protomo2TomoCTFEstimate'>TomoCTF Defocus Estimation</a></h3>\n";
echo " <p> TomoCTF will estimate the defocus of the untilted plane of your tilt-series "
	."by tiling all tilt images and combining the power spectra."
	."<br/><br/>The <a href='http://www.sciencedirect.com/science/article/pii/S0304399106000222' target='_blank'> original research article is here</a>."
	."</p>\n";
echo "</td></tr>\n";

/*
** 3D DoG Picker
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <a href='runAppionLoop.php?expId=$expId&form=Protomo2TomoCTFEstimate'><img src='img/dogpicker.jpg' width='120'></a>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=Protomo23DDoGPicker'>3D DoG Picker</a></h3>\n";
echo " <p> This is an extension of Neil's 2D DoG picker to 3D. "
	."Requires tomogram(s) as input. Recommended binning: 8 or 4."
	."<br/><br/>The <a href='http://www.ncbi.nlm.nih.gov/pmc/articles/PMC2768396/' target='_blank'> original research article is here</a>."
	."</p>\n";
echo "</td></tr>\n";


echo "</table>\n";
processing_footer();
exit;

