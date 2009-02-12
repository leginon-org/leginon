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

$expId= $_GET['expId'];
$runId= $_GET['rId'];
$itr = $_GET['itr'];

$particle = new particledata();

processing_header('Refine Iteration Report','Refine Iteration Report');

$iteration=$particle->getRefinementData($runId,$itr);
$itrinfo=$iteration[0];
$paraminfo=$particle->getIterationInfo($runId,$itr);

$report_title = 'Report for Iteration';
$report_spec = $itrinfo['DEF_id'];
echo apdivtitle($report_title."<FONT class='aptitle'>
		</FONT> (ID: <FONT class='aptitle'>".$report_spec."</FONT>)");
echo "<table><tr><td>";
$datainfo=$paraminfo;
$exclude_fields = array('DEF_id','DEF_timestamp','REF|ApPathData|path');
$title = "refinement parameters";
$particle->displayParameters($title,$datainfo,$exclude_fields,$expId);
echo "</td><td>";
echo "</td><tr></table>";

processing_footer();
