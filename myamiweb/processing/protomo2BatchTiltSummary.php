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

$corrpeak_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/correlations/s*.gif");
$corrpeak_vid_files = glob("$rundir/tiltseries".$tiltseries."/media/correlations/s*.{mp4,ogv,webm}",GLOB_BRACE);
$qa_gif_file = "$rundir/tiltseries".$tiltseries."/media/quality_assessment/series".$tiltseries."_quality_assessment.gif";
$qa_gif = "loadimg.php?rawgif=1&filename=".$qa_gif_file;

// Quality assessment for each iteration
$html .= "
<hr />
<center><H3><b>Quality Assessment for Tilt-Series #".ltrim($tiltseries, '0')."</b></H3></center>
<hr />";
$html .= '<center><img src="'.$qa_gif.'" alt="qa" width="666" />'."</center>";

$html .= "
<hr />
<center><H4><b>Correlation Peaks for Each Iteration </b></H4></center>
<hr />";

$i = 0;
$j = -1;
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
			if ($ite % 4 == 0 OR $ite < 1) {
				$html .= "</tr><tr>";
				$j++;
				break;
			}
			$i++;
		}
		$i = 0 + 4*$j;
		foreach ($corrpeak_gif_files as $corr)
		{
			$ite=$i+1;
			if ($ite <= count($corrpeak_gif_files) AND $ite > 0) {
				$corrpeak_gif = "loadimg.php?rawgif=1&filename=".$corrpeak_gif_files[$i];
				$html .= '<td><center><a href="protomo2BatchTiltIterationSummary.php?iter='.$ite.'&rundir='.$rundir.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$corrpeak_gif.'"/></a></center></td>';
			}
			if ($ite % 4 == 0 OR $ite < 1) {
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
			if ($ite <= count($corrpeak_vid_files)/1.85 AND $ite > 0) {
				$html .= '<th><a href="protomo2BatchTiltIterationSummary.php?iter='.$ite.'&rundir='.$rundir.'&tiltseries='.$tiltseries.'" target="_blank">Iteration #'.$ite.'</a></th>';
			}
			if ($ite % 4 == 0 OR $ite < 1) {
				$html .= "</tr><tr>";
				$j++;
				break;
			}
			$i++;
		}
		$i = 0 + 4*$j;
		foreach ($corrpeak_vid_files as $corr)
		{
			$ite=$i+1;
			if ($ite <= count($corrpeak_vid_files)/1.85 AND $ite > 0) {
				$corrpeak_vid_mp4 = "loadvid.php?filename=".$corrpeak_vid_files[$i];
				$html .= '<td><center><a href="protomo2BatchTiltIterationSummary.php?iter='.$ite.'&rundir='.$rundir.'&tiltseries='.$tiltseries.'" target="_blank">
					 <video id="corrpeakVideos" autoplay loop>
					 <source src="'.$corrpeak_vid_mp4.'" type="video/mp4" loop>
					 </video></a></center></td>';
			}
			if ($ite % 4 == 0 OR $ite < 1) {
				$html .= "</tr><tr>";
				$i++;
				break;
			}
			$i++;
		}
	} while ($i < count($corrpeak_vid_files)/1.85);
}
$html .= '</tr><tr></table></center><br>';


echo $html
?>
</body>
</html>
