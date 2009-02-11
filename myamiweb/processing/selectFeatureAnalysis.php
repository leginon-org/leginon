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
$alignId = $_GET['alignId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId&alignId=$alignId";

processing_header("Alignment Classify Run","Alignment Classify  Run Page", $javascript,False);

echo "<table border='1' class='tableborder' width='600'>";

#echo "<tr><td>";
#echo "  <h3>Just run an alignment, I don't care how</h3>";
#echo "</td></tr>";

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/spider_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runCoranClassify.php?expId=$expId&alignId=$alignId'>Spider Coran Classification</a></h3>";
echo "  this method uses the "
	."<a href='http://www.wadsworth.org/spider_doc/spider/docs/man/cas.html'>Spider CA S</a>"
	."&nbsp;<img src='img/external.png'>"
	." to run correspondence analysis (coran), "
	." a form of <a href='http://en.wikipedia.org/wiki/Principal_components_analysis'>"
	."Principal components analysis</a>&nbsp;<img src='img/external.png'>, "
	."and classify your aligned particles"
	."<br/><br/>";
echo "</td></tr>";

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/xmipp_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runKerDenSom.php?expId=$expId&alignId=$alignId'>Xmipp Kerden Self-Organizing Map</a></h3>";
echo "  Kerden SOM stands for 'Kernel Probability Density Estimator Self-Organizing Map'. "
	."It maps a set of high dimensional input vectors into a two-dimensional grid. "
	."For more information, please see the following "
	."<a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/KerDenSOM'>Xmipp webpage</a>. "
	."<br/><br/>";
echo "</td></tr>";

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/imagic_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='imagicMSA.php?expId=$expId&alignId=$alignId'>IMAGIC Multivariate Statistical Analysis (MSA)</a></h3>";
echo "  IMAGIC multivariate statistical analysis "
        ."gives you the option of using one of 3 distance criteria for determining "
	."a set of eigenimages, and can remove  poor particles and class averages. For more information, visit "
        ."<a href='http://www.imagescience.de/imagic/index.htm'>IMAGIC webpage</a>. "
        ."<br/><br/>";
echo "</td></tr>";

echo "</table>";

processing_footer();
exit;

