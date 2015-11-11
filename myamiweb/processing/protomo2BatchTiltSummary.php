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

$rundir=$_GET['rundir'];
$tiltseries=$_GET['tiltseries'];

$ctf_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/ctf_correction/s*.gif");
$dose_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/dose_compensation/s*.gif");
$corrpeak_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/correlations/s*.gif");
$corrpeak_vid_files = glob("$rundir/tiltseries".$tiltseries."/media/correlations/s*.{mp4,ogv,webm}",GLOB_BRACE);
$qa_gif_file = "$rundir/tiltseries".$tiltseries."/media/quality_assessment/series".$tiltseries."_quality_assessment.gif";
$azimuth_gif_file = "$rundir/tiltseries".$tiltseries."/media/angle_refinement/series".sprintf('%04d',$tiltseries)."_azimuth.gif";
$orientation_gif_file = "$rundir/tiltseries".$tiltseries."/media/angle_refinement/series".sprintf('%04d',$tiltseries)."_orientation.gif";
$elevation_gif_file = "$rundir/tiltseries".$tiltseries."/media/angle_refinement/series".sprintf('%04d',$tiltseries)."_elevation.gif";
$ctfplot_gif = "loadimg.php?rawgif=1&filename=".$ctf_gif_files[0];
$ctfdefocus_gif = "loadimg.php?rawgif=1&filename=".$ctf_gif_files[1];
$dose_gif = "loadimg.php?rawgif=1&filename=".$dose_gif_files[0];
$dosecomp_gif = "loadimg.php?rawgif=1&filename=".$dose_gif_files[1];
$qa_gif = "loadimg.php?rawgif=1&filename=".$qa_gif_file;
$azimuth_gif = "loadimg.php?rawgif=1&filename=".$azimuth_gif_file;
$orientation_gif = "loadimg.php?rawgif=1&filename=".$orientation_gif_file;
$elevation_gif = "loadimg.php?rawgif=1&filename=".$elevation_gif_file;

$runname='tiltseries'.$tiltseries;

// Quality assessment for each iteration
$html .= "
<hr />
<center><H3><b>Quality Assessment for Tilt-Series #".ltrim($tiltseries, '0')."</b></H3></center>
<hr />";
$html .= '<table id="" class="display" cellspacing="0" border="0" width="100%">';
$html .= '<tr><td rowspan="3">';
$html .= '<center><a href="protomo2QualityAssessmentPlots.php?outdir='.$rundir.'&runname='.$runname.'&tiltseries='.ltrim($tiltseries, '0').'" target="_blank"><img src="'.$qa_gif.'" alt="qa" width="700" />'."</a></center>";
$html .= '<td><center><a href="protomo2QualityAssessmentPlots.php?outdir='.$rundir.'&runname='.$runname.'&tiltseries='.ltrim($tiltseries, '0').'" target="_blank"><img src="'.$azimuth_gif.'" alt="azimuth" width="275" />'."</a></center></td></tr>";
$html .= '<td><center><a href="protomo2QualityAssessmentPlots.php?outdir='.$rundir.'&runname='.$runname.'&tiltseries='.ltrim($tiltseries, '0').'" target="_blank"><img src="'.$orientation_gif.'" alt="theta" width="275" />'."</a></center></td></tr>";
$html .= '<td><center><a href="protomo2QualityAssessmentPlots.php?outdir='.$rundir.'&runname='.$runname.'&tiltseries='.ltrim($tiltseries, '0').'" target="_blank"><img src="'.$elevation_gif.'" alt="elevation" width="275" />'."</a></center></td></tr>";
$html .= '</tr></td></table>';

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
				$html .= '<th><a href="protomo2BatchTiltIterationSummary.php?iter='.$ite.'&rundir='.$rundir.'&tiltseries='.$tiltseries.'" target="_blank">Iteration #'.$ite.'</a></th>';
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
				$html .= '<td><center><a href="protomo2BatchTiltIterationSummary.php?iter='.$ite.'&rundir='.$rundir.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$corrpeak_gif.'"/></a></center></td>';
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
				$html .= '<th><a href="protomo2BatchTiltIterationSummary.php?iter='.$ite.'&rundir='.$rundir.'&tiltseries='.$tiltseries.'" target="_blank">Iteration #'.$ite.'</a></th>';
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
				$html .= '<td><center><a href="protomo2BatchTiltIterationSummary.php?iter='.$ite.'&rundir='.$rundir.'&tiltseries='.$tiltseries.'" target="_blank">
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


echo $html
?>
</body>
</html>
