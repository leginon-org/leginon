<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once dirname(__FILE__).'/../config.php';
require_once "inc/path.inc";
require_once "inc/leginon.inc";
require_once "inc/processing.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";
require_once "inc/appionloop.inc";
require_once "inc/particledata.inc";

$outdir=$_GET['outdir'];
$runname=$_GET['runname'];
$tiltseries=$_GET['tiltseries'];

$qa_gif_file = "$outdir/$runname/media/quality_assessment/series".sprintf('%04d',$tiltseries)."_quality_assessment.gif";
$azimuth_gif_files = "$outdir/$runname/media/angle_refinement/series".sprintf('%04d',$tiltseries)."_azimuth.gif";
$theta_gif_files = "$outdir/$runname/media/angle_refinement/series".sprintf('%04d',$tiltseries)."_theta.gif";
$elevation_gif_files = "$outdir/$runname/media/angle_refinement/series".sprintf('%04d',$tiltseries)."_elevation.gif";

$qa_gif = "loadimg.php?rawgif=1&filename=".$qa_gif_file;
$azimuth_gif = "loadimg.php?rawgif=1&filename=".$azimuth_gif_files;
$theta_gif = "loadimg.php?rawgif=1&filename=".$theta_gif_files;
$elevation_gif = "loadimg.php?rawgif=1&filename=".$elevation_gif_files;

$html .= "
	<center><H3><b>Tilt-Series #$tiltseries Quality Assessment Plots</b></H3></center>
	<hr />";

$html .= "
	<H4><center><b>CCMS Plot</b></center></H4>";
        
if (isset($qa_gif_file)) {
	$html .= '<center><img src="'.$qa_gif.'" alt="qa" /></center>
	<hr />';
} else {
        $html .= "<center><b>CCMS Plot for Tilt-Series ".$tiltseries." either failed to generate or is processing</b></center>";
}

$html .= "
	<H4><center><b>Tilt Azimuth Plot</b></center></H4>";
        
if (isset($azimuth_gif_files)) {
	$html .= '<center><img src="'.$azimuth_gif.'" alt="azimuth" /></center>
	<hr />';
} else {
        $html .= "<center><b>Tilt Azimuth Plot for Tilt-Series ".$tiltseries." either failed to generate or is processing</b></center>";
}

$html .= "
	<H4><center><b>Grid Orientation (Theta) Plot</b></center></H4>";
        
if (isset($theta_gif_files)) {
	$html .= '<center><img src="'.$theta_gif.'" alt="theta" /></center>
	<hr />';
} else {
        $html .= "<center><b>Grid Orientation Plot for Tilt-Series ".$tiltseries." either failed to generate or is processing</b></center>";
}

$html .= "
	<H4><center><b>Tilt Elevation Plot</b></center></H4>";
        
if (isset($theta_gif_files)) {
	$html .= '<center><img src="'.$elevation_gif.'" alt="theta" /></center>';
} else {
        $html .= "<center><b>Tilt Elevation Plot for Tilt-Series ".$tiltseries." either failed to generate or is processing</b></center>";
}


echo $html
?>
</body>
</html>
