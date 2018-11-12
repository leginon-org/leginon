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

ini_set('session.gc_maxlifetime', 604800);
session_set_cookie_params(604800);

session_start();
if (isset($_GET['runname'])) {  //If user is coming from main summary
	$tiltseries=$_GET['tiltseries'];
	$outdir=$_GET['outdir'];
	$runname=$_GET['runname'];
	$_POST['runname']=$_GET['runname'];
	$_SESSION['runname']=$_GET['runname'];
}elseif (isset($_GET['tiltseries'])) {  //If user is coming from batch
	$tiltseries=ltrim($_GET['tiltseries'], '0');
	$outdir=$_GET['rundir'];
	$runname='tiltseries'.$_GET['tiltseries'];
	$_SESSION['from_batch']=1;
}else{
	$tiltseries=$_SESSION['tiltseries'];
	$outdir=$_SESSION['outdir'];
	$runname=$_SESSION['runname'];
}
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
	function __construct( $expId, $extraHTML, $commit='false', $reconstruction_actions='', $negative_recon='', $positive_recon='', $recon_iter='', $recon_map_sampling='4',
	$recon_map_size_x='2048', $recon_map_size_y='2048', $recon_thickness='2500', $pixelsize='', $recon_lowpass='', $recon_lp_diam_x='15',
	$recon_lp_diam_y='15', $ctf_correct='', $amp_contrast_ctf='0.07', $iWidth='20', $DefocusTol='200', $dose_presets='', $dose_a='',
	$dose_b='', $dose_c='', $link_recon='', $frame_aligned='', $reconstruction_method='', $tomo3d_procs='all', $tomo3d_options='',
	$tomo3d_sirt_iters='30', $exclude_images_by_angle='', $stack_procs='all', $bin_type='', $amp_correct='', $amp_correct_w1='0.67', $amp_correct_w2='0.33',
	$defocus_difference='250', $defocus_save_recon='', $pick_tomogram='', $dog_particle_diam='', $dog_diam_variance='5', $dog_max_picks='',
	$dog_junk_tolerance='5', $dog_lowpass_type='proc3d')
	{
		parent::__construct($expId, $extraHTML);
		//print "_POST:" . "<br>";
		//var_dump($_POST);
		//print "_GET:" . "<br>";
		//var_dump($_GET);
		//print "_SESSION:" . "<br>";
		//var_dump($_SESSION);
		
		global $html; //I can only get the selector form to pass variables properly by defining it globally in the constructor.
		
		if (!isset($_POST['reconstruction_actions'])) {$_POST['reconstruction_actions']=1;}
		$action_settings=array("Reconstruct", "CTF Correct > Reconstruct", "Dose Compensate > Reconstruct", "CTF Correct > Dose Compensate > Reconstruct");

		$html.= '<hr /><br><center><select name="reconstruction_actions" onchange=submit() style="width:225px">';
		for ($i = 1; $i < count($action_settings)+1; $i++) {
			$html.= '<option ';
			if ($i == $_POST['reconstruction_actions']) {
				$html.= 'selected ';
			}
			$html.= 'value="'.$i.'">'.$action_settings[$i-1].'</option>';
		}
		$html.= '</select>'; $html.= docpop('protomo_reconstruction_actions', ' Reconstruction Actions<br></center><br><hr />');
		
		if (!isset($_POST['reconstruction_method'])) {$_POST['reconstruction_method']=1;}
		$method_settings=array("Protomo weighted back-projection", "Tomo3D weighted back-projection", "Tomo3D SIRT", "Stack only");

		$html.= '<br><select name="reconstruction_method" onchange=submit() style="width:225px">';
		for ($i = 1; $i < count($method_settings)+1; $i++) {
			$html.= '<option ';
			if ($i == $_POST['reconstruction_method']) {
				$html.= 'selected ';
			}
			$html.= 'value="'.$i.'">'.$method_settings[$i-1].'</option>';
		}
		$html.= '</select>'; $html.= docpop('protomo_reconstruction_method', ' Reconstruction Method<br>');
		
		global $imageinfo;
		global $protomo_outdir;
		$tiltseries=$_SESSION['tiltseries'];
		$_POST['runname']=$_SESSION['runname'];
		$_POST['outdir']=$_SESSION['outdir'];
		$_POST['protomo_outdir']=$_SESSION['protomo_outdir'];
		$_POST['pixelsize'] = $imageinfo['pixelsize']*pow(10,10);
		$recon_iter=$_SESSION['iter'];
		$recon_map_size_x = $imageinfo['dimx'];
		$recon_map_size_y = $imageinfo['dimy'];
		$recon_lp_diam_x = round(pow(10,10)*$imageinfo['pixelsize']*8);
		$recon_lp_diam_y = round(pow(10,10)*$imageinfo['pixelsize']*8);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		if ($_POST['reconstruction_method'] == 1) {
			$pubList = array('appion-protomo', 'protomo', 'imodctf', 'dose_comp');
		} elseif ($_POST['reconstruction_method'] == 2 or $_POST['reconstruction_method'] == 3) {
			$pubList = array('appion-protomo', 'imodctf', 'dose_comp', 'tomo3d1', 'tomo3d2');
		} else {
			$pubList = array('appion-protomo', 'imodctf', 'dose_comp');
		}
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'protomorun' );
		$this->setTitle( 'Protomo Reconstruction Launcher' );
		$this->setHeading( 'Protomo Reconstruction' );
		$this->setExeFile( 'protomo2reconstruction.py' );
		$this->setGuideURL( "https://github.com/nysbc/appion-protomo#example" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "protomo" );
		
		$params->addParam( "ctf_correct", $ctf_correct, "Correct for CTF" );
		$params->addParam( "amp_contrast_ctf", $amp_contrast_ctf, "Amplitude Contrast" );
		$params->addParam( "iWidth", $iWidth, "Interpolation Width" );
		$params->addParam( "DefocusTol", $DefocusTol, "Defocus Tolerance" );
		$params->addParam( "dose_presets", $dose_presets, "Dose Compensation Type" );
		$params->addParam( "dose_a", $dose_a, "a" );
		$params->addParam( "dose_b", $dose_b, "b" );
		$params->addParam( "dose_c", $dose_c, "c" );
		$params->addParam( "stack_procs", $stack_procs, "Stack Making Processors" );
		$params->addParam( "tomo3d_procs", $tomo3d_procs, "Tomo3D Processors" );
		$params->addParam( "tomo3d_options", $tomo3d_options, "Additional Tomo3D Options" );
		$params->addParam( "tomo3d_sirt_iters", $tomo3d_sirt_iters, "Number of SIRT Iterations" );
		$params->addParam( "frame_aligned", $frame_aligned, "Use Frame Aligned Images" );
		//$params->addParam( "exclude_images", $exclude_images, "Exclude Specific Images" );
		$params->addParam( "exclude_images_by_angle", $exclude_images_by_angle, "Exclude Images by Tilt Angles" );
		$params->addParam( "negative_recon", $negative_recon, "<strong>–</strong> Angle Limit" );
		$params->addParam( "positive_recon", $positive_recon, "<strong>+</strong> Angle Limit" );
		$params->addParam( "recon_iter", $recon_iter, "Refinement Iteration used to generate Reconstruction" );
		$params->addParam( "reconstruction_actions", $reconstruction_actions, "Reconstruction Actions" );
		$params->addParam( "reconstruction_method", $reconstruction_method, "Reconstruction Method" );
		if ($_POST['reconstruction_method'] == 4){
			$params->addParam( "recon_map_sampling", $recon_map_sampling, "Stack Sampling" );
		} else {
			$params->addParam( "recon_map_sampling", $recon_map_sampling, "Reconstruction Sampling" );
		}
		$params->addParam( "bin_type", $bin_type, "Sampling Method" );
		$params->addParam( "recon_map_size_x", $recon_map_size_x, "Reconstruction Size (x)" );
		$params->addParam( "recon_map_size_y", $recon_map_size_y, "Reconstruction Size (y)" );
		$params->addParam( "recon_thickness", $recon_thickness, "Reconstruction Thickness" );
		$params->addParam( "recon_lowpass", $recon_lowpass, "Lowpass Filter" );
		$params->addParam( "recon_lp_diam_x", $recon_lp_diam_x, "(x)" );
		$params->addParam( "recon_lp_diam_y", $recon_lp_diam_y, "(y)" );
		$params->addParam( "link_recon", $link_recon, "Link Final Reconstruction to this Directory" );
		$params->addParam( "amp_correct", $amp_correct, "Amplitude Correct" );
		$params->addParam( "amp_correct_w1", $amp_correct_w1, "w1" );
		$params->addParam( "amp_correct_w2", $amp_correct_w2, "w2" );
		$params->addParam( "defocus_difference", $defocus_difference, "Defocus Difference for Strips" );
		$params->addParam( "defocus_save_recon", $defocus_save_recon, "Save (and use) Defocus" );
		$params->addParam( "pick_tomogram", $pick_tomogram, "Tomogram Picking Method" );
		$params->addParam( "dog_particle_diam", $dog_particle_diam, "Particle Diameter" );
		$params->addParam( "dog_diam_variance", $dog_diam_variance, "Percent Diameter Variance" );
		$params->addParam( "dog_max_picks", $dog_max_picks, "Maximum Number of Picks" );
		$params->addParam( "dog_junk_tolerance", $dog_junk_tolerance, "Junk Tolerance" );
		$params->addParam( "dog_lowpass_type", $dog_lowpass_type, "Type of Lowpass used for DoG" );
		
		// Validations
		$params->addValidation( "recon_iter", "req" );
		$params->addValidation( "recon_iter", "num" );
		if ($_POST['reconstruction_method'] == 1 or $_POST['reconstruction_method'] == 2 or $_POST['reconstruction_method'] == 3){
			$params->addValidation( "recon_thickness", "req" );
		}
		
	}
	
	// Generate a form for the parameters that are specific to this program (not Appion params)
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		global $html;
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
		
		if ($_POST['reconstruction_actions'] == 2 or $_POST['reconstruction_actions'] == 4){
			$html .= "
			<br />
			<H4>CTF Correction Parameters ".docpop('ctf_info', '(Info)')."</H4>
			<hr />";
			if (!isset($_POST['ctf_correct'])) {$_POST['ctf_correct']=3;}
			$ctf_options=array("TomoCTF", "IMOD ctfphaseflip", "None");
			$html.= '<br><select name="ctf_correct" onchange=submit() style="width:66px">';
			for ($i = 1; $i < count($ctf_options)+1; $i++) {
				$html.= '<option ';
				if ($i == $_POST['ctf_correct']) {
					$html.= 'selected ';
				}
				$html.= 'value="'.$i.'">'.$ctf_options[$i-1].'</option>';
			}
			$html.= '</select>'; $html.= docpop('ctf_correct', ' Correct for CTF').'<br>';
			if ($_POST['ctf_correct'] == 1) {
				$html.= $params->insertTextField( "amp_contrast_ctf", $fieldSize );
				$html.= $params->insertTextField( "defocus_difference", $fieldSize );
				$html.= '<select name="amp_correct" style="width:66px">';
				$html.= '<option value="on">On</option>';
				$html.= '<option selected value="off">Off</option>';
				$html.= '</select>'; $html.= docpop('amp_correct', ' Amplitude Correct').'│ ';
				$html.= $params->insertTextFieldInRow( "amp_correct_w1", $fieldSize ).'│ ';
				$html.= $params->insertTextField( "amp_correct_w2", $fieldSize );
				
			} elseif ($_POST['ctf_correct'] == 2) {
				$html.= '<select name="frame_aligned" style="width:66px">';
				$html.= '<option selected value="True">True</option>';
				$html.= '<option value="False">False</option>';
				$html.= '</select>'; $html.= docpop('protomo_frame_aligned', ' Use Frame Aligned Images').'<br>';
				$html.= $params->insertTextField( "amp_contrast_ctf", $fieldSize );
				$html.= $params->insertTextField( "iWidth", $fieldSize );
				$html.= $params->insertTextField( "DefocusTol", $fieldSize );
			}
		}
		
		if ($_POST['reconstruction_actions'] == 3 or $_POST['reconstruction_actions'] == 4){
			$html .= "
			<br>
			<H4>Dose Compensation Parameters ".docpop('dose_info', '(Info)')."</H4>
			<hr />";
				
			$html.= '<select name="dose_presets" style="width:66px">';
			$html.= '<option value="False">None</option>';
			$html.= '<option value="Light">Light</option>';
			$html.= '<option value="Moderate">Moderate</option>';
			$html.= '<option value="Heavy">Heavy</option>';
			$html.= '<option value="Custom">Custom</option>';
			$html.= '</select>'; $html.= docpop('dose_presets', ' Dose Compensation Type').'<br>';
			$html.= $params->insertTextFieldInRow( "dose_a", $fieldSize ).'│ ';
			$html.= $params->insertTextFieldInRow( "dose_b", $fieldSize ).'│ ';
			$html.= $params->insertTextField( "dose_c", $fieldSize );
		}
		
		if ($_POST['reconstruction_method'] == 4){
			$html .= "
			<br />
			<H4>Stack Parameters ".docpop('stack_info', '(Info)')."</H4>
			<hr />";
		} else {
			$html .= "
			<br />
			<H4>Reconstruction Parameters ".docpop('recon_info2', '(Info)')."</H4>
			<hr />";
		}
		
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
		if ($_POST['reconstruction_method'] == 4){
			$html.= '</select>'; $html.= docpop('protomo_recon_iter', ' Refinement Iteration used to generate Stack<br>');
		} else {
			$html.= '</select>'; $html.= docpop('protomo_recon_iter', ' Refinement Iteration used to generate Reconstruction<br>');
		}
		if ($_POST['reconstruction_method'] == 1){
			$html.= $params->insertTextField( "recon_map_sampling", $fieldSize );
			$html.= $params->insertTextField( "recon_map_size_x", $fieldSize );
			$html.= $params->insertTextField( "recon_map_size_y", $fieldSize );
			$html.= $params->insertTextField( "recon_thickness", $fieldSize );
		}
		if ($_POST['reconstruction_method'] == 2 or $_POST['reconstruction_method'] == 3){
			$html.= $params->insertTextFieldInRow( "recon_map_sampling", $fieldSize ).'│ ';
			$html.= '<select name="bin_type" style="width:100px">';
			$html.= '<option selected value="fourier">Fourier</option>';
			$html.= '<option value="sum">Sum</option>';
			$html.= '<option value="interpolation">Interpolation</option>';
			$html.= '</select>'; $html.= docpop('bin_type', ' Sampling Method').'<br>';
			$html.= $params->insertTextField( "recon_thickness", $fieldSize );
			$html.= $params->insertTextField( "tomo3d_procs", $fieldSize );
		}
		if ($_POST['reconstruction_method'] == 4){
			$html.= $params->insertTextFieldInRow( "recon_map_sampling", $fieldSize ).'│ ';
			$html.= '<select name="bin_type" style="width:100px">';
			$html.= '<option selected value="fourier">Fourier</option>';
			$html.= '<option value="sum">Sum</option>';
			$html.= '<option value="Interpolation">Interpolation</option>';
			$html.= '</select>'; $html.= docpop('bin_type', ' Sampling Method').'<br>';
			$html.= $params->insertTextField( "stack_procs", $fieldSize );
		}
		//$html.= $params->insertTextField( "exclude_images", $fieldSize );
		$html.= $params->insertTextField( "exclude_images_by_angle", $fieldSize );
		$html.= $params->insertTextFieldInRow( "negative_recon", $fieldSize ).'│ ';
		$html.= $params->insertTextField( "positive_recon", $fieldSize );
		$html.= $params->insertTextField( "defocus_save_recon", $fieldSize );
		if ($_POST['reconstruction_method'] == 1){
			$html.= '<select name="recon_lowpass" style="width:100px">';
			$html.= '<option value="True">True</option>';
			$html.= '<option selected value="False">False</option>';
			$html.= '</select>'; $html.= docpop('recon_lowpass', ' Lowpass Filter').'│ ';
			$html.= $params->insertTextFieldInRow( "recon_lp_diam_x", $fieldSize ).'│ ';
			$html.= $params->insertTextField( "recon_lp_diam_y", $fieldSize );
		}
		if ($_POST['reconstruction_method'] == 3){
			$html.= $params->insertTextField( "tomo3d_sirt_iters", $fieldSize );
		}
		if ($_POST['reconstruction_method'] == 2 or $_POST['reconstruction_method'] == 3){
			$html.= $params->insertTextField( "tomo3d_options", $fieldSize2 );
		}
		if ($_POST['reconstruction_method'] == 1 or $_POST['reconstruction_method'] == 2 or $_POST['reconstruction_method'] == 3){
			$html.= $params->insertTextField( "link_recon", $fieldSize2 );
		}
		
		$html .= "
			<br />
			<H4>Pick Tomogram ".docpop('tomo_picker_info', '(Info)')."</H4>
			<hr />";
			if (!isset($_POST['pick_tomogram'])) {$_POST['pick_tomogram']=2;}
			$pick_tomogram=array("3D DoG Picking", "None");
			$html.= '<br><select name="pick_tomogram" onchange=submit() style="width:120px">';
			for ($i = 1; $i < count($pick_tomogram)+1; $i++) {
				$html.= '<option ';
				if ($i == $_POST['pick_tomogram']) {
					$html.= 'selected ';
				}
				$html.= 'value="'.$i.'">'.$pick_tomogram[$i-1].'</option>';
			}
			$html.= '</select>'; $html.= docpop('pick_tomogram', ' Tomogram Picking Method').'<br>';
			if ($_POST['pick_tomogram'] == 1) {
				$html.= $params->insertTextFieldInRow( "dog_particle_diam", $fieldSize ).' +- ';
				$html.= $params->insertTextField( "dog_diam_variance", $fieldSize );
				$html.= $params->insertTextField( "dog_max_picks", $fieldSize );
				$html.= $params->insertTextField( "dog_junk_tolerance", $fieldSize );
				$html.= '<select name="dog_lowpass_type" style="width:66px">';
				$html.= '<option selected value="proc3d">proc3d</option>';
				$html.= '</select>'; $html.= docpop('dog_lowpass_type', ' Type of Lowpass used for DoG');
			}
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
	
	// Use form footer to re-direct user
	// to the next step of the Protomo workflow.
	public function generateFormFooter()
	{
		global $tiltseries;
		global $sessionname;
		global $runname;
		global $outdir;
		global $iters;
		global $imageinfo;

		$_SESSION['tiltseries'] = $tiltseries;
		$_SESSION['runname'] = $runname;
		$_SESSION['sessionname'] = $sessionname;
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
