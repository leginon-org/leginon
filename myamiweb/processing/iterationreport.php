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
require "inc/viewer.inc";
require "inc/processing.inc";

$runId= $_GET['rId'];
$itr = $_GET['itr'];

$particle = new particledata();

?>

<html>
<head>
<title>Refine Iteration Report</title>
<link rel="stylesheet" type="text/css" href="../css/viewer.css">
</head>
<body>

<?php

	$itrinfo=$particle->getRefinementData($runId,$itr);
	$paraminfo=$particle->getIterationInfo($runId,$itr);

	$report_title = 'Refine Iteration Report for Iteration';
	$report_spec = $itrinfo['DEF_id'];
	echo divtitle($report_title."<FONT class='aptitle'>
		</FONT> (ID: <FONT class='aptitle'>".$report_spec."</FONT>)");
/*
// Report summary line
	echo "<br><table cellspacing='1' cellpadding='2'><tr><td><span class='datafield0'>Total particles for $runparams[stackRunName]: </span></td><td>$nump</td></tr></table>\n";
*/
//Report parameters
	echo "<table><tr><td>";
	$datainfo=$paraminfo;
	$exclude_fields = array('DEF_id','DEF_timestamp','REF|ApPathData|path');
	$title = "refinement parameters";
	$particle->displayParameters($title,$datainfo,$exclude_fields);
	echo "</td><td>";
	echo "</td><tr></table>";
?>
</body>
</html>
