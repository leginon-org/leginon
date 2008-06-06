<?php
/**
 *  The Leginon software is Copyright 2003 
 *  The Scripps Research Institute, La Jolla, CA
 *  For terms of the license agreement
 *  see  http://ami.scripps.edu/software/leginon-license
 *
 *  Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/leginon.inc";
require "inc/project.inc";

$errors=false;

$leginondata = new leginondata();

// check if coming directly from a session
$expId=$_GET['expId'];
if ($expId){
  $sessionId=$expId;
  $projectId=getProjectFromExpId($expId);
  $formAction=$_SERVER['PHP_SELF']."?expId=$expId";
}
else {
  $sessionId=$_POST['sessionId'];
  $formAction=$_SERVER['PHP_SELF'];  
}

$data = processing_header("Appion Data Processing","Appion Data Processing", "<script src='../js/viewer.js'></script>");
// --- main window starts here --- //

// write out errors, if any came up:
if ($errors) {
  echo "<font color='red'>$errors</font>\n<hr />\n";
}
processing_footer();
?>
