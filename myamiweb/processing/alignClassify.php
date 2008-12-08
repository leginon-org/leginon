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
$alignId = $_GET['$alignId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId&alignId=$alignId";

processing_header("Alignment Classify Run","Alignment Classify  Run Page", $javascript,False);

echo "<table border='1' class='tableborder' width='600'>";

#echo "<tr><td>";
#echo "  <h3>Just run an alignment, I don't care how</h3>";
#echo "</td></tr>";

echo "<tr><td>";
echo "  <h3><a href='runCoranClassify.php?expId=$expId&alignId=$alignId'>Spider Coran Classification</a></h3>";
echo "  this method uses the "
	."<a href='http://www.wadsworth.org/spider_doc/spider/docs/man/cas.html'>Spider CA S</a>"
	."&nbsp;<img src='img/external.png'>"
	." to run correspondence analysis (coran) "
	.", a form of <a href='http://en.wikipedia.org/wiki/Principal_components_analysis'>"
	."Principal components analysis</a>&nbsp;<img src='img/external.png'>, "
	."and classify your aligned particles";
echo "</td></tr>";


echo "</table>";
processing_footer();
exit;

