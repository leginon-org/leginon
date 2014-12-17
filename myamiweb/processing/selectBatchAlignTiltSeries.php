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

processing_header("Batch align Tilt Series","Batch align Tilt Series Page", $javascript,False);

// Selection Header
echo "<table border='0' width='640'>\n";
echo "<tr><td>\n";
echo "  <h2>Batch Tilt Series Alignment Procedures - Not Yet Implemented!</h2>\n";
echo "  <h4>\n";
echo "    Here you will find the same maintained software packages \n"
	."as in 'Align tilt series', but configured to run in \n"
	."batch mode. Select multiple tilt series that you wish to run in batch \n"
	."mode, input the parameters you wish to use in the alignment and \n"
	."reconstruction of the tilt series, and copy & paste the command into a terminal window. \n"
	."Batch mode tilt series alignment and reconstruction might be \n"
	."useful for quickly screening tilt series. \n";
echo "  </h4>\n";
echo "</td></tr>\n";
echo "</table>\n";


echo "<br/>\n";
echo "<table border='1' class='tableborder' width='640'>\n";

/*
** Protomo 2.4.1
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/protomo.png' width='120'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=Protomo2BatchForm'>Protomo 2.4.1</a></h3>\n";
echo " <p> Protomo is a software package used in electron tomography for marker-free alignment and 3D "
	."reconstruction of tilt series. The marker-free alignment is based on cross-correlation methods and "
	."projection matching. It also includes the refinement of geometric parameters of the tilt series. "
	."3D reconstruction is carried out by weighted back-projection with general weighting functions "
	."that allow varying tilt angle increments. ";
echo "</td></tr>\n";

/*
** eTomo 4.8.13 Dev.
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runEtomo.php?expId=$expId'>eTomo - Not Yet Implemented!</a></h3>\n";
echo " <p>Here eTomo is operated completely through the command line using batchruntomo. "
	."Batchruntomo runs all the operations required to align a tilt series and build a tomogram. "
	."Batchruntomo can work on more than one data set and can run on multiple local processors and GPUs. "
	."</p>\n";
echo "</td></tr>\n";


/*
** Old software
*/

echo "<tr><td width='100' align='center'>\n";
		echo "  <img src='img/other_software.png' width='125'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runTomoAligner.php?expId=$expId'>Other Software Packages</a></h3>\n";
echo " <p>Here you will find older and unmaintained software packages for aligning tilt series, "
	."including Leginon alignment, Protomo 1 refinement, and Imod shift-only alignment. "
	."</p>\n";
echo "</td></tr>\n";



echo "</table>\n";
processing_footer();
exit;

