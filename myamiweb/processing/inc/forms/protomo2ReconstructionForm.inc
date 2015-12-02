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
if (isset($_GET['tiltseries'])) {  //If user is coming from batch
		$tiltseries=ltrim($_GET['tiltseries'], '0');
		$outdir=$_GET['rundir'];
		$runname='tiltseries'.$_GET['tiltseries'];
		$_SESSION['from_batch']=1;
}else{
		$tiltseries=$_SESSION['tiltseries'];
		$outdir=$_SESSION['outdir'];
		$runname=$_SESSION['runname'];
}
$refine_thickness=$_SESSION['thickness'];
$sessionname=$_SESSION['sessionname'];
$imageinfo=$_SESSION['imageinfo'];
$protomo_outdir = $_SESSION['protomo_outdir'];
$preset_size = $_SESSION['preset_size'];
$preset_search = $_SESSION['preset_search'];
$preset_type = $_SESSION['preset_type'];
$unselect=0;
if (!isset($_SESSION['iter']) or ($_SESSION['erase_refine'] == 1)) {
	#Find the last iteration
	for($iter = 1000; $iter > 0; $iter--)
	{
		$corr_gif_files = glob("$outdir/$runname/media/corrplots/series".sprintf('%04d',$tiltseries).sprintf('%03d',$iter-1)."*.gif");
		if (isset($corr_gif_files[0])) {
			$_SESSION['iter'] = $_SESSION['iters'] = $iter;
			break;
			}
	}
}else{
	#User chose a different iteration. Still need to count total number of iterations
	for($iters = 1000; $iters > 0; $iters--)
	{
		$count_iters = glob("$outdir/$runname/media/corrplots/series".sprintf('%04d',$tiltseries).sprintf('%03d',$iters-1)."*.gif");
		if (isset($count_iters[0])) {
			$_SESSION['iters'] = $iters;
			$unselect=1;
			break;
			}
	}
}
if ($_SESSION['erase_refine'] == 1){  //Just using erase_refine as a token
	$_SESSION['erase_refine'] = 0;
}

class Protomo2ReconstructionForm extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML, $commit='false', $negative='', $positive='', $recon_iter='', $recon_map_sampling='2',
	$recon_map_size_x='2048', $recon_map_size_y='2048',	$recon_thickness='1500', $pixelsize='', $recon_lowpass='', $recon_lp_diam_x='15',
	$recon_lp_diam_y='15', $ctf_correct='', $amp_contrast='0.07', $iWidth='20', $DefocusTol='200', $dose_presets='', $dose_a='',
	$dose_b='', $dose_c='', $link_recon='', $frame_aligned='')
	{
		parent::__construct($expId, $extraHTML);
		//print "_POST:" . "<br>";
		//var_dump($_POST);
		//print "_GET:" . "<br>";
		//var_dump($_GET);
		//print "_SESSION:" . "<br>";
		//var_dump($_SESSION);
		
		global $imageinfo;
		global $protomo_outdir;
		global $refine_thickness;
		$tiltseries=$_SESSION['tiltseries'];
		$_POST['runname']=$_SESSION['runname'];
		$_POST['outdir']=$_SESSION['outdir'];
		$_POST['protomo_outdir']=$_SESSION['protomo_outdir'];
		$_POST['pixelsize'] = $imageinfo['pixelsize']*pow(10,10);
		$recon_iter=$_SESSION['iter'];
		$recon_map_size_x = $imageinfo['dimx'];
		$recon_map_size_y = $imageinfo['dimy'];
		$recon_thickness = $refine_thickness;
		$recon_lp_diam_x = round(pow(10,10)*$imageinfo['pixelsize']*8);
		$recon_lp_diam_y = round(pow(10,10)*$imageinfo['pixelsize']*8);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('appion-protomo', 'protomo', 'imodctf', 'dose_comp');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'protomorun' );
		$this->setTitle( 'Protomo Reconstruction Launcher' );
		$this->setHeading( 'Protomo Reconstruction' );
		$this->setExeFile( 'protomo2reconstruction.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Align_Tilt-Series" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "protomo" );
		
		$params->addParam( "ctf_correct", $ctf_correct, "Correct for CTF" );
		$params->addParam( "amp_contrast", $amp_contrast, "Amplitude Contrast" );
		$params->addParam( "iWidth", $iWidth, "Interpolation Width" );
		$params->addParam( "DefocusTol", $DefocusTol, "Defocus Tolerance" );
		$params->addParam( "dose_presets", $dose_presets, "Dose Compensation Type" );
		$params->addParam( "dose_a", $dose_a, "a" );
		$params->addParam( "dose_b", $dose_b, "b" );
		$params->addParam( "dose_c", $dose_c, "c" );
		$params->addParam( "frame_aligned", $frame_aligned, "Use Frame Aligned Images" );
		$params->addParam( "negative", $negative, "<strong>–</strong> Angle Limit" );
		$params->addParam( "positive", $positive, "<strong>+</strong> Angle Limit" );
		$params->addParam( "recon_iter", $recon_iter, "Refinement Iteration used to generate Reconstruction" );
		$params->addParam( "recon_map_sampling", $recon_map_sampling, "Reconstruction Sampling" );
		$params->addParam( "recon_map_size_x", $recon_map_size_x, "Reconstruction Size (x)" );
		$params->addParam( "recon_map_size_y", $recon_map_size_y, "Reconstruction Size (y)" );
		$params->addParam( "recon_thickness", $recon_thickness, "Reconstruction Thickness" );
		$params->addParam( "recon_lowpass", $recon_lowpass, "Lowpass Filter" );
		$params->addParam( "recon_lp_diam_x", $recon_lp_diam_x, "(x)" );
		$params->addParam( "recon_lp_diam_y", $recon_lp_diam_y, "(y)" );
		$params->addParam( "link_recon", $link_recon, "Link Final Reconstruction to this Directory" );
		
		// Validations
		$params->addValidation( "recon_iter", "req" );
		$params->addValidation( "recon_iter", "num" );
		
	}
	
	// Generate a form for the parameters that are specific to this program (not Appion params)
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		global $unselect;
		global $outdir;
		global $runname;
		
		$fieldSize = 5;
		$fieldSize2 = 30;
		
		$best_file = glob("$outdir/$runname/best.*");
		$bestbin1or2_file = glob("$outdir/$runname/bestbin1or2.*");
		$worst_file = glob("$outdir/$runname/worst.*");
		$best = pathinfo($best_file[0], PATHINFO_EXTENSION);
		$bestbin1or2 = pathinfo($bestbin1or2_file[0], PATHINFO_EXTENSION);
		$worst = pathinfo($worst_file[0], PATHINFO_EXTENSION);
		
		$html .= "
		<br />
		<H4>CTF Correction Parameters ".docpop('ctf_info', '(Info)')."</H4>
		<hr />";
		$html.= '<select name="ctf_correct" style="width:66px">';
		$html.= '<option value="True">True</option>';
		$html.= '<option selected value="False">False</option>';
		$html.= '</select>'; $html.= docpop('ctf_correct', ' Correct for CTF').'<br>';
		$html.= '<select name="frame_aligned" style="width:66px">';
		$html.= '<option selected value="True">True</option>';
		$html.= '<option value="False">False</option>';
		$html.= '</select>'; $html.= docpop('protomo_frame_aligned', ' Use Frame Aligned Images').'<br>';
		$html.= $params->insertTextField( "amp_contrast", $fieldSize );
		$html.= $params->insertTextField( "iWidth", $fieldSize );
		$html.= $params->insertTextField( "DefocusTol", $fieldSize );
		
		$html .= "
		<br>
		<H4>Dose Compensation Parameters ".docpop('dose_info', '(Info)')."</H4>
		<hr />";
		
		$html.= '<select name="dose_presets" style="width:66px">';
		$html.= '<option selected value="False">None</option>';
		$html.= '<option value="Light">Light</option>';
		$html.= '<option value="Moderate">Moderate</option>';
		$html.= '<option value="Heavy">Heavy</option>';
		$html.= '<option value="Custom">Custom</option>';
		$html.= '</select>'; $html.= docpop('dose_presets', ' Dose Compensation Type').'<br>';
		$html.= $params->insertTextFieldInRow( "dose_a", $fieldSize ).'│ ';
		$html.= $params->insertTextFieldInRow( "dose_b", $fieldSize ).'│ ';
		$html.= $params->insertTextField( "dose_c", $fieldSize );
		
		$html .= "
	    <br />
	    <H4>Reconstruction Parameters ".docpop('recon_info2', '(Info)')."</H4>
	    <hr />";
		
		$html.= '<select name="recon_iter" onchange=submit() style="width:66px">';
		$html.= '<option value="'.$best.'">Best</option>';
		$html.= '<option value="'.$bestbin1or2.'">Best w/ bin=1or2</option>';
		$html.= '<option value="'.$worst.'">Worst</option>';
		for ($i=1; $i <= $_SESSION['iters']; $i++)
		{
			if ($i == $_SESSION['iter'] and $unselect == 0){
				$_SESSION['recon_iter'] = $_SESSION['iter'];
				$html.= '<option selected value="'.$i.'">'.$i.'</option>';
			}elseif ($i == $_POST['recon_iter']){
				$_SESSION['recon_iter'] = $_POST['recon_iter'];
				$html.= '<option selected value="'.$i.'">'.$i.'</option>';
			}else{
				$html.= '<option value="'.$i.'">'.$i.'</option>';
			}
		}
		$html.= '</select>'; $html.= docpop('protomo_recon_iter', ' Refinement Iteration used to generate Reconstruction<br>');
	    $html.= $params->insertTextField( "recon_map_sampling", $fieldSize );
		$html.= $params->insertTextField( "recon_map_size_x", $fieldSize );
		$html.= $params->insertTextField( "recon_map_size_y", $fieldSize );
		$html.= $params->insertTextField( "recon_thickness", $fieldSize );
		$html.= $params->insertTextFieldInRow( "negative", $fieldSize ).'│ ';
		$html.= $params->insertTextField( "positive", $fieldSize );
		$html.= '<select name="recon_lowpass" style="width:66px">';
		$html.= '<option value="True">True</option>';
		$html.= '<option selected value="False">False</option>';
		$html.= '</select>'; $html.= docpop('recon_lowpass', ' Lowpass Filter').'│ ';
		$html.= $params->insertTextFieldInRow( "recon_lp_diam_x", $fieldSize ).'│ ';
		$html.= $params->insertTextField( "recon_lp_diam_y", $fieldSize );
		$html.= $params->insertTextField( "link_recon", $fieldSize2 );
		
		$html .= "<hr />";
		
		global $outdir;
		global $runname;
		global $tiltseries;
		$corr_gif_files = glob("$outdir/$runname/media/corrplots/series".sprintf('%04d',$tiltseries).sprintf('%03d',$_SESSION['recon_iter']-1)."*.gif");
		
		$corr_coa = "loadimg.php?rawgif=1&filename=".$corr_gif_files[0];
		$corr_cofx = "loadimg.php?rawgif=1&filename=".$corr_gif_files[1];
		$corr_cofy = "loadimg.php?rawgif=1&filename=".$corr_gif_files[2];
		$corr_rot = "loadimg.php?rawgif=1&filename=".$corr_gif_files[3];
		$corr_scl = "loadimg.php?rawgif=1&filename=".$corr_gif_files[4];
		
		$html .= "<br>
			<H4><center><b>Correction Factor Plots for Iteration #".$_SESSION['recon_iter']." ".docpop('corrimageinfo_recon', '(Info)')."</b></center></H4>";
		$html .= '<br><center><table id="" class="display" cellspacing="0" border="1" width=650><tr>';
		$html .= '<th>Correction Factor (x)</th>';
		$html .= '<th>Correction Factor (y)</th>';
		$html .= "</tr><tr>";
		$html .= '<td><center><a href="protomo2RefineIterationSummary.php?iter='.$_SESSION['recon_iter'].'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$corr_cofx.'" alt="cofx" width="325" /></a></center></td>';
		$html .= '<td><center><a href="protomo2RefineIterationSummary.php?iter='.$_SESSION['recon_iter'].'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$corr_cofy.'" alt="cofy" width="325" /></a></center></td>';
		$html .= "</tr><tr>";
		$html .= '<th>Correction Factor for Rotation (degrees)</th>';
		$html .= '<th>Correction Factor for Scaling</th>';
		$html .= "</tr><tr>";
		$html .= '<td><center><a href="protomo2RefineIterationSummary.php?iter='.$_SESSION['recon_iter'].'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$corr_rot.'" alt="rot" width="325" /></a></center></td>';
		$html .= '<td><center><a href="protomo2RefineIterationSummary.php?iter='.$_SESSION['recon_iter'].'&outdir='.$outdir.'&runname='.$runname.'&tiltseries='.$tiltseries.'" target="_blank"><img src="'.$corr_scl.'" alt="scl" width="325" /></a></center></td>';
		$html .= '</tr><tr></table></center><br><hr />';

		// Only display link to next step in tomo processing if on completed Command page
		if ($_POST["process"] != "Just Show Command")
		{
			$html .= "<br></br>
			<b><center>[Enter all required parameters and click 'Just Show Command' to proceed]</center></b>";
		}
		
		return $html;
	}
	
	// Override the default build Command Function because the --test flag is not normal
	// for other Appion Loop methods and not included in the parent.
	public function buildCommand( $postArray )
	{
		$command   = parent::buildCommand( $postArray );
		
		global $tiltseries;
		global $sessionname;
		
		$pixelsize=$_POST['pixelsize'];
		$command.="--pixelsize=$pixelsize ";
		$command.="--tiltseries=$tiltseries ";
		$command.="--sessionname=$sessionname ";
		
		return $command." ";
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
		global $iters;
		global $imageinfo;

		$_SESSION['tiltseries'] = $tiltseries;
		$_SESSION['runname'] = $runname;
		$_SESSION['sessionname'] = $sessionname;
		$_SESSION['runname'] = $runname;
		$_SESSION['outdir'] = $outdir;
		$_SESSION['iters'] = $iters;
		$_SESSION['imageinfo'] = $imageinfo;
		$_SESSION['thickness'] = $_POST['thickness'];
		$_SESSION['preset_size'] = $preset_size;
		$_SESSION['preset_search'] = $preset_search;
		$_SESSION['preset_type'] = $preset_type;
		
		if ($_POST["process"] == "Just Show Command" and $_SESSION['from_batch'] == 0)
		{
			//$html .= "<br></br>
				//<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2UploadForm'><b><center>[Click here to continue on to <font size='4'>Upload your Reconstruction</font>] <font size='5'>→</font></center></center></b></a>";
			$html .= "<br>
				<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2BatchForm'><b><center>[Click here to use all previous parameter files for <font size='4'>Batch Refinement and Reconstruction</font> of this session's tilt-series] <font size='5'>→</font></center></center></b></a>";
		}	
		return $html;
	}
}
?>
