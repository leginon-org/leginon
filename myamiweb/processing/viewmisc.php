<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Display results for each iteration of a refinement
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
  
// --- check if reconstruction is specified
$reconId = $_GET['reconId'];
writeTop("Miscellaneous","Miscellaneous Stuff");

// --- Get Reconstruction Data
$particle = new particledata();
$fileinfo = $particle->getMiscInfoFromReconId($reconId);
# display starting model
$html .= "<TABLE WIDTH='600'>\n";
foreach ($fileinfo as $p) {
  $html .= "<TR><TD>";
  $snapfile = $p['path'].'/'.$p['name'];
  if (ereg('\.txt$',$p['name'])){
    $html .= "<A HREF='loadtxt.php?filename=$snapfile'>$p[name]</A>\n";
  }
  else{
    $html .= "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'><IMG SRC='loadimg.php?filename=$snapfile' HEIGHT='200'>\n";
  }
  $html .= "</TD><TD>$p[description]</TD>\n";
  $html .= "</TR>\n";
}
$html.="</TABLE>\n";

echo $html;

writeBottom();
?>
