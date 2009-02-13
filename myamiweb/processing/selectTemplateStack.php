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

processing_header("Selection of Template Stack","Selection of Template Stack Page", $javascript,False);

echo "<table border='1' class='tableborder' width='640'>\n";

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/template_stack_clsavgs.png' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='templateStackSummaryClsAvg.php?expId=$expId'>Template Stacks from Class Averages</a></h3>\n";
echo "  Summary of the template stacks created from the alignment pipeline. These can be used to run "
	."IMAGIC common lines, or for IMAGIC Multi Reference Alignment."
	."<br/><br/>\n";
echo "</td></tr>\n";

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/template_stack_forwardproj.png' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='templateStackSummaryForward.php?expId=$expId'>Template Stacks from Forward Projections</a></h3>\n";
echo "  Summary of the template stacks created from forward projections of an already existing map. These "
	."are particularly useful for running IMAGIC Multi Reference Alignment, but can also be used for other "
	."template-based protocols. "
	."<br/><br/>\n";
echo "</td></tr>\n";

echo "</table>\n";
processing_footer();
exit;

