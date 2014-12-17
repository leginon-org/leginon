<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicLayoutForm.inc";
require_once "inc/processing.inc";
require_once "inc/appionloop.inc";

session_start();
$tiltseries=$_SESSION['tiltseries'];
$sessionname=$_SESSION['sessionname'];
$imageinfo=$_SESSION['imageinfo'];
$_SESSION['erase_coarse'] = 0;

class Protomo2RefineForm extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML, $sessionname='', $tiltseries='', $r1_region_x='', $r2_region_x='', $r3_region_x='', $r4_region_x='', $r1_region_y='', $r2_region_y='', $r3_region_y='', $r4_region_y='', $r1_sampling='8', $r2_sampling='4', $r3_sampling='2', $r4_sampling='', $map_sampling='8', $thickness='1000', $pixelsize='', $r1_lp_diam_x='10', $r2_lp_diam_x='5', $r3_lp_diam_x='2', $r4_lp_diam_x='', $r1_lp_apod_x='25', $r2_lp_apod_x='15', $r3_lp_apod_x='10', $r4_lp_apod_x='',
	$r1_lp_diam_y='10', $r2_lp_diam_y='5', $r3_lp_diam_y='2', $r4_lp_diam_y='', $r1_lp_apod_y='25', $r2_lp_apod_y='15', $r3_lp_apod_y='10', $r4_lp_apod_y='', $r1_hp_diam_x='250', $r2_hp_diam_x='350', $r3_hp_diam_x='500', $r4_hp_diam_x='', $r1_hp_diam_y='250', $r2_hp_diam_y='350', $r3_hp_diam_y='500', $r4_hp_diam_y='', $r1_hp_apod_x='75', $r2_hp_apod_x='100', $r3_hp_apod_x='150', $r4_hp_apod_x='', $r1_hp_apod_y='75', $r2_hp_apod_y='100', $r3_hp_apod_y='150', $r4_hp_apod_y='', $corr_mode='mcf', $raw_path='', $r1_iters='10', $r2_iters='5', $r3_iters='2', $r4_iters='', $param='', $binning='true',
	$preprocessing='true', $select_images='', $exclude_images='', $border='100', $clip_low='3.5', $clip_high='3.5', $thr_low='', $thr_high='', $gradient='true', $gradient_switch='', $iter_gradient='', $iter_gradient_switch='', $filter='median',
	$r1_kernel_x='', $r2_kernel_x='', $r3_kernel_x='', $r4_kernel_x='', $r1_kernel_y='', $r2_kernel_y='', $r3_kernel_y='', $r4_kernel_y='', $grow='0', $window_area='0.95', $mask_apod_x='', $mask_apod_y='', $mask_width_x='', $mask_width_y='', $do_estimation='false', $norotations='false', $max_correction='',
	$correlation_size_x='160', $correlation_size_y='160', $r1_peak_search_radius_x='300', $r2_peak_search_radius_x='300', $r3_peak_search_radius_x='300', $r4_peak_search_radius_x='', $r1_peak_search_radius_y='300', $r2_peak_search_radius_y='300', $r3_peak_search_radius_y='300', $r4_peak_search_radius_y='', $orientation='true', $orientation_switch='', $azimuth='true', $azimuth_switch='', $elevation='false', $elevation_switch='',
	$rotation='true', $rotation_switch='', $scale='false', $scale_switch='', $logging='true', $loglevel='2', $map_size_x='512', $map_size_y='512', $map_size_z='200', $filename_prefix='', $image_file_type='', $cachedir='cache',
	$protomo_outdir='out', $retry='5', $retry_shrink='0.9', $gui_coarse_align='', $create_reconstruction='true', $keep_recons='false', $gif_optimize='true', $restart_cycle='' )
	{
		parent::__construct($expId, $extraHTML);
		//print "_POST:" . "<br>";
		//var_dump($_POST);
		//print "_GET:" . "<br>";
		//var_dump($_GET);
		//print "_SESSION:" . "<br>";
		//var_dump($_SESSION);
		
		global $imageinfo;
		$_POST['runname']=$_SESSION['runname'];
		$_POST['outdir']=$_SESSION['outdir'];
		$r1_region_x = $r2_region_x = $r3_region_x = $imageinfo['dimx']*0.75;
		$r1_region_y = $r2_region_y = $r3_region_y = $imageinfo['dimy']*0.75;
		$map_size_x = $imageinfo['dimx']/$map_sampling;
		$map_size_y = $imageinfo['dimy']/$map_sampling;
		$r1_kernel_x = $r2_kernel_x = $r3_kernel_x = intval($r1_region_x/$r1_sampling);
		$r1_kernel_y = $r2_kernel_y = $r3_kernel_y = intval($r1_region_y/$r1_sampling);
		$r1_mask_width_x = $r2_mask_width_x = $r3_mask_width_x = intval($r1_region_x/$r1_sampling);
		$r1_mask_width_y = $r2_mask_width_y = $r3_mask_width_y = intval($r1_region_y/$r1_sampling);
		$r1_mask_apod_x = $r2_mask_apod_x = $r3_mask_apod_x = intval($r1_region_x/$r1_sampling);
		$r1_mask_apod_y = $r2_mask_apod_y = $r3_mask_apod_y = intval($r1_region_y/$r1_sampling);
		$restart_cycle = $_SESSION['restart_cycle'];
		$image_file_type = pathinfo($imageinfo['filename'], PATHINFO_EXTENSION);
		$_SESSION['image_file_type'] = $image_file_type;
		$_POST['pixelsize'] = $imageinfo['pixelsize']*pow(10,10);
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('protomo');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'protomorun' );
		$this->setTitle( 'Protomo Refinement Launcher' );
		$this->setHeading( 'Protomo Refinement' );
		$this->setExeFile( 'protomo2aligner.py' );
		$this->setGuideURL( "http://www.electrontomography.org/?page_id=317" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "protomo" );
				
		$params->addParam( "tiltseries", $tiltseries, "Tilt Series #" );
		$params->addParam( "r1_region_x", $r1_region_x, "R1" );
		$params->addParam( "r2_region_x", $r2_region_x, "R2" );
		$params->addParam( "r3_region_x", $r3_region_x, "R3" );
		$params->addParam( "r4_region_x", $r4_region_x, "R4 │ Window Size (x) (<strong>Required Parameter</strong>)" );
		$params->addParam( "r1_region_y", $r1_region_y, "R1" );
		$params->addParam( "r2_region_y", $r2_region_y, "R2" );
		$params->addParam( "r3_region_y", $r3_region_y, "R3" );
		$params->addParam( "r4_region_y", $r4_region_y, "R4 │ Window Size (y) (<strong>Required Parameter</strong>)" );
		$params->addParam( "r1_sampling", $r1_sampling, "R1" );
		$params->addParam( "r2_sampling", $r2_sampling, "R2" );
		$params->addParam( "r3_sampling", $r3_sampling, "R3" );
		$params->addParam( "r4_sampling", $r4_sampling, "R4 │ Sampling" );
		$params->addParam( "map_sampling", $map_sampling, "Sampling for Depiction" );
		$params->addParam( "thickness", $thickness, "Thickness, in angstroms (<strong>Required Parameter</strong>)" );
		$params->addParam( "r1_mask_width_x", $r1_mask_width_x, "R1" );
		$params->addParam( "r2_mask_width_x", $r2_mask_width_x, "R2" );
		$params->addParam( "r3_mask_width_x", $r3_mask_width_x, "R3" );
		$params->addParam( "r4_mask_width_x", $r4_mask_width_x, "R4 │ Rectangular Mask Width (x)" );
		$params->addParam( "r1_mask_width_y", $r1_mask_width_y, "R1" );
		$params->addParam( "r2_mask_width_y", $r2_mask_width_y, "R2" );
		$params->addParam( "r3_mask_width_y", $r3_mask_width_y, "R3" );
		$params->addParam( "r4_mask_width_y", $r4_mask_width_y, "R4 │ Rectangular Mask Width (y)" );
		$params->addParam( "r1_lowpass_diameter_x", $r1_lp_diam_x, "R1" );
		$params->addParam( "r2_lowpass_diameter_x", $r2_lp_diam_x, "R2" );
		$params->addParam( "r3_lowpass_diameter_x", $r3_lp_diam_x, "R3" );
		$params->addParam( "r4_lowpass_diameter_x", $r4_lp_diam_x, "R4 │ Lowpass Filter (x)" );
		$params->addParam( "r1_lowpass_diameter_y", $r1_lp_diam_y, "R1" );
		$params->addParam( "r2_lowpass_diameter_y", $r2_lp_diam_y, "R2" );
		$params->addParam( "r3_lowpass_diameter_y", $r3_lp_diam_y, "R3" );
		$params->addParam( "r4_lowpass_diameter_y", $r4_lp_diam_y, "R4 │ Lowpass Filter (y)" );
		$params->addParam( "r1_highpass_diameter_x", $r1_hp_diam_x, "R1" );
		$params->addParam( "r2_highpass_diameter_x", $r2_hp_diam_x, "R2" );
		$params->addParam( "r3_highpass_diameter_x", $r3_hp_diam_x, "R3" );
		$params->addParam( "r4_highpass_diameter_x", $r4_hp_diam_x, "R4 │ Highpass Filter (x)" );
		$params->addParam( "r1_highpass_diameter_y", $r1_hp_diam_y, "R1" );
		$params->addParam( "r2_highpass_diameter_y", $r2_hp_diam_y, "R2" );
		$params->addParam( "r3_highpass_diameter_y", $r3_hp_diam_y, "R3" );
		$params->addParam( "r4_highpass_diameter_y", $r4_hp_diam_y, "R4 │ Highpass Filter (y)" );
		$params->addParam( "r1_mask_apod_x", $r1_mask_apod_x, "R1" );
		$params->addParam( "r2_mask_apod_x", $r2_mask_apod_x, "R2" );
		$params->addParam( "r3_mask_apod_x", $r3_mask_apod_x, "R3" );
		$params->addParam( "r4_mask_apod_x", $r4_mask_apod_x, "R4 │ Apodization (x) for Masks" );
		$params->addParam( "r1_mask_apod_y", $r1_mask_apod_y, "R1" );
		$params->addParam( "r2_mask_apod_y", $r2_mask_apod_y, "R2" );
		$params->addParam( "r3_mask_apod_y", $r3_mask_apod_y, "R3" );
		$params->addParam( "r4_mask_apod_y", $r4_mask_apod_y, "R4 │ Apodization (y) for Masks" );
		$params->addParam( "r1_lowpass_apod_x", $r1_lp_apod_x, "R1" );
		$params->addParam( "r2_lowpass_apod_x", $r2_lp_apod_x, "R2" );
		$params->addParam( "r3_lowpass_apod_x", $r3_lp_apod_x, "R3" );
		$params->addParam( "r4_lowpass_apod_x", $r4_lp_apod_x, "R4 │ Lowpass Apodization Filter (x)" );
		$params->addParam( "r1_lowpass_apod_y", $r1_lp_apod_y, "R1" );
		$params->addParam( "r2_lowpass_apod_y", $r2_lp_apod_y, "R2" );
		$params->addParam( "r3_lowpass_apod_y", $r3_lp_apod_y, "R3" );
		$params->addParam( "r4_lowpass_apod_y", $r4_lp_apod_y, "R4 │ Lowpass Apodization Filter (y)" );
		$params->addParam( "r1_highpass_apod_x", $r1_hp_apod_x, "R1" );
		$params->addParam( "r2_highpass_apod_x", $r2_hp_apod_x, "R2" );
		$params->addParam( "r3_highpass_apod_x", $r3_hp_apod_x, "R3" );
		$params->addParam( "r4_highpass_apod_x", $r4_hp_apod_x, "R4 │ Highpass Apodization Filter (x)" );
		$params->addParam( "r1_highpass_apod_y", $r1_hp_apod_y, "R1" );
		$params->addParam( "r2_highpass_apod_y", $r2_hp_apod_y, "R2" );
		$params->addParam( "r3_highpass_apod_y", $r3_hp_apod_y, "R3" );
		$params->addParam( "r4_highpass_apod_y", $r4_hp_apod_y, "R4 │ Highpass Apodization Filter (y)" );
		$params->addParam( "corr_mode", $corr_mode, "Correlation Mode (xcf, mcf, pcf, dbl)" );
		$params->addParam( "raw_path", $raw_path, "Raw Image Path" );
		$params->addParam( "r1_iters", $r1_iters, "R1" );
		$params->addParam( "r2_iters", $r2_iters, "R2" );
		$params->addParam( "r3_iters", $r3_iters, "R3" );
		$params->addParam( "r4_iters", $r4_iters, "R4 │ Alignment Iterations" );
		$params->addParam( "param_file", $param, "External Param File" );
		$params->addParam( "binning", $binning, "Raw Image Binning" );
		$params->addParam( "preprocessing", $preprocessing, "Raw Image Preprocessing" );
		$params->addParam( "select_images", $select_images, "Select Specific Images" );
		$params->addParam( "exclude_images", $exclude_images, "Exclude Specific Images" );
		$params->addParam( "border", $border, "Border Width for Exclusion" );
		$params->addParam( "clip_low", $clip_low, "Lower Clip (in SD)" );
		$params->addParam( "clip_high", $clip_high, "Upper Clip (in SD)" );
		$params->addParam( "thr_low", $thr_low, "Lower Threshold (in density values)" );
		$params->addParam( "thr_high", $thr_high, "Upper Threshold (in density values)" );
		$params->addParam( "gradient", $gradient, "Linear Gradient Subtraction" );
		$params->addParam( "gradient_switch", $gradient_switch, "Switch at Iteration" );
		$params->addParam( "iter_gradient", $iter_gradient, "Iterate Gradient Subtraction Once" );
		$params->addParam( "iter_gradient_switch", $iter_gradient_switch, "Switch at Iteration" );
		$params->addParam( "filter", $filter, "Preprocessing median/gauss Filter" );
		$params->addParam( "r1_kernel_x", $r1_kernel_x, "R1" );
		$params->addParam( "r2_kernel_x", $r2_kernel_x, "R2" );
		$params->addParam( "r3_kernel_x", $r3_kernel_x, "R3" );
		$params->addParam( "r4_kernel_x", $r4_kernel_x, "R4 │ Filter Window Size (x)" );
		$params->addParam( "r1_kernel_y", $r1_kernel_y, "R1" );
		$params->addParam( "r2_kernel_y", $r2_kernel_y, "R2" );
		$params->addParam( "r3_kernel_y", $r3_kernel_y, "R3" );
		$params->addParam( "r4_kernel_y", $r4_kernel_y, "R4 │ Filter Window Size (y)" );
		$params->addParam( "grow", $grow, "Grow Binary Mask" );
		$params->addParam( "window_area", $window_area, "Window Area Fraction" );
		$params->addParam( "do_estimation", $do_estimation, "Estimate Geometric Parameters" );
		$params->addParam( "norotations", "$norotations", "No In-plane Rotations" );
		$params->addParam( "max_correction", $max_correction, "Correction Cutoff" );
		$params->addParam( "correlation_size_x", $correlation_size_x, "Size (x) of Cross-Correlation Image" );
		$params->addParam( "correlation_size_y", $correlation_size_y, "Size (y) of Cross-Correlation Image" );
		$params->addParam( "r1_peak_search_radius_x", $r1_peak_search_radius_x, "R1" );
		$params->addParam( "r2_peak_search_radius_x", $r2_peak_search_radius_x, "R2" );
		$params->addParam( "r3_peak_search_radius_x", $r3_peak_search_radius_x, "R3" );
		$params->addParam( "r4_peak_search_radius_x", $r4_peak_search_radius_x, "R4 │ Peak Search Redius (x)" );
		$params->addParam( "r1_peak_search_radius_y", $r1_peak_search_radius_y, "R1" );
		$params->addParam( "r2_peak_search_radius_y", $r2_peak_search_radius_y, "R2" );
		$params->addParam( "r3_peak_search_radius_y", $r3_peak_search_radius_y, "R3" );
		$params->addParam( "r4_peak_search_radius_y", $r4_peak_search_radius_y, "R4 │ Peak Search Radius (y)" );
		$params->addParam( "orientation", $orientation, "Include Orientation Angles in Refinement" );
		$params->addParam( "orientation_switch", $orientation_switch, "Switch at Iteration" );
		$params->addParam( "azimuth", $azimuth, "Include Tilt Azimuth in Refinement" );
		$params->addParam( "azimuth_switch", $azimuth_switch, "Switch at Iteration" );
		$params->addParam( "elevation", $elevation, "Include Tilt Axis Elevation in Refinement" );
		$params->addParam( "elevation_switch", $elevation_switch, "Switch at Iteration" );
		$params->addParam( "rotation", $rotation, "Include In-plane Rotations in Refinement" );
		$params->addParam( "rotation_switch", $rotation_switch, "Switch at Iteration" );
		$params->addParam( "scale", $scale, "Include Scale Factors (Magnification) in Refinement" );
		$params->addParam( "scale_switch", $scale_switch, "Switch at Iteration" );
		$params->addParam( "logging", $logging, "Logging" );
		$params->addParam( "loglevel", $loglevel, "Logging Level" );
		$params->addParam( "filename_prefix", $filename_prefix, "Filename Prefix" );
		$params->addParam( "image_file_type", $image_file_type, "Image Extension" );
		$params->addParam( "cachedir", $cachedir, "Cache Directory" );
		$params->addParam( "protomo_outdir", $protomo_outdir, "Output Directory" );
		$params->addParam( "retry", $retry, "Number of Refinement Retries Allowed" );
		$params->addParam( "retry_shrink", $retry_shrink, "Window Size Fraction to Shrink Each Retry Attempt" );
		$params->addParam( "create_reconstruction", $create_reconstruction, "Create a Reconstruction Gif" );
		$params->addParam( "keep_recons", $keep_recons, "Keep Intermediate Reconstruction" );
		$params->addParam( "map_size_x", $map_size_x, "Reconstructon Size (x)" );
		$params->addParam( "map_size_y", $map_size_y, "Reconstructon Size (y)" );
		$params->addParam( "map_size_z", $map_size_z, "Reconstructon Size (z)" );
		$params->addParam( "gif_optimize", $gif_optimize, "Gif Optimization" );
		$params->addParam( "restart_cycle", $restart_cycle, "Restart Refinement at Iteration" );
		
		// Validations
		$params->addValidation( "r1_region_x", "req" );
		$params->addValidation( "r1_region_x", "num" );
		$params->addValidation( "r1_region_y", "req" );
		$params->addValidation( "r1_region_y", "num" );
		$params->addValidation( "thickness", "req" );
		$params->addValidation( "thickness", "num" );
		$params->addValidation( "r1_iters", "req" );
		$params->addValidation( "r1_iters", "num" );
	}
		
	// Generate a form for the parameters that are specific to this program (not Appion params)
	public function generateAdditionalFormLeft()
	{
		if ($_SESSION['erase_refine']==1)
		{
			$html .= "<br></br>
			<b><center>Either remove all previous Refinements by running this series of commands:</center></b>";
			$html .= "<br></br>
			<center><code>rm ".$_SESSION['outdir'].$_SESSION['runname']."/*.corr<br>
			rm ".$_SESSION['outdir'].$_SESSION['runname']."/gifs/correlations/series".sprintf('%04d',$_SESSION['tiltseries'])."[0-9][0-9]_cor.*<br>
			rm ".$_SESSION['outdir'].$_SESSION['runname']."/gifs/reconstructions/series".sprintf('%04d',$_SESSION['tiltseries'])."[0-9][0-9]_bck.*<br>
			rm ".$_SESSION['outdir'].$_SESSION['runname']."/gifs/corrplots/series".sprintf('%04d',$_SESSION['tiltseries'])."*<br>
			rm ".$_SESSION['outdir'].$_SESSION['runname']."/gifs/tiltseries/series".sprintf('%04d',$_SESSION['tiltseries'])."*<br></code></center>";
			//mv ".$_SESSION['outdir'].$_SESSION['runname']."/coarse_series".sprintf('%04d',$_SESSION['tiltseries']).".i3t ".$_SESSION['outdir'].$_SESSION['runname']."/series".sprintf('%04d',$_SESSION['tiltseries']).".i3t<br>
			//rm ".$_SESSION['outdir'].$_SESSION['runname']."/series".sprintf('%04d',$_SESSION['tiltseries'])."[0-9][0-9].*<br>
			//rm ".$_SESSION['outdir'].$_SESSION['runname']."/cache/"."series".sprintf('%04d',$_SESSION['tiltseries'])."*.<br>
			//rm ".$_SESSION['outdir'].$_SESSION['runname']."/out/series".sprintf('%04d',$_SESSION['tiltseries'])."[0-9][0-9]_cor.*<br>
			$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineForm'><b><center>and then Click here or Refresh this page to continue,</center></b></a>";
			$html .= "<br></br>
			<b><center>Or to continue from a refinement iteration, leave all files in place and <a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineForm'>Refresh</a> this page.<br>Then enter the iteration you would like to restart from into the 'Restart Refinement at Iteration' box.</center></b>";
			$_SESSION['erase_refine'] = 0;
			
		}
		else
		{
			$this->updateFormParams();
			$params = $this->getFormParams();
		
			$fieldSize = 5;
			$fieldSize2 = 3;
			
			$html .= "
		    <br />
		    <H4>General Parameters ".docpop('genparam_info2', '(Info)')."</H4>
		    <hr />";
			
			$html.= $params->insertTextFieldInRow( "r1_iters", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_iters", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_iters", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_iters", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_sampling", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_sampling", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_sampling", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_sampling", $fieldSize2 );
			$html.= $params->insertTextField( "raw_path", $fieldSize );
			//$html.= $params->insertTextField( "param_file", $fieldSize );
			//$html.= $params->insertTextField( "filename_prefix", $fieldSize );
			//$html.= $params->insertTextField( "image_file_type", $fieldSize );
			//$html.= $params->insertTextField( "cachedir", $fieldSize );
			//$html.= $params->insertTextField( "protomo_outdir", $fieldSize );
			//$html.= $params->insertTextField( "preprocessing", $fieldSize );
			$html.= '<select name="preprocessing" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_preprocessing', ' Raw Image Preprocessing').'<br>';
			//$html.= $params->insertTextField( "binning", $fieldSize );
			$html.= '<select name="binning" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_binning', ' Raw Image Binning').'<br>';
			$html.= $params->insertTextField( "select_images", $fieldSize );
			$html.= $params->insertTextField( "exclude_images", $fieldSize );
			//$html.= $params->insertTextField( "logging", $fieldSize );
			$html.= '<select name="logging" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_logging', ' Logging').'<br>';
			$html.= $params->insertTextField( "loglevel", $fieldSize );
			$html.= $params->insertTextField( "restart_cycle", $fieldSize );
			
			$html .= "
		    <br />
		    <H4>Preprocessing Parameters ".docpop('preprocparam_info', '(Info)')."</H4>
		    <hr />";
		    
			//$html.= $params->insertTextField( "gradient", $fieldSize );
			$html.= '<select name="gradient" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_gradient', ' Linear Gradient Subtraction').'│ ';
			$html.= $params->insertTextField( "gradient_switch", $fieldSize );
			//$html.= $params->insertTextField( "iter_gradient", $fieldSize );
			$html.= '<select name="iter_gradient" style="width:66px">';
			$html.= '<option value="true">true</option>';
			$html.= '<option selected value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_iter_gradient', ' Iterate Gradient Subtraction Once').'│ ';
			$html.= $params->insertTextField( "iter_gradient_switch", $fieldSize );
			//$html.= $params->insertTextField( "filter", $fieldSize );
			$html.= '<select name="filter" style="width:66px">';
			$html.= '<option selected value="median">median</option>';
			$html.= '<option value="gauss">gauss</option>';
			$html.= '</select>'; $html.= docpop('protomo_filter', ' Preprocessing median/gauss Filter').'<br>';
			$html.= $params->insertTextField( "border", $fieldSize );
			$html.= $params->insertTextField( "clip_low", $fieldSize );
			$html.= $params->insertTextField( "clip_high", $fieldSize );
			$html.= $params->insertTextField( "thr_low", $fieldSize );
			$html.= $params->insertTextField( "thr_high", $fieldSize );
			$html.= $params->insertTextFieldInRow( "r1_kernel_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_kernel_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_kernel_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_kernel_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_kernel_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_kernel_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_kernel_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_kernel_y", $fieldSize2 );
			$html.= $params->insertTextField( "grow", $fieldSize );
			
			$html .= "
		    <br />
		    <H4>Window Parameters ".docpop('windowparam_info', '(Info)')."</H4>
		    <hr />";
		    
			$html.= $params->insertTextFieldInRow( "r1_region_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_region_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_region_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_region_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_region_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_region_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_region_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_region_y", $fieldSize2 );
			$html.= $params->insertTextField( "thickness", $fieldSize );
			$html.= $params->insertTextField( "window_area", $fieldSize );
			
			$html .= "
		    <br />
		    <H4>Mask Parameters ".docpop('maskparam_info', '(Info)')."</H4>
		    <hr />";
		    
			$html.= $params->insertTextFieldInRow( "r1_mask_width_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_mask_width_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_mask_width_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_mask_width_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_mask_width_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_mask_width_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_mask_width_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_mask_width_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_lowpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_lowpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_lowpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_lowpass_diameter_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_lowpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_lowpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_lowpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_lowpass_diameter_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_highpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_highpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_highpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_highpass_diameter_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_highpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_highpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_highpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_highpass_diameter_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_mask_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_mask_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_mask_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_mask_apod_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_mask_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_mask_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_mask_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_mask_apod_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_lowpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_lowpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_lowpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_lowpass_apod_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_lowpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_lowpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_lowpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_lowpass_apod_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_highpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_highpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_highpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_highpass_apod_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_highpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_highpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_highpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_highpass_apod_y", $fieldSize2 );
			
			$html .= "
		    <br />
		    <H4>Cross-Correlation Parameters ".docpop('crosscorrparam_info', '(Info)')."</H4>
		    <hr />";
			
			//$html.= $params->insertTextField( "corr_mode", $fieldSize );
			$html.= '<select name="corr_mode" style="width:66px">';
			$html.= '<option value="xcf">xcf</option>';
			$html.= '<option selected value="mcf">mcf</option>';
			$html.= '<option value="pcf">pcf</option>';
			$html.= '<option value="dbl">dbl</option>';
			$html.= '</select>'; $html.= docpop('protomo_corr_mode', ' Correlation Mode (xcf, mcf, pcf, dbl)').'<br>';
			$html.= $params->insertTextFieldInRow( "r1_peak_search_radius_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_peak_search_radius_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_peak_search_radius_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_peak_search_radius_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_peak_search_radius_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_peak_search_radius_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_peak_search_radius_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r4_peak_search_radius_y", $fieldSize2 );
			
			$html .= "
		    <br />
		    <H4>Area Matching Parameters ".docpop('areamatchinparam_info', '(Info)')."</H4>
		    <hr />";
			
			//$html.= $params->insertTextField( "do_estimation", $fieldSize );
			$html.= '<select name="do_estimation" style="width:66px">';
			$html.= '<option value="true">true</option>';
			$html.= '<option selected value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_do_estimation', ' Estimate Geometric Parameters').'<br>';
			//$html.= $params->insertTextField( "norotations", $fieldSize );
			$html.= '<select name="norotations" style="width:66px">';
			$html.= '<option value="true">true</option>';
			$html.= '<option selected value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_norotations', ' No In-plane Rotations').'<br>';
			//$html.= $params->insertTextField( "max_correction", $fieldSize );
			$html.= $params->insertTextField( "retry", $fieldSize );
			$html.= $params->insertTextField( "retry_shrink", $fieldSize );
			
			$html .= "
		    <br />
		    <H4>Geometry Refinement Parameters ".docpop('geomrefineparam_info', '(Info)')."</H4>
		    <hr />";
			
			//$html.= $params->insertTextField( "orientation", $fieldSize );
			$html.= '<select name="orientation" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_orientation', ' Include Orientation Angles in Refinement').'│ ';
			$html.= $params->insertTextField( "orientation_switch", $fieldSize );
			//$html.= $params->insertTextField( "azimuth", $fieldSize );
			$html.= '<select name="azimuth" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_azimuth', ' Include Tilt Azimuth in Refinement').'│ ';
			$html.= $params->insertTextField( "azimuth_switch", $fieldSize );
			//$html.= $params->insertTextField( "elevation", $fieldSize );
			$html.= '<select name="elevation" style="width:66px">';
			$html.= '<option value="true">true</option>';
			$html.= '<option selected value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_elevation', ' Include Tilt Axis Elevation in Refinement').'│ ';
			$html.= $params->insertTextField( "elevation_switch", $fieldSize );
			//$html.= $params->insertTextField( "rotation", $fieldSize );
			$html.= '<select name="rotation" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_rotation', ' Include In-plane Rotations in Refinement').'│ ';
			$html.= $params->insertTextField( "rotation_switch", $fieldSize );
			//$html.= $params->insertTextField( "scale", $fieldSize );
			$html.= '<select name="scale" style="width:66px">';
			$html.= '<option value="true">true</option>';
			$html.= '<option selected value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_scale', ' Include Scale Factors (Magnification) in Refinement').'│ ';
			$html.= $params->insertTextField( "scale_switch", $fieldSize );
			
			$html .= "
		    <br />
		    <H4>Depiction Parameters ".docpop('depictionparam_info', '(Info)')."</H4>
		    <hr />";
			
			
			$html.= $params->insertTextField( "correlation_size_x", $fieldSize );
			$html.= $params->insertTextField( "correlation_size_y", $fieldSize );
			//$html.= $params->insertTextField( "create_reconstruction", $fieldSize );
			$html.= '<select name="create_reconstruction" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_create_reconstruction', ' Create Reconstruction Gifs').'<br>';
			//$html.= $params->insertTextField( "gif_optimize", $fieldSize );
			$html.= '<select name="gif_optimize" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_gif_optimize', ' Optimize Reconstruction Gifs').'<br>';
			$html.= $params->insertTextField( "map_sampling", $fieldSize );
			$html.= $params->insertTextField( "map_size_x", $fieldSize );
			$html.= $params->insertTextField( "map_size_y", $fieldSize );
			$html.= $params->insertTextField( "map_size_z", $fieldSize );
			//$html.= $params->insertTextField( "keep_recons", $fieldSize );
			$html.= '<select name="keep_recons" style="width:66px">';
			$html.= '<option value="true">true</option>';
			$html.= '<option selected value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_keep_recons', ' Keep Intermediate Reconstruction').'<br>';
			
			$html .= "<hr />";
		    
			// Only display link to next step in tomo processing if on completed Command page
			if (empty($_POST['r1_region_x']) OR empty($_POST['r1_region_y']) OR empty($_POST['thickness']) OR empty($_POST['r1_iters']) AND !isset($_POST['process']))
			{
				$html .= "<br></br>
				<b><center>[Enter the Required Parameters and click 'Just Show Command' to proceed]</center></b><br>";
			}
		}
		return $html;
	}		

	// Override the default build Command Function because the --session flag is not normal
	// for other Appion Loop methods and not included in the parent.
	public function buildCommand( $postArray )
	{
		$command   = parent::buildCommand( $postArray );
		
		global $tiltseries;
		global $sessionname;
		$t=time();
		
		$pixelsize=$_POST['pixelsize'];
		$image_file_type=$_SESSION['image_file_type'];
		$command.="--tiltseries=$tiltseries ";
		$command.="--sessionname=$sessionname ";
		$command.="--pixelsize=$pixelsize ";
		$command.="--image_file_type=$image_file_type ";
		$command.="--coarse=False ";
		
		//$command.="> ".$_SESSION['outdir'].$_SESSION['runname']."/".$_SESSION['runname']."_".date("Y-m-d.h:i:s",$t).".log";
		return $command." ";
	}
	
	// Override the default ShowReference function because the user needs to be re-directed
	// to the next step of the Protomo workflow.
	public function showReference( $postArray )
	{
		$html = parent::showReference( $postArray );
		
		global $tiltseries;
		global $sessionname;
		global $imageinfo;
		
		$_SESSION['tiltseries'] = $tiltseries;
		$_SESSION['runname'] = $_POST['runname'];
		$_SESSION['sessionname'] = $sessionname;
		$_SESSION['outdir'] = $_POST['outdir'];
		$_SESSION['iters'] = $_POST['r1_iters'] + $_POST['r2_iters'] + $_POST['r3_iters'] + $_POST['r4_iters'];
		$_SESSION['imageinfo'] = $imageinfo;
		$_SESSION['protomo_outdir'] = $_POST['protomo_outdir'];

		// Only display link to next step in tomo processing if on completed Command page
		if (isset($_POST['r1_region_x']) AND isset($_POST['r1_region_y']) AND isset($_POST['thickness']) AND isset($_SESSION['iters']) AND isset($_POST['process']))
		{
			$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineSummary'><b><center>[Click here to <font size='4'>View Refinement Results</font> after protomo2aligner.py has been run] <font size='5'>→</font></center></b></a>";
		}
		
		return $html;
	}
}
?>
