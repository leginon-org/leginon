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
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";

processing_header("More Stack Tools","More Stack Tools Page", $javascript,False);

echo "<table border='1' class='tableborder'>";

echo "<tr><td>";
echo "  <h3><a href='makestack2.php?expId=$expId'>Make a New Stack</a></h3>";
echo "  create a stack from a particle picking run ";
echo "</td></tr>";

echo "<tr><td>";
echo "  <h3><a href='runCombineStacks.php?expId=$expId'>Combine Stacks</a></h3>";
echo "  combine stacks from different sessions into one large stack.";
echo "</td></tr>";

echo "<tr><td>";
echo "  <h3><a href='makestack.php?expId=$expId'>Old Make Stack</a></h3>";
echo "  use the old make stack to create a new stack ";
echo "</td></tr>";

echo "<tr><td>";
echo "  <h3><a href='stacksummary.php?expId=$expId&mean=1'>View Stacks</a></h3>";
echo "  view a list of the available stacks where you can center the particles"
	." or filter the stack based on the mean and standard deviation";
echo "</td></tr>";

echo "</table>";
processing_footer();
exit;

