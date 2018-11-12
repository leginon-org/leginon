<?php
require_once "inc/particledata.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";

$expId= $_GET['expId'];
$runId = $_GET['rId'];
$stackId = $_GET['stackId'];
$particle = new particledata();

$projectId=getProjectId();

// Display the standard Appion interface header
processing_header('Generate Missing Stack',"Generate Missing Stack");
// Display the table built by the BasicReport class or errors
$command = "generateMissingStack.py ";
$command.= "--projectid=$projectId ";
$command.= "--expid=$expId ";
$command.= "--stackid=$stackId ";
if ($clusterId) $command.= "--cluster-id=$clusterId ";

echo $command;

// Display the standard Appion interface footer
processing_footer();

?>
