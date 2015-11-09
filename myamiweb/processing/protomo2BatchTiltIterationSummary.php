<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */
ini_set('display_errors', '0');     # don't show any errors...
error_reporting(E_ALL | E_STRICT);

require_once dirname(__FILE__).'/../config.php';
require_once "inc/path.inc";
require_once "inc/leginon.inc";
require_once "inc/processing.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";
require_once "inc/appionloop.inc";
require_once "inc/particledata.inc";

$rundir=$_GET['rundir'];
$iter=$_GET['iter'];
$tiltseries=$_GET['tiltseries'];

$corrpeak_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/correlations/s*.gif");
$corrpeak_vid_files = glob("$rundir/tiltseries".$tiltseries."/media/correlations/series".$tiltseries.sprintf('%03d',$iter-1)."_cor.{mp4,ogv,webm}",GLOB_BRACE);
$corr_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/corrplots/series".$tiltseries.sprintf('%03d',$iter-1)."*.gif");
$tilt_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/tiltseries/s*.gif");
$tilt_vid_files = glob("$rundir/tiltseries".$tiltseries."/media/tiltseries/series".$tiltseries.sprintf('%03d',$iter-1).".{mp4,ogv,webm}",GLOB_BRACE);
$rec_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/reconstructions/s*.gif");
$rec_vid_files = glob("$rundir/tiltseries".$tiltseries."/media/reconstructions/series".$tiltseries.sprintf('%02d',$iter)."_bck.{mp4,ogv,webm}",GLOB_BRACE);

$corrpeak_gif = "loadimg.php?rawgif=1&filename=".$corrpeak_gif_files[$iter-1];
$corrpeak_mp4 = "loadvid.php?filename=".$corrpeak_vid_files[0];
$corrpeak_ogv = "loadvid.php?filename=".$corrpeak_vid_files[1];
$corrpeak_webm = "loadvid.php?filename=".$corrpeak_vid_files[2];
$download_corrpeak_mp4 = "downloadvid.php?filename=".$corrpeak_vid_files[0];
$corr_coa = "loadimg.php?rawgif=1&filename=".$corr_gif_files[0];
$corr_cofx = "loadimg.php?rawgif=1&filename=".$corr_gif_files[1];
$corr_cofy = "loadimg.php?rawgif=1&filename=".$corr_gif_files[2];
$corr_rot = "loadimg.php?rawgif=1&filename=".$corr_gif_files[3];
$corr_scl = "loadimg.php?rawgif=1&filename=".$corr_gif_files[4];
$tilt_gif = "loadimg.php?rawgif=1&filename=".$tilt_gif_files[$iter-1];
$tilt_mp4 = "loadvid.php?filename=".$tilt_vid_files[0];
$tilt_ogv = "loadvid.php?filename=".$tilt_vid_files[1];
$tilt_webm = "loadvid.php?filename=".$tilt_vid_files[2];
$download_tilt_mp4 = "downloadvid.php?filename=".$tilt_vid_files[0];
$rec_gif = "loadimg.php?rawgif=1&filename=".$rec_gif_files[$iter-1];
$rec_mp4 = "loadvid.php?filename=".$rec_vid_files[0];
$rec_ogv = "loadvid.php?filename=".$rec_vid_files[1];
$rec_webm = "loadvid.php?filename=".$rec_vid_files[2];
$download_rec_mp4 = "downloadvid.php?filename=".$rec_vid_files[0];

$html .= "
	<center><H3><b>Tilt-Series #".ltrim($tiltseries, '0')."<br>Refinement Iteration #$iter</b></H3></center>
	<hr />";
$html .= "
	<H4><center><b>Correlation Peak</b></center></H4>";
        
if (isset($corrpeak_gif_files[0])) {
	$html .= '<center><img src="'.$corrpeak_gif.'" alt="correlations" /></center>';
        $html .= '<p align="right"><a href="'.$download_corrpeak_mp4.'">Download Video</a></p><br /><hr />';
} elseif (isset($corrpeak_vid_files[0])){
        $html .= '<center><video id="corrpeakVideos" autoplay loop>
                  <source src="'.$corrpeak_mp4.'" type="video/mp4" loop>'.'<br />
                  <source src="'.$corrpeak_webm.'" type="video/webm" loop>'.'<br />
                  <source src="'.$corrpeak_ogv.'" type="video/ogg" loop>'.'<br />
                  HTML5 video is not supported by your browser.
                  </video></center>';
        //$html .= '<center>'.docpop('corrimageinfo_coarse', 'Image Info').'</center>';
        $html .= '<p align="right"><a href="'.$download_corrpeak_mp4.'">Download Video</a></p><hr />';
} else {
        $html .= "<center><b>Depiction Correlation Peak Video for Refinement Iteration ".$iter." either failed to generate or is still processing</b></center>";
}

$html .= "
	<H4><center><b>Correlation Plots</b></center></H4>";
$html .= '<center><table id="" class="display" cellspacing="0" border="1" width=820><tr>';
$html .= '<th>Correction Factor (x)</th>';
$html .= '<th>Correction Factor (y)</th>';
$html .= "</tr><tr>";
$html .= '<td><img src="'.$corr_cofx.'" alt="cofx" width="500" />'."<br /></td>";
$html .= '<td><img src="'.$corr_cofy.'" alt="cofy" width="500" />'."<br /></td>";
$html .= "</tr><tr>";
$html .= '<th>Correction Rotation Factor</th>';
$html .= '<th>Angle between the (x) and (y) Correction Factors</th>';
$html .= "</tr><tr>";
$html .= '<td><img src="'.$corr_rot.'" alt="rot" width="500" />'."<br /></td>";
$html .= '<td><img src="'.$corr_scl.'" alt="scl" width="500" />'."<br /></td>";
$html .= '</tr><tr></table></center><br><hr />';

$html .= "
	<H4><center><b>Tilt-Series</b></center></H4>";
        
if (isset($tilt_gif_files[0])) {
	$html .= '<center><img src="'.$tilt_gif.'" alt="correlations" /></center>';
        $html .= '<p align="right"><a href="'.$download_tilt_mp4.'">Download Video</a></p><br /><hr />';
} elseif (isset($tilt_vid_files[0])){
        $html .= '<center><video id="tiltVideos" controls autoplay loop>
                  <source src="'.$tilt_mp4.'" type="video/mp4" loop>'.'<br />
                  <source src="'.$tilt_webm.'" type="video/webm" loop>'.'<br />
                  <source src="'.$tilt_ogv.'" type="video/ogg" loop>z'.'<br />
                  HTML5 video is not supported by your browser.
                  </video></center>';
        //$html .= '<center>'.docpop('tiltimageinfo_coarse', 'Image Info').'</center>';
        $html .= '<p align="right"><a href="'.$download_tilt_mp4.'">Download Video</a></p><hr />';
} else {
        $html .= "<center><b>Depiction Tilt-Series Video for Refinement Iteration ".$iter." either failed to generate, is still processing, or wasn't requested.</b></center>";
}

$html .= "
	<H4><center><b>Preliminary Reconstruction</b></center></H4>";
        
if (isset($rec_gif_files[0])) {
	$html .= '<center><img src="'.$rec_gif.'" alt="correlations" /></center>';
        $html .= '<p align="right"><a href="'.$download_rec_mp4.'">Download Video</a></p><br />';
} elseif (isset($rec_vid_files[0])){
        $html .= '<center><video id="reconVideos" controls autoplay loop>
                  <source src="'.$rec_mp4.'" type="video/mp4" loop>'.'<br />
                  <source src="'.$rec_webm.'" type="video/webm" loop>'.'<br />
                  <source src="'.$rec_ogv.'" type="video/ogg" loop>'.'<br />
                  HTML5 video is not supported by your browser.
                  </video></center>';
        //$html .= '<center>'.docpop('reconimageinfo_coarse', 'Image Info').'</center>';
        $html .= '<p align="right"><a href="'.$download_rec_mp4.'">Download Video</a></p>';
} else {
        $html .= "<center><b>Depiction Reconstruction Video for Refinement Iteration ".$iter." either failed to generate, is still processing, or wasn't requested.</b></center>";
}

echo $html
?>
</body>
</html>
