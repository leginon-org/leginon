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

ini_set('session.gc_maxlifetime', 604800);
session_set_cookie_params(604800);

session_start();
$rundir=$_GET['rundir'];
$tiltseries=$_GET['tiltseries'];

$ctf_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/ctf_correction/s*.gif");
$dose_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/dose_compensation/s*.gif");
$corrpeak_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/correlations/c*.gif");
$corrpeak_vid_files = glob("$rundir/tiltseries".$tiltseries."/media/correlations/c*.{mp4,ogv,webm}",GLOB_BRACE);
$initial_tilt_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/tiltseries/i*.gif");
$initial_tilt_vid_files = glob("$rundir/tiltseries".$tiltseries."/media/tiltseries/i*.{mp4,ogv,webm}",GLOB_BRACE);
$tilt_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/tiltseries/c*.gif");
$tilt_vid_files = glob("$rundir/tiltseries".$tiltseries."/media/tiltseries/c*.{mp4,ogv,webm}",GLOB_BRACE);
$rec_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/reconstructions/c*.gif");
$rec_vid_files = glob("$rundir/tiltseries".$tiltseries."/media/reconstructions/c*.{mp4,ogv,webm}",GLOB_BRACE);

// Display Coarse Alignment Summary
$ctfplot_gif = "loadimg.php?rawgif=1&filename=".$ctf_gif_files[0];
$ctfdefocus_gif = "loadimg.php?rawgif=1&filename=".$ctf_gif_files[1];
$dose_gif = "loadimg.php?rawgif=1&filename=".$dose_gif_files[0];
$dosecomp_gif = "loadimg.php?rawgif=1&filename=".$dose_gif_files[1];
$corrpeak_gif = "loadimg.php?rawgif=1&filename=".$corrpeak_gif_files[0];
$corrpeak_mp4 = "loadvid.php?filename=".$corrpeak_vid_files[0];
$corrpeak_ogv = "loadvid.php?filename=".$corrpeak_vid_files[1];
$corrpeak_webm = "loadvid.php?filename=".$corrpeak_vid_files[2];
$download_corrpeak_mp4 = "downloadvid.php?filename=".$corrpeak_vid_files[0];
$initial_tilt_gif = "loadimg.php?rawgif=1&filename=".$initial_tilt_gif_files[0];
$initial_tilt_mp4 = "loadvid.php?filename=".$initial_tilt_vid_files[0];
$initial_tilt_ogv = "loadvid.php?filename=".$initial_tilt_vid_files[1];
$initial_tilt_webm = "loadvid.php?filename=".$initial_tilt_vid_files[2];
$download_initial_tilt_mp4 = "downloadvid.php?filename=".$initial_tilt_vid_files[0];
$tilt_gif = "loadimg.php?rawgif=1&filename=".$tilt_gif_files[0];
$tilt_mp4 = "loadvid.php?filename=".$tilt_vid_files[0];
$tilt_ogv = "loadvid.php?filename=".$tilt_vid_files[1];
$tilt_webm = "loadvid.php?filename=".$tilt_vid_files[2];
$download_tilt_mp4 = "downloadvid.php?filename=".$tilt_vid_files[0];
$rec_gif = "loadimg.php?rawgif=1&filename=".$rec_gif_files[0];
$rec_mp4 = "loadvid.php?filename=".$rec_vid_files[0];
$rec_ogv = "loadvid.php?filename=".$rec_vid_files[1];
$rec_webm = "loadvid.php?filename=".$rec_vid_files[2];
$download_rec_mp4 = "downloadvid.php?filename=".$rec_vid_files[0];

$html .= "
	<center><H3><b>Tilt-Series #".ltrim($tiltseries, '0')."<br>Coarse Alignment</b></H3></center>
	<hr />";
$html .= "
<center><H4>Tilt-Series Correlation Peaks</H4></center>
<br />";
if (isset($corrpeak_gif_files[0])) {
	$html .= '<center><img src="'.$corrpeak_gif.'" alt="correlations" />'."<br /></center>";
	$html .= '<center>';
	$html .= '<p align="right"><a href="'.$download_corrpeak_mp4.'">Download Video</a></p><br /><hr />';
} elseif (isset($corrpeak_vid_files[0])){
	$html .= '<center><video id="corrpeakVideos" autoplay loop>
		  <source src="'.$corrpeak_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$corrpeak_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$corrpeak_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<center>';
	$html .= '<p align="right"><a href="'.$download_corrpeak_mp4.'">Download Video</a></p><hr />';
} else {
	$html .= "<center><b>Depiction Correlation Peak Video for Coarse Alignment either failed to generate or is still processing</b></center>";
}

$html.='<br /><script type="text/javascript">
function toggleMe(a){
var e=document.getElementById(a);
if(!e)return true;
if(e.style.display=="none"){
e.style.display="block"
}
else{
e.style.display="none"
}
return true;
}
</script>

<center><input type="button" style="width:150px;height:30px;" onclick="return toggleMe(\'para1\')" value="View Initial Tilt-Series"></center><br>
<div id="para1" style="display:none">';
$html .= "
<center><H4>Tilt-Series Before Coarse Alignment</H4></center>
<br />";
if (isset($initial_tilt_gif_files[0])) {
	$html .= '<center><img src="'.$initial_tilt_gif.'" alt="tiltseries" />'."<br /></center>";
	$html .= '<center>';
	$html .= '<p align="right"><a href="'.$download_initial_tilt_mp4.'">Download Video</a></p><br /><br />';
} elseif (isset($initial_tilt_vid_files[0])){
	$html .= '<center><video id="initialTiltVideos" controls autoplay loop>
		  <source src="'.$initial_tilt_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$initial_tilt_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$initial_tilt_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<center>';
	$html .= '<p align="right"><a href="'.$download_initial_tilt_mp4.'">Download Video</a></p>';
} else {
	$html .= "<center><b>Depiction Tilt-Series Video for unaligned tilt-series either failed to generate, is still processing, or wasn't requested</b></center>";
}
$html .= '</div>';

$html .= "
<hr /><br /><center><H4>Tilt-Series After Coarse Alignment</H4></center>
<br />";
if (isset($tilt_gif_files[0])) {
	$html .= '<center><img src="'.$tilt_gif.'" alt="tiltseries" />'."<br /></center>";
	$html .= '<center>';
	$html .= '<p align="right"><a href="'.$download_tilt_mp4.'">Download Video</a></p><br /><br /><hr />';
} elseif (isset($tilt_vid_files[0])){
	$html .= '<center><video id="tiltVideos" controls autoplay loop>
		  <source src="'.$tilt_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$tilt_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$tilt_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<center>';
	$html .= '<p align="right"><a href="'.$download_tilt_mp4.'">Download Video</a></p><hr />';
} else {
	$html .= "<center><b>Depiction Tilt-Series Video for Coarse Alignment either failed to generate, is still processing, or wasn't requested</b></center>";
}
$html .= "
<br />
<center><H4>Tilt-Series Reconstruction After Coarse Alignment</H4></center>
<br />";
if (isset($rec_gif_files[0])) {
	$html .= '<center><img src="'.$rec_gif.'" alt="reconstruction" />'."<br /></center>";
	$html .= '<center>';
	$html .= '<p align="right"><a href="'.$download_rec_mp4.'">Download Video</a></p><br /><br /><hr />';
} elseif (isset($rec_vid_files[0])){
	$html .= '<center><video id="reconVideos" controls autoplay loop>
		  <source src="'.$rec_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$rec_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$rec_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<center>';
	$html .= '<p align="right"><a href="'.$download_rec_mp4.'">Download Video</a></p><hr />';
} else {
	$html .= "<center><b>Depiction Reconstruction Video for Coarse Alignment either failed to generate, is still processing, or wasn't requested</b></center>";
}

if (isset($ctf_gif_files[0])) {
	$html .= "
<br />	
<center><H4>CTF Correction</H4></center>
<br />";
	$html .= '<center><table id="" class="display" cellspacing="0" border="0"><tr>';
	$html .= '<td><img src="'.$ctfdefocus_gif.'" alt="ctfdefocus_gif" width="400" />'."<br /></td>";
	$html .= '<td><img src="'.$ctfplot_gif.'" alt="ctfplot_gif" width="400" />'."<br /></td>";
	$html .= '</tr><tr></table></center><br>';
	$html .= '<center>';
}

if (isset($dose_gif_files[0])) {
	$html .= "
<br />	
<center><H4>Dose Compensation</H4></center>
<br />";
	$html .= '<center><table id="" class="display" cellspacing="0" border="0"><tr>';
	$html .= '<td><img src="'.$dose_gif.'" alt="dose_gif" width="400" />'."<br /></td>";
	$html .= '<td><img src="'.$dosecomp_gif.'" alt="dosecomp_gif" width="400" />'."<br /></td>";
	$html .= '</tr><tr></table></center><br>';
	$html .= '<center>';
}

echo $html
?>
</body>
</html>