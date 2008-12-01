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

processing_header("Particle Alignment Run","Particle Alignment Run Page", $javascript,False);

echo "<table border='1' class='tableborder'>";

#echo "<tr><td>";
#echo "  <h3>Just run an alignment, I don't care how</h3>";
#echo "</td></tr>";

echo "<tr><td>";
echo "  <h3><a href='runMaxLikeAlign.php?expId=$expId'>Xmipp Maximum Likeihood Alignment</a></h3>";
echo "  this method is the most robust, but takes some time to complete."
	." It uses the "
	."<a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/MLalign2D'>Xmipp ml_align2d</a>"
	."&nbsp;<img src='img/external.png'>"
	." program to perform alignments";
echo "</td></tr>";

echo "<tr><td>";
echo "  <h3><a href='runNoRefAlignment.php?expId=$expId'>Spider Reference-free Alignment</a></h3>";
echo "  this method uses the "
	."<a href='http://www.wadsworth.org/spider_doc/spider/docs/man/apsr.html'>Spider AP SR</a>"
	."&nbsp;<img src='img/external.png'>"
	." command to align your particles";
echo "</td></tr>";

echo "<tr><td>";
echo "  <h3><a href='runRefBasedAlignment.php?expId=$expId'>Spider Reference-based Alignment</a></h3>";
echo "  first you select template and then this method uses the "
	."<a href='http://www.wadsworth.org/spider_doc/spider/docs/man/apmq.html'>Spider AP MQ</a>"
	."&nbsp;<img src='img/external.png'>"
	." command to align your particles to the selected templates";
echo "</td></tr>";

echo "</table>";
processing_footer();
exit;

