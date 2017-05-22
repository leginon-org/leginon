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
#require_once "inc/displaytables.inc";

$expId = $_GET['expId'];
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

processing_header("Stack Tools","Stack Tools Page", $javascript,False);

// Selection Header
echo "<table border='0' width='640'>\n";
echo "<tr><td>\n";
echo "  <h2>Stack Creation Tools</h2>\n";
//echo "  <img src='img/stack.png' width='250'><br/>\n";
echo "  <h4>\n";
echo "   Stack creation takes particle picks or existing stacks to create stacks\n";
echo "  </h4>\n";
echo "</td></tr>\n";
echo "</table>\n";

echo "<br/>\n";
echo "<table border='0' class='tableborder' width='640'>\n";

/*
** Make Stack
*/

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/makestack.png' width='128'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runMakeStack2.php?expId=$expId'>Make Stack</a></h3>\n";
echo "<p> ";
echo "  create a stack from a particle picking run, full features ";
echo "</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";

/* ===== */

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/quick_stack.png' width='128'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=quickStackForm'>Quick Stack</a></h3>";
echo "<p> ";
echo "  quickly create a stack from a particle picking run, simple features ";
echo "</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";

/* ===== */

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/combinestack.png' width='128'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runCombineStacks.php?expId=$expId'>Combine Stacks</a></h3>";
echo "<p> ";
echo "  combine stacks from different sessions into one large stack.";
echo "</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";

/* ===== */

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/stackintopicks.png' width='128'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runStackIntoPicks.php?expId=$expId'>Convert Stack into Particle Picks</a></h3>";
echo "<p> ";
echo "  take an existing stack and create a particle picking run. "
	." This is good for creating a new stack based on an existing stack with a bigger boxsize .";
echo "</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";

/* ===== */

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/view_stack.png' width='128'>\n";
echo "</td><td>\n";
echo "  <h3><a href='stacksummary.php?expId=$expId&mean=1'>View Stacks</a></h3>";
echo "<p> ";
echo "  view a list of the available stacks where you can center the particles"
	." or filter the stack based on the mean and standard deviation";
echo "</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";

/* ===== */

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/substack.png' width='128'>\n";
echo "</td><td>\n";
echo "  <h3><a href='alignSubStack.php?expId=$expId'>Alignment SubStack</a></h3>";
echo "<p> ";
echo "  make a substack based on an alignment or classification. "
	."It is easier to select from stack viewer of class averages";
echo "</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";

/* ===== */

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/learnstack.png' width='128'>\n";
echo "</td><td>\n";
echo "  <h3><a href='learningStackCleaner.php?expId=$expId'>Learning Stack Cleaner</a></h3>";
echo "<p> ";
echo "You categorize particles as good or bad.  "
	."From your classification, the program learns the quality of the particles, which then can be extended to the entire stack.";
echo "</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";

/* ===== */

echo "<tr><td width='100' align='center'>\n";
echo "  <img src='img/appionlogo.jpg' width='64'>\n";
echo "</td><td>\n";
echo "  <h3><a href='runAppionLoop.php?expId=$expId&form=deParticleAlignForm'>Run DE particle stack alignment</a></h3>";
echo "<p> ";
echo "  DE has written a particle alignment script. This depends on particle stacks. ";
echo "</p>\n";
//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
echo "</td></tr>\n";



if (!HIDE_FEATURE)
{
	/* ===== */
	
	echo "<tr><td width='100' align='center'>\n";
	echo "  <img src='img/appionlogo.jpg' width='64'>\n";
	echo "</td><td>\n";
		echo "  <h3><a href='jumpSubStack.php?expId=$expId'>Jumpers SubStack</a></h3>";
	echo "<p> ";
		echo "  make a substack based on particle 'jumpers' from a reconstruction.";
	echo "</p>\n";
	//echo "  <img src='img/align-smr.png' width='250'><br/>\n";
	echo "</td></tr>\n";
}
echo "</table>";
processing_footer();
exit;

