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
#require "inc/displaytables.inc";

$expId = $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

processing_header("Particle Alignment Selection","Particle Alignment Selection Page", $javascript,False);

// Selection Header
echo "<table border='0' width='640'>\n";
echo "<tr><td>\n";
echo "  <h2>Particle Alignment Procedures</h2>\n";
echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "  <h4>\n";
echo "    Particle alignment consists of shift, rotation, and mirror transformations for all"
		." particles in a stack to a common orientation or template. "
		." The reference free methods are great methods to create a template"
		."for particle picking or reference-based alignments.\n";
echo "  </h4>\n";
echo "</td></tr>\n";
echo "</table>\n";


echo "<br/>\n";
echo "<table border='1' class='tableborder' width='640'>\n";

#echo "<tr><td>\n";
#echo "  <h3>Just run an alignment, I don't care how</h3>\n";
#echo "</td></tr>\n";

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/xmipp_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runMaxLikeAlign.php?expId=$expId'>Xmipp Maximum Likeihood Alignment</a></h3>\n";
echo "  this method is the most robust, but takes some time to complete."
	." It uses the "
	."<a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/MLalign2D'>Xmipp ml_align2d</a>"
	."&nbsp;<img src='img/external.png'>"
	." program to perform alignments. This method is unbiased and very thorough, but also the slowest of the methods"
	."<br/><br/>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/spider_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runRefBasedAlignment.php?expId=$expId'>Spider Reference-based Alignment</a></h3>\n";
echo "  first you select template and then this method uses the "
	."<a href='http://www.wadsworth.org/spider_doc/spider/docs/man/apmq.html'>Spider AP MQ</a>"
	."&nbsp;<img src='img/external.png'>"
	." command to align your particles to the selected templates. Multiprocessing additions has made this very fast."
	."<br/><br/>\n";
//echo "  <img src='img/align-rsm.png' width='125'><br/>\n";
echo "</td></tr>\n";

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/imagic_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='multiReferenceAlignment.php?expId=$expId'>IMAGIC Multi Reference Alignment (MRA)</a></h3>\n";
echo "  this method uses the "
        ."<a href='http://www.imagescience.de/smi/index.htm'>IMAGIC m-r-a</a>"
        ."&nbsp;<img src='img/external.png'>"
        ." command to align your particles to the templates within a specified template stack"
        ."<br/><br/>\n";
echo "</td></tr>\n";

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/spider_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runSpiderNoRefAlignment.php?expId=$expId'>Spider Reference-free Alignment</a></h3>\n";
echo "  this method uses the "
	."<a href='http://www.wadsworth.org/spider_doc/spider/docs/man/apsr.html'>Spider AP SR</a>"
	."&nbsp;<img src='img/external.png'>"
	." command to align your particles. This method is very quick, but also very sloppy. "
	."It is best to run several times and compare the results."
	."<br/><br/>\n";
//echo "  <img src='img/align-rsm.png' width='125'><br/>\n";
echo "</td></tr>\n";

echo "</table>\n";
processing_footer();
exit;

