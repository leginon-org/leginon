<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 */

require_once dirname(__FILE__).'/../config.php';
require_once "inc/path.inc";
require_once "inc/leginon.inc";
require_once "inc/processing.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";
require_once "inc/appionloop.inc";
require_once "inc/particledata.inc";

ini_set('session.gc_maxlifetime', 604800);
session_set_cookie_params(604800);

$page = $_SERVER['REQUEST_URI'];
header("Refresh: 300; URL=$page");

session_start();
$sessionname=$_SESSION['sessionname'];
$imageinfo=$_SESSION['imageinfo'];
$outdir=$_GET['outdir'];
$runname=$_GET['runname'];
$tiltseriesnumber=$_GET['tiltseries'];

$defocus_gif_files = glob("$outdir/".$runname."/defocus_estimation/*/*/diagnostic.gif");
$ctf_gif_files = glob("$outdir/".$runname."/media/ctf_correction/s*.gif");
$dose_gif_files = glob("$outdir/".$runname."/media/dose_compensation/s*.gif");
$corrpeak_gif_files = glob("$outdir/".$runname."/media/correlations/s*.gif");
$corrpeak_vid_files = glob("$outdir/".$runname."/media/correlations/s*.{mp4,ogv,webm}",GLOB_BRACE);
$recon_files = glob("$outdir/".$runname."/recons_*/*.mrc",GLOB_BRACE);
$stack_files = glob("$outdir/".$runname."/stack*/*.mrcs",GLOB_BRACE);
$qa_gif_file = "$outdir/".$runname."/media/quality_assessment/series".sprintf('%04d',$tiltseriesnumber)."_quality_assessment.gif";
$azimuth_gif_file = "$outdir/".$runname."/media/angle_refinement/series".sprintf('%04d',$tiltseriesnumber)."_azimuth.gif";
$orientation_gif_file = "$outdir/".$runname."/media/angle_refinement/series".sprintf('%04d',$tiltseriesnumber)."_orientation.gif";
$elevation_gif_file = "$outdir/".$runname."/media/angle_refinement/series".sprintf('%04d',$tiltseriesnumber)."_elevation.gif";
$defocus_gif = "loadimg.php?rawgif=1&filename=".$defocus_gif_files[0];
$ctfplot_gif = "loadimg.php?rawgif=1&filename=".$ctf_gif_files[0];
$ctfdefocus_gif = "loadimg.php?rawgif=1&filename=".$ctf_gif_files[1];
$dose_gif = "loadimg.php?rawgif=1&filename=".$dose_gif_files[0];
$dosecomp_gif = "loadimg.php?rawgif=1&filename=".$dose_gif_files[1];
$qa_gif = "loadimg.php?rawgif=1&filename=".$qa_gif_file;
$azimuth_gif = "loadimg.php?rawgif=1&filename=".$azimuth_gif_file;
$orientation_gif = "loadimg.php?rawgif=1&filename=".$orientation_gif_file;
$elevation_gif = "loadimg.php?rawgif=1&filename=".$elevation_gif_file;

// Quality assessment for each iteration
$html .= "
<hr />
<center><H2><b>Quality Assessment for Tilt-Series #".ltrim($tiltseriesnumber, '0')."</b> <font size=3>($runname)</font></H2></center>
<hr />";
$html .= '<table id="" class="display" cellspacing="0" border="0" width="100%">';
$html .= '<tr><td rowspan="3">';
$html .= '<center><a href="protomo2QualityAssessmentPlots.php?outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseriesnumber.'" target="_blank"><img src="'.$qa_gif.'" alt="qa" width="700" />'."</a></center>";
$html .= '<td><center><a href="protomo2QualityAssessmentPlots.php?outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseriesnumber.'" target="_blank"><img src="'.$azimuth_gif.'" alt="azimuth" width="275" />'."</a></center></td></tr>";
$html .= '<td><center><a href="protomo2QualityAssessmentPlots.php?outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseriesnumber.'" target="_blank"><img src="'.$orientation_gif.'" alt="theta" width="275" />'."</a></center></td></tr>";
$html .= '<td><center><a href="protomo2QualityAssessmentPlots.php?outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseriesnumber.'" target="_blank"><img src="'.$elevation_gif.'" alt="elevation" width="275" />'."</a></center></td></tr>";
$html .= '</tr></td></table>';

if (isset($defocus_gif_files[0])) {
	$html .= "
<center><H4>Defocus Estimation</H4></center>
<br />";
	$html .= '<table id="" class="display" cellspacing="0" border="1" align="center">';
	$html .= "<tr>";
	$html .= '<th><img src="loadimg.php?rawgif=1&filename='.$defocus_gif_files[2].'" alt="defocus_gif2" width="225" /></th>';
	$html .= '<th><img src="loadimg.php?rawgif=1&filename='.$defocus_gif_files[6].'" alt="defocus_gif6" width="325" /></th>';
	$html .= '<th><img src="loadimg.php?rawgif=1&filename='.$defocus_gif_files[10].'" alt="defocus_gif10" width="420" /></th>';
	$html .= "</tr><tr>";
	$html .= '<th><img src="loadimg.php?rawgif=1&filename='.$defocus_gif_files[0].'" alt="defocus_gif0" width="225" /></th>';
	$html .= '<th><img src="loadimg.php?rawgif=1&filename='.$defocus_gif_files[4].'" alt="defocus_gif4" width="325" /></th>';
	$html .= '<th><img src="loadimg.php?rawgif=1&filename='.$defocus_gif_files[8].'" alt="defocus_gif8" width="420" /></th>';
	$html .= "</tr><tr>";
	$html .= '<th><img src="loadimg.php?rawgif=1&filename='.$defocus_gif_files[1].'" alt="defocus_gif1" width="225" /></th>';
	$html .= '<th><img src="loadimg.php?rawgif=1&filename='.$defocus_gif_files[5].'" alt="defocus_gif5" width="325" /></th>';
	$html .= '<th><img src="loadimg.php?rawgif=1&filename='.$defocus_gif_files[9].'" alt="defocus_gif9" width="420" /></th>';
	$html .= "</tr><tr>";
	$html .= '<th><img src="loadimg.php?rawgif=1&filename='.$defocus_gif_files[3].'" alt="defocus_gif3" width="225" /></th>';
	$html .= '<th><img src="loadimg.php?rawgif=1&filename='.$defocus_gif_files[7].'" alt="defocus_gif7" width="325" /></th>';
	$html .= '<th><img src="loadimg.php?rawgif=1&filename='.$defocus_gif_files[11].'" alt="defocus_gif11" width="420" /></th>';
	$html .= '</tr><tr></table><br>';
}

if (isset($ctf_gif_files[0])) {
		$html .= "
	<center><H4>CTF Correction</H4></center>";
		$html .= '<center><table id="" class="display" cellspacing="0" border="0"><tr>';
		$html .= '<td><img src="'.$ctfdefocus_gif.'" alt="ctfdefocus_gif" width="300" />'."<br /></td>";
		$html .= '<td><img src="'.$ctfplot_gif.'" alt="ctfplot_gif" width="300" />'."<br /></td>";
		$html .= '</tr><tr></table></center>';
}
	
if (isset($dose_gif_files[0])) {
		$html .= "
	<center><H4>Dose Compensation</H4></center>";
		$html .= '<center><table id="" class="display" cellspacing="0" border="0"><tr>';
		$html .= '<td><img src="'.$dose_gif.'" alt="dose_gif" width="300" />'."<br /></td>";
		$html .= '<td><img src="'.$dosecomp_gif.'" alt="dosecomp_gif" width="300" />'."<br /></td>";
		$html .= '</tr><tr></table></center><br>';
}
	

$html .= "
<hr />
<center><H4><b>Correlation Peaks for Each Iteration </b></H4></center>
<hr />";

$i = 0;
$j = -1;
$numcolumns=5;
$html .= '<center><table id="" class="display" cellspacing="0" border="1" width="700">';
$html .= "<tr>";
if (count($corrpeak_gif_files) > 0)
{
	do {
		foreach ($corrpeak_gif_files as $corr)
		{
			$ite=$i+1;
			if ($ite <= count($corrpeak_gif_files) AND $ite > 0) {
				$html .= '<th><a href="protomo2TiltIterationSummary.php?expId='.$_GET['expId'].'&iter='.$ite.'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseriesnumber.'" target="_blank">Iteration #'.$ite.'</a></th>';
			}
			if ($ite % $numcolumns == 0 OR $ite < 1) {
				$html .= "</tr><tr>";
				$j++;
				break;
			}
			$i++;
		}
		$i = 0 + $numcolumns*$j;
		foreach ($corrpeak_gif_files as $corr)
		{
			$ite=$i+1;
			if ($ite <= count($corrpeak_gif_files) AND $ite > 0) {
				$corrpeak_gif = "loadimg.php?rawgif=1&filename=".$corrpeak_gif_files[$i];
				$html .= '<td><center><a href="protomo2TiltIterationSummary.php?expId='.$_GET['expId'].'&iter='.$ite.'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseriesnumber.'" target="_blank"><img src="'.$corrpeak_gif.'"/></a></center></td>';
			}
			if ($ite % $numcolumns == 0 OR $ite < 1) {
				$html .= "</tr><tr>";
				$i++;
				break;
			}
			$i++;
		}
	} while ($i < count($corrpeak_gif_files));
}
elseif (count($corrpeak_vid_files) > 0)
{
	do {
		foreach ($corrpeak_vid_files as $corr)
		{
			$ite=$i+1;
			if ($ite <= count($corrpeak_vid_files)/3 AND $ite > 0) {
				$html .= '<th><a href="protomo2TiltIterationSummary.php?expId='.$_GET['expId'].'&iter='.$ite.'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseriesnumber.'" target="_blank">Iteration #'.$ite.'</a></th>';
			}
			if ($ite % $numcolumns == 0 OR $ite < 1) {
				$html .= "</tr><tr>";
				$j++;
				break;
			}
			$i++;
		}
		$i = 0 + $numcolumns*$j;
		foreach ($corrpeak_vid_files as $corr)
		{
			$ite=$i+1;
			if ($ite <= count($corrpeak_vid_files)/3 AND $ite > 0) {
				$corrpeak_vid_mp4 = "loadvid.php?filename=".$corrpeak_vid_files[$i];
				$html .= '<td><center><a href="protomo2TiltIterationSummary.php?expId='.$_GET['expId'].'&iter='.$ite.'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseriesnumber.'" target="_blank">
					 <video id="corrpeakVideos" autoplay loop>
					 <source src="'.$corrpeak_vid_mp4.'" type="video/mp4" loop>
					 </video></a></center></td>';
			}
			if ($ite % $numcolumns == 0 OR $ite < 1) {
				$html .= "</tr><tr>";
				$i++;
				break;
			}
			$i++;
		}
	} while ($i < count($corrpeak_vid_files)/3);
}
$html .= '</tr><tr></table></center><br>';

if (count($recon_files) > 0) {
	$html .= "
	<hr />
	<center><H4><b>Available Reconstructions</b></H4></center>
	<hr />";
	
	foreach ($recon_files as $item) {
		$html .= '<br>'.$item;
	}
	$html .= '<br><br>';

}

if (count($stack_files) > 0) {
	$html .= "
	<hr />
	<center><H4><b>Available Tilt-Series Stacks</b></H4></center>
	<hr />";
	
	foreach ($stack_files as $item) {
		$html .= '<br>'.$item;
	}

}

echo $html

?>
</body>
</html>
