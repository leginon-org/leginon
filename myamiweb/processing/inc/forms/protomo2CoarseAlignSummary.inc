<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */
ini_set('display_errors', '0');     # don't show any errors...
error_reporting(E_ALL | E_STRICT);

require_once "basicLayoutForm.inc";
require_once "inc/leginon.inc";

ini_set('session.gc_maxlifetime', 604800);
session_set_cookie_params(604800);

session_start();
$tiltseries=$_SESSION['tiltseries'];
$sessionname=$_SESSION['sessionname'];
$outdir=$_SESSION['outdir'];
$runname=$_SESSION['runname'];
$imageinfo=$_SESSION['imageinfo'];

class Protomo2CoarseAlignSummary extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML, $tiltseries='' )
	{
		parent::__construct($expId, $extraHTML);
		//print "_POST:" . "<br>";
		//var_dump($_POST);
		//print "_GET:" . "<br>";
		//var_dump($_GET);
		//print "_SESSION:" . "<br>";
		//var_dump($_SESSION);
		
		$tiltseries=$_SESSION['tiltseries'];
		$_POST['runname']=$_SESSION['runname'];
		$_POST['outdir']=$_SESSION['outdir'];
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//

		
		// Set the publications to be references on the web pages
		$pubList = array('appion-protomo', 'protomo');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'protomorun' );
		$this->setTitle( 'Protomo Coarse Alignment Summary' );
		$this->setHeading( 'Protomo Coarse Alignment Summary' );
		$this->setExeFile( '' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Align_Tilt-Series" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
	}
	
	// Display plots and videos
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		global $outdir;
		global $runname;
		
		$ctf_gif_files = glob("$outdir/$runname/media/ctf_correction/s*.gif");
		$dose_gif_files = glob("$outdir/$runname/media/dose_compensation/s*.gif");
		$corrpeak_gif_files = glob("$outdir/$runname/media/correlations/c*.gif");
		$corrpeak_vid_files = glob("$outdir/$runname/media/correlations/c*.{mp4,ogv,webm}",GLOB_BRACE);
		$initial_tilt_gif_files = glob("$outdir/$runname/media/tiltseries/i*.gif");
		$initial_tilt_vid_files = glob("$outdir/$runname/media/tiltseries/i*.{mp4,ogv,webm}",GLOB_BRACE);
		$tilt_gif_files = glob("$outdir/$runname/media/tiltseries/c*.gif");
		$tilt_vid_files = glob("$outdir/$runname/media/tiltseries/c*.{mp4,ogv,webm}",GLOB_BRACE);
		$rec_gif_files = glob("$outdir/$runname/media/reconstructions/c*.gif");
		$rec_vid_files = glob("$outdir/$runname/media/reconstructions/c*.{mp4,ogv,webm}",GLOB_BRACE);
		
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
		
		if (isset($ctf_gif_files[0])) {
			$html .= "
		<br />	
		<center><H4>CTF Correction</H4></center>
		<br />";
			$html .= '<center><table id="" class="display" cellspacing="0" border="0"><tr>';
			$html .= '<td><img src="'.$ctfdefocus_gif.'" alt="ctfdefocus_gif" width="400" />'."<br /></td>";
			$html .= '<td><img src="'.$ctfplot_gif.'" alt="ctfplot_gif" width="400" />'."<br /></td>";
			$html .= '</tr><tr></table></center><br>';
			$html .= '<center>'.docpop('ctfplot_info', 'Image Info').'</center><br><hr />';
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
			$html .= '<center>'.docpop('doseplot_info', 'Image Info').'</center><br><hr />';
		}
		
		$html .= "
	<br />
	<center><H4>Tilt-Series Correlation Peaks</H4></center>
	<br />";
		if (isset($corrpeak_gif_files[0])) {
			$html .= '<center><img src="'.$corrpeak_gif.'" alt="correlations" />'."<br /></center>";
			$html .= '<center>'.docpop('corrimageinfo_coarse', 'Image Info').'</center>';
			$html .= '<p align="right"><a href="'.$download_corrpeak_mp4.'">Download Video</a></p><br /><br /><hr />';
		} elseif (isset($corrpeak_vid_files[0])){
			$html .= '<center><video id="corrpeakVideos" autoplay loop>
				  <source src="'.$corrpeak_mp4.'" type="video/mp4" loop>'.'<br />
				  <source src="'.$corrpeak_webm.'" type="video/webm" loop>'.'<br />
				  <source src="'.$corrpeak_ogv.'" type="video/ogg" loop>'.'<br />
				  HTML5 video is not supported by your browser.
				  </video></center>';
			$html .= '<center>'.docpop('corrimageinfo_coarse', 'Image Info').'</center>';
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
			$html .= '<center>'.docpop('initialtiltimageinfo_coarse', 'Image Info').'<br /><br /></center>';
			$html .= '<p align="right"><a href="'.$download_initial_tilt_mp4.'">Download Video</a></p><br /><br />';
		} elseif (isset($initial_tilt_vid_files[0])){
			$html .= '<center><video id="initialTiltVideos" controls autoplay loop>
				  <source src="'.$initial_tilt_mp4.'" type="video/mp4" loop>'.'<br />
				  <source src="'.$initial_tilt_webm.'" type="video/webm" loop>'.'<br />
				  <source src="'.$initial_tilt_ogv.'" type="video/ogg" loop>'.'<br />
				  HTML5 video is not supported by your browser.
				  </video></center>';
			$html .= '<center>'.docpop('initialtiltimageinfo_coarse', 'Image Info').'</center>';
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
			$html .= '<center>'.docpop('tiltimageinfo_coarse', 'Image Info').'</center>';
			$html .= '<p align="right"><a href="'.$download_tilt_mp4.'">Download Video</a></p><br /><br /><hr />';
		} elseif (isset($tilt_vid_files[0])){
			$html .= '<center><video id="tiltVideos" controls autoplay loop>
				  <source src="'.$tilt_mp4.'" type="video/mp4" loop>'.'<br />
				  <source src="'.$tilt_webm.'" type="video/webm" loop>'.'<br />
				  <source src="'.$tilt_ogv.'" type="video/ogg" loop>'.'<br />
				  HTML5 video is not supported by your browser.
				  </video></center>';
			$html .= '<center>'.docpop('tiltimageinfo_coarse', 'Image Info').'</center>';
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
			$html .= '<center>'.docpop('reconimageinfo_coarse', 'Image Info').'<br /><br /></center>';
			$html .= '<p align="right"><a href="'.$download_rec_mp4.'">Download Video</a></p><br /><br /><hr />';
		} elseif (isset($rec_vid_files[0])){
			$html .= '<center><video id="reconVideos" controls autoplay loop>
				  <source src="'.$rec_mp4.'" type="video/mp4" loop>'.'<br />
				  <source src="'.$rec_webm.'" type="video/webm" loop>'.'<br />
				  <source src="'.$rec_ogv.'" type="video/ogg" loop>'.'<br />
				  HTML5 video is not supported by your browser.
				  </video></center>';
			$html .= '<center>'.docpop('reconimageinfo_coarse', 'Image Info').'</center>';
			$html .= '<p align="right"><a href="'.$download_rec_mp4.'">Download Video</a></p><hr />';
		} else {
			$html .= "<center><b>Depiction Reconstruction Video for Coarse Alignment either failed to generate, is still processing, or wasn't requested</b></center>";
		}
		
		// Only display link to next step in tomo processing if Coarse Alignment is complete
		if (max(count($corrpeak_gif_files),count($corrpeak_vid_files)) < 1)
		{
			$html .= "<br></br>
				<b><center>[Refresh this page after Coarse Alignment completes]</center><br></b>";
			$html .= "<br></br>
				<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2CoarseAlignForm'><b><center><font size='5'>←</font> [Click here to go back to <font size='4'>Coarse Alignment</font>]</center></b></a>";
		} else {
			$html .= "<br></br>
				<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineForm'><b><center>[Click here to continue onto <font size='4'>Refinement</font> if the Coarse Alignment results are satisfactory] <font size='5'>→</font></center></b></a>";
			$html .= "<br></br>
				<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2CoarseAlignForm'><b><center><font size='5'>←</font> [Click here to go back to <font size='4'>Coarse Alignment</font>]</center></b></a>";
		}
		
		return $html;
	}	
	
	// Override the default ShowReference function because the user needs to be re-directed
	// to the next step of the Protomo workflow.
	public function showReference( $postArray )
	{
		$html = parent::showReference( $postArray );
		
		global $tiltseries;
		global $sessionname;
		global $runname;
		global $outdir;
		global $imageinfo;
		
		$_SESSION['tiltseries'] = $tiltseries;
		$_SESSION['runname'] = $runname;
		$_SESSION['sessionname'] = $sessionname;
		$_SESSION['outdir'] = $outdir;
		$_SESSION['imageinfo'] = $imageinfo;
		$_SESSION['erase_coarse'] = 1;
		$_SESSION['restart_cycle'] = '';
		
		return $html;
	}
}
?>
