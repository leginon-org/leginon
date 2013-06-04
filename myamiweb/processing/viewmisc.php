<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Display results for each iteration of a refinement
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
  
// --- check if reconstruction is specified
$reconId = $_GET['reconId'];
$projectId = getProjectId();
processing_header("Miscellaneous","Miscellaneous Stuff");

// --- Get Reconstruction Data
$particle = new particledata();
if ($reconId)
	$fileinfo = $particle->getMiscInfoFromReconId($reconId);
if ($projectId)
  $fileinfo = $particle->getMiscInfoFromProject($projectId);
# display starting model
$html .= "<TABLE WIDTH='600' BORDER='1'>\n";
foreach ($fileinfo as $p) {
  $html .= "<TR><td>";
  $snapfile = $p['path'].'/'.$p['name'];
  if (preg_match('%\.txt$%',$p['name'])){
    $html .= "<A HREF='loadtxt.php?filename=$snapfile'>$p[name]</A>\n";
  }
  elseif (preg_match('%\.html$%',$p['name'])){
		$txt = file_get_contents($snapfile);
    $html .= $txt;
  }
  else{
    $html .= "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'><img src='loadimg.php?filename=$snapfile' HEIGHT='200'>\n";
  }
  $html .= "</TD><td>$p[description]</TD>\n";
  $html .= "</tr>\n";
}
$html.="</table>\n";

echo $html;

processing_footer();
?>
