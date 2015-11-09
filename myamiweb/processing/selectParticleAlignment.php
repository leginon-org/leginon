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

/*
** Xmipp Maximum Likelihood Reference Free Alignment
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/xmipp_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runMaxLikeAlign.php?expId=$expId'>Xmipp Maximum Likelihood Alignment</a></h3>\n";
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

/*
 ** Xmipp 2 Clustering 2D Reference Free Alignment
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/xmipp_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runCL2DAlign.php?expId=$expId'>Xmipp 2 Clustering 2D Alignment</a></h3>\n";
echo " <p> this method builds a hierarchical classification of particles"
		." It uses the "
		."<a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/ClassAverages'>Xmipp 2 cl2d</a>"
				."&nbsp;<img src='img/external.png'>"
						." program to perform alignments. "
								."It is a relatively fast method that aligns and classify the images at the same time. "
										."The method starts by estimating a few classes that are further subdivided till the desired number of classes is reached. "
												."Every time an image is compared to the class averages it is aligned before-hand. <b> NOTE: in Xmipp 2.4 the alignment "
														."parameters are not saved in the database, and therefore this method cannot be used for RCT / OTR reconstructions.</b>"
																."</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";

/*
 ** Xmipp 3 Clustering 2D Reference Free Alignment
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/xmipp_logo.png' width='64'>\n";
echo "</td><td>\n";
//echo "  <h3><a href='runXmipp3CL2DAlign.php?expId=$expId'>Xmipp 3 Clustering 2D Alignment</a></h3>\n";
$form = "Xmipp3CL2DAlign";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=$form'>Xmipp 3 Clustering 2D Alignment</a></h3>\n";
echo " <p> this method builds a hierarchical classification of particles"
		." It uses the "
		."<a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/Classify_mpi_cl2d_v3'>Xmipp 3 cl2d</a>"
				."&nbsp;<img src='img/external.png'>"
						." program to perform alignments. "
								."It is a relatively fast method that aligns and classify the images at the same time. "
										."The method starts by estimating a few classes that are further subdivided till the desired number of classes is reached. "
												."Every time an image is compared to the class averages it is aligned before-hand."
																."</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";

if (!HIDE_IMAGIC) {
	/*
	** IMAGIC Reference Based Alignment
	*/

	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/imagic_logo.png' width='64'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='multiReferenceAlignment.php?expId=$expId'>IMAGIC Multi Reference Alignment (MRA)</a></h3>\n";
	echo " <p> this method uses the "
		."<a href='http://www.imagescience.de/smi/index.htm'>IMAGIC m-r-a</a>"
		."&nbsp;<img src='img/external.png'>"
		." command to align your particles to the templates within a specified template stack"
		."</p>\n";
	echo "</td></tr>\n";
}

/*
 ** Iterative Stable Alignment and Clustering (ISAC)
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <h2>ISAC</h2>\n";
echo "</td><td>\n";
//echo "  <h3><a href='runISAC.php?expId=$expId'>Iterative Stable Alignment and Clustering (ISAC)</a></h3>\n";
$form = "IsacForm";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=$form'>Iterative Stable Alignment and Clustering (ISAC)</a></h3>\n";
echo " <p>Initial version. More information about ISAC is available from:"
		." <a href='http://sparx-em.org/sparxwiki/sxisac'>sxisac - SPARX</a>"
		."</p>\n";
echo "</td></tr>\n";

/*
** Topology representing network alignment
*/
echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/canimg.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runTopolAlign.php?expId=$expId'>Iterative MSA/MRA</a></h3>\n";
echo "<p>Fast & easy 2D ref-free alignment by iterative MSA/MRA.  Classification "
	." can be performed using a topology-representing network or IMAGIC MSA."
	." Multi-reference alignment can be performed using IMAGIC or EMAN. </a>" 
#		."The classification is performed by Vince Ramey's implementation of "
#		."<a target='blank' href='http://www.ncbi.nlm.nih.gov/pubmed/14572474'>"
#		."Ogura et al. JSB (2003)</a>"
	."</p>\n";
echo "</td></tr>\n";

/*
** SPIDER Reference Based Alignment
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/spider_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runRefBasedAlignment.php?expId=$expId'>Spider Reference-based Alignment</a></h3>\n";
echo " <p> first you select template and then this method uses the "
	."<a href='http://www.wadsworth.org/spider_doc/spider/docs/man/apmq.html'>Spider AP MQ</a>"
	."&nbsp;<img src='img/external.png'>"
	." command to align your particles to the selected templates. Multiprocessing additions has made this extremely fast (~1 hour)."
	."<br/>"
	."<br/>"
	."This method is broken on SPIDER version 18 or newer, <a href='http://emg.nysbc.org/redmine/issues/2064'>see bug report</a>"
	."</p>\n";
//echo "  <img src='img/align-rsm.png' width='125'><br/>\n";
echo "</td></tr>\n";

/*
** Xmipp Maximum Likelihood Reference Based Alignment
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/xmipp_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runRefBasedMaxlikeAlign.php?expId=$expId'>Xmipp Reference Based Maximum Likelihood Alignment</a></h3>\n";
echo " <p> similar to reference-free but you select templates first."
	." It uses the "
	."<a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/MLalign2D'>Xmipp ml_align2d</a>"
	."&nbsp;<img src='img/external.png'>"
	." program to perform alignments. "
	."</p><p>\n"
	."Still untested as to how much bias the reference gives you, but this may be useful in some cases. "
	."Also, when no particles align to a particular template, it goes black and unused in further iterations. "
	."</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";

/*
** SPIDER Reference Free Alignment
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/spider_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runSpiderNoRefAlignment.php?expId=$expId'>Spider Reference-free Alignment</a></h3>\n";
echo " <p> this method uses the "
	."<a href='http://www.wadsworth.org/spider_doc/spider/docs/man/apsr.html'>Spider AP SR</a>"
	."&nbsp;<img src='img/external.png'>"
	." command to align your particles. "
	."</p><p>\n"
	."<font color='#aa2222'>WARNING:</font> this method is very quick (~few minutes), "
	."but also very sloppy and does not always do a great job. "
	."The only way to obtain decent results is to run several times and compare the results.</p>"
	."</p>\n";
//echo "  <img src='img/align-rsm.png' width='125'><br/>\n";
echo "</td></tr>\n";


if (!HIDE_FEATURE)
{
	/*
	** SPIDER Ed Iter Alignment
	*/
	
	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/editer.jpg' width='64'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='runEdIterAlignment.php?expId=$expId'>Ed's Iteration Alignment</a></h3>\n";
	echo " <p> this method uses the "
		."<a href='http://www.wadsworth.org/spider_doc/spider/docs/man/apsr.html'>Spider AP SR</a>"
		."&nbsp;<img src='img/external.png'> "
		." and the  "
		."<a href='http://www.wadsworth.org/spider_doc/spider/docs/man/apsh.html'>Spider AP SH</a>"
		."&nbsp;<img src='img/external.png'> "
		." commands to align your particles through multiple iterations of ref-free and ref-based alignments. "
		."</p><p>\n"
		."<font color='#aa2222'>WARNING:</font> report all problems to Ed Brignole"
		."</p>\n";
	//echo "  <img src='img/align-rsm.png' width='125'><br/>\n";
	echo "</td></tr>\n";
}

if (!HIDE_FEATURE)
{
	/*
	** EMAN reference-free alignment
	*/
	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/eman_logo.png' width='64'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='runEmanRefine2d.php?expId=$expId'>EMAN Refine 2d Reference-free Alignment</a></h3>\n";
	echo "<p>Fast and easy 2D ref-free alignment using EMAN's "
		."<a href='http://blake.bcm.tmc.edu/eman/eman1/progs/refine2d.py.html'>"
		."refine2d.py</a> program"
		."</p>\n";
	echo "</td></tr>\n";
}


echo "</table>\n";
processing_footer();
exit;

