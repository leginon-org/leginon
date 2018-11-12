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

processing_header("Per-particle Drift Correction Selection","Per-particle Frame Alignment Selection", $javascript,False);

// Selection Header
echo "<table border='0' width='640'>\n";
echo "<tr><td>\n";
echo "  <h2>Particle Stack Frame Alignment Procedures</h2>\n";
echo "  <h4>\n";
echo "    These programs align frames of individual particles \n";
echo "  </h4>\n";
echo "</td></tr>\n";
echo "</table>\n";

/*
** Rubinstein lm-bfgs Particle Polisher
*/

echo "<br/>\n";
echo "<table border='1' class='tableborder' width='640'>\n";

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=rubinsteinParticlePolisher'> Rubinstein Particle Polisher</a></h3>\n";
echo " <p> CPU program Im-bfgs </p>";
echo " <p>Written by John Rubinstein. See <a http://sites.google.com/site/rubinsteingroup/direct-detector-align_lmbfgs> <b>Rubinstein group software site</b> </a> for more information"
        ."</p>\n";
echo "</td></tr>\n";

/*
** DE per particle alignment
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/DE.png' width='96'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=makeDEPerParticle'>DE per Particle Alignment using DE_process_frames.py</a></h3>\n";
echo " <p> CPU program parallelized by multiple job submission</p>";
echo " <p>Written by Benjamin Bammes for DE-12, DE-20, and DE-64.  Operates on particle stacks. Wrapped in Appion by Scott Stagg."
	."</p>\n";
echo "</td></tr>\n";

echo "</table>\n";

processing_footer();
exit;

