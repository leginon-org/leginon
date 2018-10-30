<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */
ini_set('display_errors', '0');     # don't show any errors...
error_reporting(E_ALL | E_STRICT);

require_once "basicLayoutForm.inc";
require_once "inc/leginon.inc";
require_once "inc/html_elements.inc";

ini_set('session.gc_maxlifetime', 604800);
session_set_cookie_params(604800);

$page = $_SERVER['REQUEST_URI'];
header("Refresh: 300; URL=$page");

session_start();
$tiltseries=$_SESSION['tiltseries'];
$sessionname=$_SESSION['sessionname'];
$outdir=$_SESSION['outdir'];
$runname=$_SESSION['runname'];
$iters=$_SESSION['iters'];
$imageinfo=$_SESSION['imageinfo'];
$thickness=$_SESSION['thickness'];
$preset_size = $_SESSION['preset_size'];
$preset_search = $_SESSION['preset_search'];
$preset_type = $_SESSION['preset_type'];

class Protomo2RefineSummary extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML )
	{
		parent::__construct($expId, $extraHTML);
		//print "_POST:" . "<br>";
		//var_dump($_POST);
		//print "_GET:" . "<br>";
		//var_dump($_GET);
		//print "_SESSION:" . "<br>";
		//var_dump($_SESSION);
		
		$_POST['runname']=$_SESSION['runname'];
		$_POST['outdir']=$_SESSION['outdir'];
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//

		
		// Set the publications to be references on the web pages
		$pubList = array('appion-protomo', 'protomo');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'protomorun' );
		$this->setTitle( 'Protomo Refinement Summary' );
		$this->setHeading( 'Protomo Refinement Summary' );
		$this->setExeFile( '' );
		$this->setGuideURL( "https://github.com/nysbc/appion-protomo#example" );
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
		global $tiltseries;
		
		$defocus_gif_files = glob("$outdir/$runname/defocus_estimation/*/*/diagnostic.gif");
		$ctf_gif_files = glob("$outdir/$runname/media/ctf_correction/s*.gif");
		$dose_gif_files = glob("$outdir/$runname/media/dose_compensation/s*.gif");
		$corrpeak_gif_files = glob("$outdir/$runname/media/correlations/s*.gif");
		$corrpeak_vid_files = glob("$outdir/$runname/media/correlations/s*.{mp4,ogv,webm}",GLOB_BRACE);
		$recon_files = glob("$outdir/$runname/recons_*/*.mrc",GLOB_BRACE);
		$stack_files = glob("$outdir/$runname/stack*/*.mrcs",GLOB_BRACE);
		$qa_gif_file = "$outdir/$runname/media/quality_assessment/series".sprintf('%04d',$tiltseries)."_quality_assessment.gif";
		$azimuth_gif_file = "$outdir/$runname/media/angle_refinement/series".sprintf('%04d',$tiltseries)."_azimuth.gif";
		$orientation_gif_file = "$outdir/$runname/media/angle_refinement/series".sprintf('%04d',$tiltseries)."_orientation.gif";
		$elevation_gif_file = "$outdir/$runname/media/angle_refinement/series".sprintf('%04d',$tiltseries)."_elevation.gif";
		
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
	<center><H4><b>Quality Assessment ".docpop('quality_assessment', '(Info)')."</b></H4></center>
	<hr />";
		if (count($corrpeak_gif_files) > 0 or count($corrpeak_vid_files) > 0)
		{
			$html .= '<table id="" class="display" cellspacing="0" border="0" width="100%">';
			$html .= '<tr><td rowspan="3">';
			$html .= '<center><a href="protomo2QualityAssessmentPlots.php?outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$qa_gif.'" alt="qa" width="700" />'."</a></center>";
			$html .= '<center>'.docpop('quality_assessment2', 'CCMS Info').'</center><br></td>';
			$html .= '<td><center><a href="protomo2QualityAssessmentPlots.php?outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$azimuth_gif.'" alt="azimuth" width="270" />'."</a></center></td></tr>";
			$html .= '<td><center><a href="protomo2QualityAssessmentPlots.php?outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$orientation_gif.'" alt="theta" width="270" />'."</a></center></td></tr>";
			$html .= '<td><center><a href="protomo2QualityAssessmentPlots.php?outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$elevation_gif.'" alt="elevation" width="270" />'."</a></center></td></tr>";
			$html .= '</tr></td></table>';
		}
		
		if (isset($defocus_gif_files[0])) {
			$html .= "
	<br /><hr />
	<center><H4><b>Defocus Estimation</b></H4></center>
	<hr />";
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
			$html .= '<center>'.docpop('defocus_estimate_info', 'Image Info').'</center><br>';
		}
		
		if (isset($ctf_gif_files[0])) {
			$html .= "
		<br />	
		<center><H4>CTF Correction</H4></center>
		<br />";
			$html .= '<center><table id="" class="display" cellspacing="0" border="0"><tr>';
			$html .= '<td><a href="protomo2QualityAssessmentPlots.php?outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$ctfdefocus_gif.'" alt="ctfdefocus_gif" width="300" />'."</a><br /></td>";
			$html .= '<td><a href="protomo2QualityAssessmentPlots.php?outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$ctfplot_gif.'" alt="ctfplot_gif" width="300" />'."</a><br /></td>";
			$html .= '</tr><tr></table></center><br>';
			$html .= '<center>'.docpop('ctfplot_info', 'Image Info').'</center><br><hr />';
		}
		
		if (isset($dose_gif_files[0])) {
			$html .= "
		<br />	
		<center><H4>Dose Compensation</H4></center>
		<br />";
			$html .= '<center><table id="" class="display" cellspacing="0" border="0"><tr>';
			$html .= '<td><a href="protomo2QualityAssessmentPlots.php?outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$dose_gif.'" alt="dose_gif" width="300" />'."</a><br /></td>";
			$html .= '<td><a href="protomo2QualityAssessmentPlots.php?outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$dosecomp_gif.'" alt="dosecomp_gif" width="300" />'."</a><br /></td>";
			$html .= '</tr><tr></table></center><br>';
			$html .= '<center>'.docpop('doseplot_info', 'Image Info').'</center><br><hr />';
		}
		
		// Table of all of the correlation peaks for easy identification of bad alignment iterations
		$html .= "
	<hr />
	<center><H4><b>Correlation Peaks for Each Iteration ".docpop('corrimageinfo_refine', '(Info)')."</b></H4></center>
	<hr />";
		
		$i = 0;
		$j = -1;
		$numcolumns=5;
		$html .= '<table id="" class="display" cellspacing="0" border="1" align="center">';
		$html .= "<tr>";
		if (count($corrpeak_gif_files) > 0)
		{
			do {
				foreach ($corrpeak_gif_files as $corr)
				{
					$ite=$i+1;
					if ($ite <= count($corrpeak_gif_files) AND $ite > 0) {
						$html .= '<th><a href="protomo2RefineIterationSummary.php?iter='.$ite.'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank">Iteration #'.$ite.'</a></th>';
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
						$html .= '<td><center><a href="protomo2RefineIterationSummary.php?iter='.$ite.'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$corrpeak_gif.'"/></a></center></td>';
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
						$html .= '<th><a href="protomo2RefineIterationSummary.php?iter='.$ite.'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank">Iteration #'.$ite.'</a></th>';
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
						$html .= '<td><center><a href="protomo2RefineIterationSummary.php?iter='.$ite.'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank">
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
		$html .= '</tr><tr></table><br>';
		
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
			$html .= '<br>';
		}

		// Only display link to next step in tomo processing if at least one iteration is complete
		if (max(count($corrpeak_gif_files),count($corrpeak_vid_files)) < 1)
		{
			$html .= openRoundBorder();
			$html .= "<table border='0'>";
			$html .= "<br></br>
				<b><center>[Refresh this page after at least one Refinement iteration completes]</center><br></b>";
			$html .= "<br></br>
				<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineForm'><b><center><font size='5'>←</font> [Click here to go back to <font size='4'>Refinement</font>]</center></b></a><br>";
			$html .= "<br></tr>\n";
			$html .= "</table>\n";
			$html .= closeRoundBorder();
		} else {
			$html .= "<br><hr /><br>";
			$html .= openRoundBorder();
			$html .= "<table border='0'>";
			$html .= "<br></br>
				<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2ReconstructionForm'><b><center>[Click here to continue onto <font size='4'>Reconstruction</font> if protomo2aligner.py has finished <br>and you're happy with the alignment of at least one iteration] <font size='5'>→</font></center></b></a>";
			$html .= "<br></br>
				<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineForm'><b><center><font size='5'>←</font> [Click here to go back to <font size='4'>Refinement</font>]</center></b></a><br>";
			$html .= "<br></tr>\n";
			$html .= "</table>\n";
			$html .= closeRoundBorder();
		}
			
		return $html;
	}	
	
	// Use form footer to re-direct user
	// to the next step of the Protomo workflow.
	public function generateFormFooter( $postArray )
	{	
		global $tiltseries;
		global $sessionname;
		global $runname;
		global $outdir;
		global $iters;
		global $thickness;
		global $imageinfo;

		$_SESSION['thickness'] = $thickness;
		$_SESSION['tiltseries'] = $tiltseries;
		$_SESSION['runname'] = $runname;
		$_SESSION['sessionname'] = $sessionname;
		$_SESSION['outdir'] = $outdir;
		$_SESSION['iters'] = $iters;
		$_SESSION['imageinfo'] = $imageinfo;
		$_SESSION['erase_refine'] = 1;
		$_SESSION['restart_cycle'] = $iters;
		$_SESSION['preset_size'] = $preset_size;
		$_SESSION['preset_search'] = $preset_search;
		$_SESSION['preset_type'] = $preset_type;
		
		$html .= openRoundBorder();
		$html .= "<table border='0'>";
		$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2ReconstructionForm'><b><center>[Click here to continue onto <font size='4'>Reconstruction</font> if protomo2aligner.py has finished <br>and you're happy with the alignment of at least one iteration] <font size='5'>→</font></center></b></a>";
		$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineForm'><b><center><font size='5'>←</font> [Click here to go back to <font size='4'>Refinement</font>]</center></b></a><br>";
		$html .= "<br></tr>\n";
		$html .= "</table>\n";
		$html .= closeRoundBorder();

		return $html;
	}
}
?>
