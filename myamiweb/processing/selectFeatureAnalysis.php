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
$alignId = $_GET['alignId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId&alignId=$alignId";

processing_header("Feature Analysis Selection","Feature Analysis Selection Page", $javascript,False);

// Selection Header
echo "<table border='0' width='640'>\n";
echo "<tr><td>\n";
echo "  <h2>Feature Analysis Procedures</h2>\n";
echo "  <h4>\n";
echo "    Feature analysis refers to systematic techniques for extracting features"
	." from a series of images or particles with the intent of clustering images with"
	." with similar features together."
	." Feature anaylsis is closely related to "
	."<a href='http://en.wikipedia.org/wiki/Multivariate_statistics'>multivariate statistics"
	."&nbsp;<img border='0' src='img/external.png'></a>."
	." All of these feature analysis techniques fall into two categories"
	." <a href='http://en.wikipedia.org/wiki/Principal_components_analysis'>principal component analysis (PCA)"
	."&nbsp;<img border='0' src='img/external.png'></a>"
	." (Spider Coran and IMAGIC MSA)."
	." and <a href='http://en.wikipedia.org/wiki/Artificial_neural_network'>neural networks"
	."&nbsp;<img border='0' src='img/external.png'></a>"
	." (Xmipp KerDen SOM).";
echo "  </h4>\n";
echo "</td></tr>\n";
echo "</table>\n";

echo "<br/>\n";

echo "<table border='1' class='tableborder' width='640'>";

#echo "<tr><td>";
#echo "  <h3>Just run an alignment, I don't care how</h3>";
#echo "</td></tr>";

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/spider_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runCoranClassify.php?expId=$expId&alignId=$alignId'>Spider Coran Classification</a></h3>";
echo "  this method uses the "
	."<a href='http://www.wadsworth.org/spider_doc/spider/docs/man/cas.html'>Spider CA S"
	."&nbsp;<img border='0' src='img/external.png'></a>"
	." to run correspondence analysis (coran), "
	." a form of <a href='http://en.wikipedia.org/wiki/Principal_components_analysis#Correspondence_analysis'>"
	."principal components analysis&nbsp;<img border='0' src='img/external.png'></a>, "
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
	."<a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/KerDenSOM'>Xmipp webpage"
	."&nbsp;<img border='0' src='img/external.png'></a>. "
	."<br/><br/>";
echo "</td></tr>";

//----IMAGIC Multivariate Statistical Analysis----//

if (!$HIDE_IMAGIC) {
	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/imagic_logo.png' width='64'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='imagicMSA.php?expId=$expId&alignId=$alignId'>IMAGIC Multivariate Statistical Analysis (MSA)</a></h3>";
	echo "  IMAGIC multivariate statistical analysis "
		."gives you the option of using one of 3 distance criteria for determining "
		."a set of eigenimages, and can remove  poor particles and class averages. For more information, visit "
		."<a href='http://www.imagescience.de/imagic/index.htm'>IMAGIC webpage"
		."&nbsp;<img border='0' src='img/external.png'></a></a>. "
	        ."<br/><br/>";
	echo "</td></tr>";
}

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/xmipp_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runRotKerDenSom.php?expId=$expId&alignId=$alignId'>Xmipp Rotational Kerden Self-Organizing Map</a></h3>";
echo "  This function applies the Kerden SOM to rotational symmetric particles. "
	."This is especially useful for classifying particles with difference cyclic symmetries."
	."For more information, please see the following "
	."<a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/RotationalSpectraClassification'>Xmipp webpage"
	."&nbsp;<img border='0' src='img/external.png'></a>. "
	."<br/><br/>";
echo "</td></tr>";


// ----Cluster by Affinity Propagation----//

// This feature works on small stacks but not large ones. 
if (!HIDE_FEATURE)
{
	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/affinityprop.png' width='64'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='runAffinityProp.php?expId=$expId&alignId=$alignId'>Cluster by Affinity Propagation</a></h3>";
	echo "  An algorithm that identifies exemplars among data points and forms clusters of data points"
		." around these exemplars. It operates by simultaneously considering all data point as potential"
		." exemplars and exchanging messages between data points until a good set of exemplars and "
		." clusters emerges, please see the following "
		."<a href='http://www.psi.toronto.edu/affinitypropagation/'>affinity propagation webpage"
		."&nbsp;<img border='0' src='img/external.png'></a> and "
		."<a href='http://www.psi.toronto.edu/affinitypropagation/faq.html'>FAQ"
		."&nbsp;<img border='0' src='img/external.png'></a>. "
		."<br/><br/>";
	echo "</td></tr>";
}

echo "</table>";

processing_footer();
exit;

