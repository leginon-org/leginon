<?php
/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 *	Simple viewer to view a image using mrcmodule
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/processing.inc";

$expId = $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

processing_header("Selection of Template Stack","Selection of Template Stack Page", $javascript,False);

echo "<table border='1' class='tableborder' width='640'>\n";

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/template_stack_clsavgs.png' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='templateStackSummary.php?expId=$expId&type=clsavg'>Template Stacks from Class Averages</a></h3>\n";
echo "  Summary of the template stacks created from the alignment pipeline. These can be used to run "
	."IMAGIC common lines, or for IMAGIC Multi Reference Alignment."
	."<br/><br/>\n";
echo "</td></tr>\n";

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/template_stack_forwardproj.png' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='templateStackSummary.php?expId=$expId&type=forward'>Template Stacks from Forward Projections</a></h3>\n";
echo "  Summary of the template stacks created from forward projections of an already existing map. These "
	."are particularly useful for running IMAGIC Multi Reference Alignment, but can also be used for other "
	."template-based protocols. "
	."<br/><br/>\n";
echo "</td></tr>\n";

echo "</table>\n";
processing_footer();
exit;

