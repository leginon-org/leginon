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
	."</p>\n";
//echo "  <img src='img/align-rsm.png' width='125'><br/>\n";
echo "</td></tr>\n";

if (!$HIDE_IMAGIC && !HIDE_FEATURE) {
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
	."<font color='#aa2222'>WARNING:</font> report all problems to Ed"
	."</p>\n";
//echo "  <img src='img/align-rsm.png' width='125'><br/>\n";
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


if (!HIDE_FEATURE)
{
	/*
	** Topology representing network alignment
	*/
	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/canimg.png' width='64'>\n";
	echo "</td><td>\n";
	echo "  <h3><a href='runTopolAlign.php?expId=$expId'>CAN Reference-free alignment</a></h3>\n";
	echo "<p>Fast & easy 2D ref-free alignment by iterative classification using "
		."a topology-representing network, followed by multi-reference alignment. "
		."The classification is performed by Vince Ramey's implementation of "
		."<a target='blank' href='http://www.ncbi.nlm.nih.gov/pubmed/14572474'>"
		."Ogura et al. JSB (2003)</a>"
		."</p>\n";
	echo "</td></tr>\n";
}

echo "</table>\n";
processing_footer();
exit;

