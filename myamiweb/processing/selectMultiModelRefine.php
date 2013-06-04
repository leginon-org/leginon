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

processing_header("Multi-Model Classification and Refinement Software Selection","Multi-Model Classification and Refinement Software Selection Page", $javascript,False);

// Selection Header
echo "<table border='0' width='640'>\n";
echo "<tr><td>\n";
echo "  <h2>Multi-Model Classification and Refinement Procedures</h2>\n";
echo "  <h4>\n";
echo "    Many molecular complexes appear to exhibit at least a small degree of intrinsic conformational variability that becomes "
	."important for performing their biological function. Alternatively, complexes may exist in variable compositional states, "
	."whereby a cofactor may be binding with substoichiometric affinity. This sort of conformational and / or compositional "
	."heterogeneity is often found within a single data set, and can be dealt with computationally. The algorithm(s) below "
	."address this issue by classifying raw particles into a predefined number of classes, using both supervised and unsupervised "
	."approaches. After classification, the particles are refined within their particular class and a model is reconstructed in a similar "
	."manner to single-model refinement protocols. Effectively, rather than limiting the final resolution of a reconstruction, "
	."conformational and / or compositional heterogeneity becomes a factor that can be exploited to uncover novel " 
	."states of the macromolecular complex.\n";
echo "  </h4>\n";
echo "</td></tr>\n";
echo "</table>\n";


echo "<br/>\n";
echo "<table border='1' class='tableborder' width='640'>\n";


/*
** Xmipp 3D Maximum Likelihood Classification 
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/xmipp_logo.png' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='selectStackForm.php?expId=$expId&method=xmippml3d&type=multi'>Xmipp Maximum-Likelihood 3D Classification</a></h3>\n";
echo " <p>This is the <a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/MLrefine3D'>Xmipp ML3D protocol.&nbsp</a><img src='img/external.png'>"
	." The classification technique is the key operation behind the all of the procedures in the "
	."<a href='http://xmipp.cnb.csic.es/twiki/bin/view/Xmipp/MLrefine3D'>full maximum-likelihood refinement procedure</a>&nbsp;<img src='img/external.png'>&nbsp;"
	."Through optimization of the log-likelihood function, it aims to find the most likely set of parameterers to construct a model describing the "
	."structural heterogeneity present in the data. One of the biggest advantages of this approach is that distinct classes are identified in an usupervised manner. "
	."The input to this procedure can either be a single, highly low-pass filtered reference, or several references. In the former case, the user is given the "
	."option of specifying the number of classes to uncover in an unsupervised manner. In the latter case, the number of resulting classes is identical "
	."to the number of input references, and the procedure becomes more supervised in nature. The downside to the maximum-likelihood approach is the large "
	."computational burden. For example, 25 iterations of a 100,000-particle stack with a boxsize of 80 pixels at an angular sampling increment of 10 "
	."degrees takes ~ 6 cpu months to complete. Therefore choose your cluster parameters wisely." 
	."</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";



echo "</table>\n";
processing_footer();
exit;

