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

processing_header("Reconstruction Refinement Software Selection","Refinement Software Selection Page", $javascript,False);

// Selection Header
echo "<table border='0' width='640'>\n";
echo "<tr><td>\n";
echo "  <h2>Reconstruction Refinement Procedures</h2>\n";
echo "  <h4>\n";
echo "    Most initial models establish a preliminary sense of the overall shape of " 
	."the biological specimen. To reveal structural information that can answer specific "
	."biological questions, the model requires refining. In single particle analysis, a refinement "
	."is an iterative procedure, which sequentially aligns the raw particles, assign to them appropriate "
	."spatial orientations (Euler angles) by comparing them against the a model, and then back-projects "
	."them into 3D space to form a new model. Effectively, a full refinement takes as input a raw particle "
	."stack and an initial model and is usually carried out until no further improvement of the structure can "
	."be observed.\n";
echo "  </h4>\n";
echo "</td></tr>\n";
echo "</table>\n";


echo "<br/>\n";
echo "<table border='1' class='tableborder' width='640'>\n";


/*
** Xmipp Maximum Likelihood Reference Free Alignment
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/xmipp_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='selectStackForm.php?expId=$expId&method=xmipp'>Xmipp Refinement</a></h3>\n";
echo " <p> this method is the most robust, but takes some time to complete."
	." It uses the "
	."<a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/MLalign2D'>Xmipp ml_align2d</a>"
	."&nbsp;<img src='img/external.png'>"
	." program to perform alignments. "
	."</p><p>\n"
	."This method is unbiased and very thorough, but also the slowest of the methods (~days). "
	."Maximum likelihood also does a course search, integer pixels shifts and ~5 degree angle increments, "
	."so it is best to get templates with this method and use ref-based alignment to get better alignment parameters" 
	."</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";

if (!HIDE_FEATURE)
{
	/*
	** SPIDER Reference Based Alignment
	*/
	
	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/spider_logo.png' width='64'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='selectStackForm.php?expId=$expId&method=spider'>Spider Refinement</a></h3>\n";
	echo " <p> first you select template and then this method uses the "
		."<a href='http://www.wadsworth.org/spider_doc/spider/docs/man/apmq.html'>Spider AP MQ</a>"
		."&nbsp;<img src='img/external.png'>"
		." command to align your particles to the selected templates. Multiprocessing additions has made this extremely fast (~1 hour)."
		."</p>\n";
	//echo "  <img src='img/align-rsm.png' width='125'><br/>\n";
	echo "</td></tr>\n";
}

if (!HIDE_IMAGIC && !HIDE_FEATURE) {
	/*
	** IMAGIC Reference Based Alignment
	*/

	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/imagic_logo.png' width='64'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='selectStackForm.php?expId=$expId&method=imagic'>IMAGIC Refinement</a></h3>\n";
	echo " <p> this method uses the "
		."<a href='http://www.imagescience.de/smi/index.htm'>IMAGIC m-r-a</a>"
		."&nbsp;<img src='img/external.png'>"
		." command to align your particles to the templates within a specified template stack"
		."</p>\n";
	echo "</td></tr>\n";
}



	/*
	** Topology representing network alignment
	*/
	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/canimg.png' width='64'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='selectStackForm.php?expId=$expId&method=frealign'>Frealign Refinement</a></h3>\n";
	echo "<p>Fast & easy 2D ref-free alignment by iterative classification using "
		."a topology-representing network, followed by multi-reference alignment. "
		."The classification is performed by Vince Ramey's implementation of "
		."<a target='blank' href='http://www.ncbi.nlm.nih.gov/pubmed/14572474'>"
		."Ogura et al. JSB (2003)</a>"
		."</p>\n";
	echo "</td></tr>\n";


	/*
	** Topology representing network alignment
	*/
	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/eman_logo.png' width='64'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='selectStackForm.php?expId=$expId&method=eman'>EMAN Refinement</a></h3>\n";
	echo "<p>Fast and easy 2D ref-free alignment using EMAN's "
		."<a href='http://blake.bcm.tmc.edu/eman/eman1/progs/refine2d.py.html'>"
		."refine2d.py</a> program"
		."</p>\n";
	echo "</td></tr>\n";

echo "</table>\n";
processing_footer();
exit;

