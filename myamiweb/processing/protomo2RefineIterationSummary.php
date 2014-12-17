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

$outdir=$_GET['outdir'];
$runname=$_GET['runname'];
$iter=$_GET['iter'];
$tiltseries=$_GET['tiltseries'];

$corrpeak_files = glob("$outdir/$runname/gifs/correlations/s*.gif");
$corr_files = glob("$outdir/$runname/gifs/corrplots/series".sprintf('%04d',$tiltseries).sprintf('%02d',$iter-1)."*.gif");
$tilt_files = glob("$outdir/$runname/gifs/tiltseries/s*.gif");
$rec_files = glob("$outdir/$runname/gifs/reconstructions/s*.gif");
$corrpeak_gif = "loadimg.php?rawgif=1&filename=".$corrpeak_files[$iter-1];
$corr_coa = "loadimg.php?rawgif=1&filename=".$corr_files[0];
$corr_cofx = "loadimg.php?rawgif=1&filename=".$corr_files[1];
$corr_cofy = "loadimg.php?rawgif=1&filename=".$corr_files[2];
$corr_rot = "loadimg.php?rawgif=1&filename=".$corr_files[3];
$tilt_gif = "loadimg.php?rawgif=1&filename=".$tilt_files[$iter-1];
$rec_gif = "loadimg.php?rawgif=1&filename=".$rec_files[$iter-1];

$html .= "
	<center><H3><b>Refinement Iteration #$iter</b></H3></center>
	<hr />";

$html .= "
	<H4><b>Correlation Peak</b></H4>";
        
$html .= '<img src="'.$corrpeak_gif.'" alt="correlations" />'."<br />";

$html .= "
	<H4><b>Correlation Plots</b></H4>";
$html .= '<table id="" class="display" cellspacing="0" border="1" width=820><tr>';
$html .= '<th>Correction Factor (x)</th>';
$html .= '<th>Correction Factor (y)</th>';
$html .= "</tr><tr>";
$html .= '<td><img src="'.$corr_cofx.'" alt="cofx" width="400" />'."<br /></td>";
$html .= '<td><img src="'.$corr_cofy.'" alt="cofy" width="400" />'."<br /></td>";
$html .= "</tr><tr>";
$html .= '<th>Correction Rotation Factor</th>';
$html .= '<th>Angle between the (x) and (y) Correction Factors</th>';
$html .= "</tr><tr>";
$html .= '<td><img src="'.$corr_rot.'" alt="rot" width="400" />'."<br /></td>";
$html .= '<td><img src="'.$corr_coa.'" alt="coa" width="400" />'."<br /></td>";
$html .= '</tr><tr></table><br>';

$html .= "
	<H4><b>Tilt Series</b></H4>";
        
$html .= '<img src="'.$tilt_gif.'" alt="correlations" />'."<br />";

$html .= "
	<H4><b>Preliminary Reconstruction</b></H4>";
        
$html .= '<img src="'.$rec_gif.'" alt="correlations" />'."<br />";


echo $html
?>
</body>
</html>
