<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
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

$page = $_SERVER['REQUEST_URI'];
header("Refresh: 300; URL=$page");

session_start();
$rundir=$_GET['rundir'];
$tiltseries=$_GET['tiltseries'];

$defocus_gif_files = glob("$rundir/tiltseries".$tiltseries."/defocus_estimation/*/*/diagnostic.gif");
$ctf_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/ctf_correction/s*.gif");
$dose_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/dose_compensation/s*.gif");
$corrpeak_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/correlations/c*.gif");
$corrpeak_vid_files = glob("$rundir/tiltseries".$tiltseries."/media/correlations/c*.{mp4,ogv,webm}",GLOB_BRACE);
$initial_tilt_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/tiltseries/i*.gif");
$initial_tilt_vid_files = glob("$rundir/tiltseries".$tiltseries."/media/tiltseries/i*.{mp4,ogv,webm}",GLOB_BRACE);
$manual_tilt_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/tiltseries/m*.gif");
$manual_tilt_vid_files = glob("$rundir/tiltseries".$tiltseries."/media/tiltseries/m*.{mp4,ogv,webm}",GLOB_BRACE);
$tilt_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/tiltseries/c*.gif");
$tilt_vid_files = glob("$rundir/tiltseries".$tiltseries."/media/tiltseries/c*.{mp4,ogv,webm}",GLOB_BRACE);
$manual_rec_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/reconstructions/m*.gif");
$manual_rec_vid_files = glob("$rundir/tiltseries".$tiltseries."/media/reconstructions/m*.{mp4,ogv,webm}",GLOB_BRACE);
$rec_gif_files = glob("$rundir/tiltseries".$tiltseries."/media/reconstructions/c*.gif");
$rec_vid_files = glob("$rundir/tiltseries".$tiltseries."/media/reconstructions/c*.{mp4,ogv,webm}",GLOB_BRACE);

// Display Coarse Alignment Summary
$defocus_gif = "loadimg.php?rawgif=1&filename=".$defocus_gif_files[0];
$ctfplot_gif = "loadimg.php?rawgif=1&filename=".$ctf_gif_files[0];
$ctfdefocus_gif = "loadimg.php?rawgif=1&filename=".$ctf_gif_files[1];
$dose_gif = "loadimg.php?rawgif=1&filename=".$dose_gif_files[0];
$dosecomp_gif = "loadimg.php?rawgif=1&filename=".$dose_gif_files[1];
$corrpeak_gif = "loadimg.php?rawgif=1&filename=".$corrpeak_gif_files[0];
$corrpeak_mp4 = "loadvid.php?filename=".$corrpeak_vid_files[0];
$corrpeak_ogv = "loadvid.php?filename=".$corrpeak_vid_files[1];
$corrpeak_webm = "loadvid.php?filename=".$corrpeak_vid_files[2];
$corrpeak2_gif = "loadimg.php?rawgif=1&filename=".$corrpeak_gif_files[1];
$corrpeak2_mp4 = "loadvid.php?filename=".$corrpeak_vid_files[3];
$corrpeak2_ogv = "loadvid.php?filename=".$corrpeak_vid_files[4];
$corrpeak2_webm = "loadvid.php?filename=".$corrpeak_vid_files[5];
$download_corrpeak_mp4 = "downloadvid.php?filename=".$corrpeak_vid_files[0];
$download_corrpeak2_mp4 = "downloadvid.php?filename=".$corrpeak_vid_files[3];
$initial_tilt_gif = "loadimg.php?rawgif=1&filename=".$initial_tilt_gif_files[0];
$initial_tilt_mp4 = "loadvid.php?filename=".$initial_tilt_vid_files[0];
$initial_tilt_ogv = "loadvid.php?filename=".$initial_tilt_vid_files[1];
$initial_tilt_webm = "loadvid.php?filename=".$initial_tilt_vid_files[2];
$download_initial_tilt_mp4 = "downloadvid.php?filename=".$initial_tilt_vid_files[0];
$manual_tilt_gif = "loadimg.php?rawgif=1&filename=".$manual_tilt_gif_files[0];
$manual_tilt_mp4 = "loadvid.php?filename=".$manual_tilt_vid_files[0];
$manual_tilt_ogv = "loadvid.php?filename=".$manual_tilt_vid_files[1];
$manual_tilt_webm = "loadvid.php?filename=".$manual_tilt_vid_files[2];
$download_manual_tilt_mp4 = "downloadvid.php?filename=".$manual_tilt_vid_files[0];
$tilt_gif = "loadimg.php?rawgif=1&filename=".$tilt_gif_files[0];
$tilt_mp4 = "loadvid.php?filename=".$tilt_vid_files[0];
$tilt_ogv = "loadvid.php?filename=".$tilt_vid_files[1];
$tilt_webm = "loadvid.php?filename=".$tilt_vid_files[2];
$tilt2_gif = "loadimg.php?rawgif=1&filename=".$tilt_gif_files[1];
$tilt2_mp4 = "loadvid.php?filename=".$tilt_vid_files[3];
$tilt2_ogv = "loadvid.php?filename=".$tilt_vid_files[4];
$tilt2_webm = "loadvid.php?filename=".$tilt_vid_files[5];
$download_tilt_mp4 = "downloadvid.php?filename=".$tilt_vid_files[0];
$download_tilt2_mp4 = "downloadvid.php?filename=".$tilt_vid_files[3];
$rec_gif = "loadimg.php?rawgif=1&filename=".$rec_gif_files[0];
$rec_mp4 = "loadvid.php?filename=".$rec_vid_files[0];
$rec_ogv = "loadvid.php?filename=".$rec_vid_files[1];
$rec_webm = "loadvid.php?filename=".$rec_vid_files[2];
$rec2_gif = "loadimg.php?rawgif=1&filename=".$rec_gif_files[1];
$rec2_mp4 = "loadvid.php?filename=".$rec_vid_files[3];
$rec2_ogv = "loadvid.php?filename=".$rec_vid_files[4];
$rec2_webm = "loadvid.php?filename=".$rec_vid_files[5];
$download_rec_mp4 = "downloadvid.php?filename=".$rec_vid_files[0];
$download_rec2_mp4 = "downloadvid.php?filename=".$rec_vid_files[3];
$manual_rec_gif = "loadimg.php?rawgif=1&filename=".$manual_rec_gif_files[0];
$manual_rec_mp4 = "loadvid.php?filename=".$manual_rec_vid_files[0];
$manual_rec_ogv = "loadvid.php?filename=".$manual_rec_vid_files[1];
$manual_rec_webm = "loadvid.php?filename=".$manual_rec_vid_files[2];
$download_manual_rec_mp4 = "downloadvid.php?filename=".$manual_rec_vid_files[0];

$html .= "
	<center><H3><b>Tilt-Series #".ltrim($tiltseries, '0')."<br>Coarse Alignment</b></H3></center>
	<hr />";
$html .= "
<center><H4>Tilt-Series Correlation Peaks</H4></center>
<br />";
if (isset($corrpeak_gif_files[0]) and isset($corrpeak_gif_files[1])) {
	$html .= '<center><b>Iteration 1 &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp Iteration 2</b></center>'.//lol
			  '<center><img src="'.$corrpeak_gif.'" alt="correlations" /> <img src="'.$corrpeak2_gif.'" alt="correlations2" />'."<br /></center>";
	$html .= '<p align="right"><a href="'.$download_corrpeak_mp4.'">Download Iteration 1 Video</a></p>';
	$html .= '<p align="right"><a href="'.$download_corrpeak2_mp4.'">Download Iteration 2 Video</a></p><br /><br /><hr />';
} elseif (isset($corrpeak_gif_files[0])) {
	$html .= '<center><img src="'.$corrpeak_gif.'" alt="correlations" />'."<br /></center>";
	$html .= '<p align="right"><a href="'.$download_corrpeak_mp4.'">Download Video</a></p><br /><br /><hr />';
} elseif (isset($corrpeak_vid_files[0]) and isset($corrpeak_vid_files[3])){
	$html .= '<center><video id="corrpeakVideos" autoplay loop>
		  <source src="'.$corrpeak_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$corrpeak_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$corrpeak_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<center><video id="corrpeakVideos2" autoplay loop>
		  <source src="'.$corrpeak2_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$corrpeak2_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$corrpeak2_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<p align="right"><a href="'.$download_corrpeak_mp4.'">Download Iteration 1 Video</a></p>';
	$html .= '<p align="right"><a href="'.$download_corrpeak2_mp4.'">Download Iteration 2 Video</a></p><hr />';
} elseif (isset($corrpeak_vid_files[0])){
	$html .= '<center><video id="corrpeakVideos" autoplay loop>
		  <source src="'.$corrpeak_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$corrpeak_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$corrpeak_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<p align="right"><a href="'.$download_corrpeak_mp4.'">Download Video</a></p><hr />';
} else {
	$html .= "<center><b>Depiction Correlation Peak Video for Coarse Alignment either failed to generate or is still processing</b></center>";
}

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
	$html .= '</tr><tr></table><br><hr />';
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
if (isset($tilt_gif_files[0]) and isset($tilt_gif_files[1]) and isset($manual_tilt_gif_files[0])) {
	$html .= '<center><img src="'.$tilt_gif.'" alt="tiltseries" /> <img src="'.$manual_tilt_gif.'" alt="manualtiltseries" /> <img src="'.$tilt2_gif.'" alt="tiltseries2" />'."<br /></center>";
	$html .= '<p align="right"><a href="'.$download_tilt_mp4.'">Download Iteration 1 Video</a></p><br /><br />';
	$html .= '<p align="right"><a href="'.$download_manual_tilt_mp4.'">Download Manual Alignment Video</a></p><br /><br />';
	$html .= '<p align="right"><a href="'.$download_tilt2_mp4.'">Download Iteration 2 Video</a></p><br /><br /><hr />';
} elseif (isset($tilt_gif_files[0]) and isset($manual_tilt_gif_files[0])) {
	$html .= '<center><img src="'.$tilt_gif.'" alt="tiltseries" /> <img src="'.$manual_tilt_gif.'" alt="manualtiltseries" />'."<br /></center>";
	$html .= '<p align="right"><a href="'.$download_tilt_mp4.'">Download Iteration 1 Video</a></p><br /><br />';
	$html .= '<p align="right"><a href="'.$download_manual_tilt_mp4.'">Download Manual Alignment Video</a></p><br /><br />';
} elseif (isset($tilt_gif_files[0]) and isset($tilt_gif_files[1])) {
	$html .= '<center><img src="'.$tilt_gif.'" alt="tiltseries" /> <img src="'.$tilt2_gif.'" alt="tiltseries2" />'."<br /></center>";
	$html .= '<p align="right"><a href="'.$download_tilt_mp4.'">Download Iteration 1 Video</a></p><br /><br />';
	$html .= '<p align="right"><a href="'.$download_tilt2_mp4.'">Download Iteration 2 Video</a></p><br /><br /><hr />';
} elseif (isset($tilt_gif_files[0])) {
	$html .= '<center><img src="'.$tilt_gif.'" alt="tiltseries" />'."<br /></center>";
	$html .= '<p align="right"><a href="'.$download_tilt_mp4.'">Download Video</a></p><br /><br /><hr />';
} elseif (isset($tilt_vid_files[0]) and isset($tilt_vid_files[3]) and isset($manual_tilt_vid_files[0])){
	$html .= '<center><b>Iteration 1</b></center>
		  <center><video id="tiltVideos" controls autoplay loop>
		  <source src="'.$tilt_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$tilt_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$tilt_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<center><b>Manual</b></center>
		  <center><video id="manualTiltVideos" controls autoplay loop>
		  <source src="'.$manual_tilt_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$manual_tilt_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$manual_tilt_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<center><b>Iteration 2</b></center>
		  <center><video id="tiltVideos2" controls autoplay loop>
		  <source src="'.$tilt2_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$tilt2_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$tilt2_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<p align="right"><a href="'.$download_tilt_mp4.'">Download Iteration 1 Video</a></p>';
	$html .= '<p align="right"><a href="'.$download_manual_tilt_mp4.'">Download Manual Alignment Video</a></p>';
	$html .= '<p align="right"><a href="'.$download_tilt2_mp4.'">Download Iteration 2 Video</a></p><hr />';
} elseif (isset($tilt_vid_files[0]) and isset($manual_tilt_vid_files[0])){
	$html .= '<center><b>Iteration 1</b></center>
		  <center><video id="tiltVideos" controls autoplay loop>
		  <source src="'.$tilt_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$tilt_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$tilt_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<center><b>Manual</b></center>
		  <center><video id="manualTiltVideos" controls autoplay loop>
		  <source src="'.$manual_tilt_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$manual_tilt_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$manual_tilt_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<p align="right"><a href="'.$download_tilt_mp4.'">Download Iteration 1 Video</a></p>';
	$html .= '<p align="right"><a href="'.$download_manual_tilt_mp4.'">Download Manual Alignment Video</a></p>';
} elseif (isset($tilt_vid_files[0]) and isset($tilt_vid_files[3])){
	$html .= '<center><b>Iteration 1</b></center>
		  <center><video id="tiltVideos" controls autoplay loop>
		  <source src="'.$tilt_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$tilt_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$tilt_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<center><b>Iteration 2</b></center>
		  <center><video id="tiltVideos2" controls autoplay loop>
		  <source src="'.$tilt2_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$tilt2_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$tilt2_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<p align="right"><a href="'.$download_tilt_mp4.'">Download Iteration 1 Video</a></p>';
	$html .= '<p align="right"><a href="'.$download_tilt2_mp4.'">Download Iteration 2 Video</a></p><hr />';
} elseif (isset($tilt_vid_files[0])){
	$html .= '<center><video id="tiltVideos" controls autoplay loop>
		  <source src="'.$tilt_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$tilt_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$tilt_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<p align="right"><a href="'.$download_tilt_mp4.'">Download Video</a></p><hr />';
} else {
	$html .= "<center><b>Depiction Tilt-Series Video for Coarse Alignment either failed to generate, is still processing, or wasn't requested</b></center>";
}

$html .= "
<br />
<center><H4>Tilt-Series Reconstruction After Coarse Alignment</H4></center>
<br />";
if (isset($rec_gif_files[0]) and isset($rec_gif_files[1]) and isset($manual_rec_gif_files[1])) {
	$html .= '<center><img src="'.$rec_gif.'" alt="reconstruction" /> <img src="'.$manual_rec_gif.'" alt="manualreconstruction" /> <img src="'.$rec2_gif.'" alt="reconstruction2" />'."<br /></center>";
	$html .= '<p align="right"><a href="'.$download_rec_mp4.'">Download Iteration 1 Video</a></p><br /><br />';
	$html .= '<p align="right"><a href="'.$download_manual_rec_mp4.'">Download Manual Alignment Video</a></p><br /><br />';
	$html .= '<p align="right"><a href="'.$download_rec2_mp4.'">Download Iteration 2 Video</a></p><br /><br /><hr />';
} elseif (isset($rec_gif_files[0]) and isset($manual_rec_gif_files[1])) {
	$html .= '<center><img src="'.$rec_gif.'" alt="reconstruction" /> <img src="'.$manual_rec_gif.'" alt="manualreconstruction" />'."<br /></center>";
	$html .= '<p align="right"><a href="'.$download_rec_mp4.'">Download Iteration 1 Video</a></p><br /><br />';
	$html .= '<p align="right"><a href="'.$download_manual_rec_mp4.'">Download Manual Alignment Video</a></p><br /><br /><hr />';
} elseif (isset($rec_gif_files[0]) and isset($rec_gif_files[1])) {
	$html .= '<center><img src="'.$rec_gif.'" alt="reconstruction" /> <img src="'.$rec2_gif.'" alt="reconstruction2" />'."<br /></center>";
	$html .= '<p align="right"><a href="'.$download_rec_mp4.'">Download Iteration 1 Video</a></p><br /><br />';
	$html .= '<p align="right"><a href="'.$download_rec2_mp4.'">Download Iteration 2 Video</a></p><br /><br /><hr />';
} elseif (isset($rec_gif_files[0])) {
	$html .= '<center><img src="'.$rec_gif.'" alt="reconstruction" />'."<br /></center>";
	$html .= '<p align="right"><a href="'.$download_rec_mp4.'">Download Video</a></p><br /><br /><hr />';
} elseif (isset($rec_vid_files[0]) and isset($rec_vid_files[3]) and isset($manual_rec_vid_files[0])){
	$html .= '<center><b>Iteration 1</b></center>
		  <center><video id="reconVideos" controls autoplay loop>
		  <source src="'.$rec_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$rec_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$rec_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<center><b>Manual</b></center>
		  <center><video id="manualreconVideos" controls autoplay loop>
		  <source src="'.$rec2_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$rec2_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$rec2_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<center><b>Iteration 2</b></center>
		  <center><video id="reconVideos2" controls autoplay loop>
		  <source src="'.$rec2_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$rec2_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$rec2_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<p align="right"><a href="'.$download_rec_mp4.'">Download Iteration 1 Video</a></p>';
	$html .= '<p align="right"><a href="'.$download_manual_rec_mp4.'">Download Manual Alignment Video</a></p>';
	$html .= '<p align="right"><a href="'.$download_rec2_mp4.'">Download Iteration 2 Video</a></p><hr />';
} elseif (isset($rec_vid_files[0]) and isset($manual_rec_vid_files[0])){
	$html .= '<center><b>Iteration 1</b></center>
		  <center><video id="reconVideos" controls autoplay loop>
		  <source src="'.$rec_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$rec_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$rec_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<center><b>Manual</b></center>
		  <center><video id="manualreconVideos" controls autoplay loop>
		  <source src="'.$rec2_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$rec2_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$rec2_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<p align="right"><a href="'.$download_rec_mp4.'">Download Iteration 1 Video</a></p>';
	$html .= '<p align="right"><a href="'.$download_manual_rec_mp4.'">Download Manual Alignment Video</a></p><hr />';
} elseif (isset($rec_vid_files[0]) and isset($rec_vid_files[3])){
	$html .= '<center><b>Iteration 1</b></center>
		  <center><video id="reconVideos" controls autoplay loop>
		  <source src="'.$rec_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$rec_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$rec_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<center><b>Iteration 2</b></center>
		  <center><video id="reconVideos2" controls autoplay loop>
		  <source src="'.$rec2_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$rec2_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$rec2_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<p align="right"><a href="'.$download_rec_mp4.'">Download Iteration 1 Video</a></p>';
	$html .= '<p align="right"><a href="'.$download_rec2_mp4.'">Download Iteration 2 Video</a></p><hr />';
} elseif (isset($rec_vid_files[0])){
	$html .= '<center><video id="reconVideos" controls autoplay loop>
		  <source src="'.$rec_mp4.'" type="video/mp4" loop>'.'<br />
		  <source src="'.$rec_webm.'" type="video/webm" loop>'.'<br />
		  <source src="'.$rec_ogv.'" type="video/ogg" loop>'.'<br />
		  HTML5 video is not supported by your browser.
		  </video></center>';
	$html .= '<p align="right"><a href="'.$download_rec_mp4.'">Download Video</a></p><hr />';
} else {
	$html .= "<center><b>Depiction Reconstruction Video for Coarse Alignment either failed to generate, is still processing, or wasn't requested</b></center>";
}


echo $html
?>
</body>
</html>
