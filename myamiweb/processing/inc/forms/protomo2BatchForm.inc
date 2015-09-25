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
require_once "inc/processing.inc";
require_once "inc/appionloop.inc";
require_once "inc/leginon.inc";

session_start();
$sessionname=$_SESSION['sessionname'];
$imageinfo=$_SESSION['imageinfo'];

class Protomo2BatchForm extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML, $sessionname='', $raw_path='', $dimx='', $dimy='', $procs='all',$coarse_param_file='',
	$refine_param_file='', $recon_param_file='', $cachedir='', $protomo_outdir='', $link_recons='', $tiltseriesranges='', $firststep='1',
	$laststep='3', $shift_limit='30' , $angle_limit='40', $r1_sampling='8', $r2_sampling='4', $r3_sampling='2', $r4_sampling='1', $r5_sampling='',
	$auto_r1_sampling='8', $auto_r2_sampling='6', $auto_r3_sampling='4', $auto_r4_sampling='2', $auto_r5_sampling='1', $auto_r6_sampling='4',
	$auto_r7_sampling='2', $auto_r8_sampling='1', $r1_iters='20', $r2_iters='15', $r3_iters='10', $r4_iters='5', $r5_iters='',
	$auto_r1_iters='20', $auto_r2_iters='20', $auto_r3_iters='20', $auto_r4_iters='20', $auto_r5_iters='20',$auto_r6_iters='20',
	$auto_r7_iters='20', $auto_r8_iters='20', $r1_lp_diam_x='15', $r2_lp_diam_x='15', $r3_lp_diam_x='15', $r4_lp_diam_x='15', $r5_lp_diam_x='',
	$r6_lp_diam_x='15', $r7_lp_diam_x='15', $r8_lp_diam_x='15', $r1_lp_diam_y='15', $r2_lp_diam_y='15', $r3_lp_diam_y='15', $r4_lp_diam_y='15',
	$r5_lp_diam_y='', $r6_lp_diam_y='15', $r7_lp_diam_y='15', $r8_lp_diam_y='15', $r1_region_x='', $r2_region_x='', $r3_region_x='',
	$r4_region_x='', $r5_region_x='', $r1_region_y='', $r2_region_y='', $r3_region_y='', $r4_region_y='', $r5_region_y='', $r1_lp_apod_x='',
	$r2_lp_apod_x='', $r3_lp_apod_x='', $r4_lp_apod_x='', $r5_lp_apod_x='', $r1_lp_apod_y='', $r2_lp_apod_y='', $r3_lp_apod_y='',
	$r4_lp_apod_y='', $r5_lp_apod_y='', $r1_hp_apod_x='75', $r2_hp_apod_x='100', $r3_hp_apod_x='150', $r4_hp_apod_x='200', $r5_hp_apod_x='',
	$r1_hp_apod_y='75', $r2_hp_apod_y='100', $r3_hp_apod_y='150', $r4_hp_apod_y='200', $r5_hp_apod_y='', $r1_peak_search_radius_x='300',
	$r2_peak_search_radius_x='300', $r3_peak_search_radius_x='300', $r4_peak_search_radius_x='300', $r5_peak_search_radius_x='',
	$r1_peak_search_radius_y='300', $r2_peak_search_radius_y='300', $r3_peak_search_radius_y='300', $r4_peak_search_radius_y='300',
	$r5_peak_search_radius_y='', $all_tilt_videos="False", $all_recon_videos="False", $r1_kernel_x='', $r2_kernel_x='', $r3_kernel_x='',
	$r4_kernel_x='', $r5_kernel_x='', $r1_kernel_y='', $r2_kernel_y='', $auto_convergence='0.015', $auto_convergence_iters='5',
	$r3_kernel_y='', $r4_kernel_y='', $r5_kernel_y='', $voltage='300', $cs='0', $amp_contrast='0.07', $iWidth='20', $DefocusTol='200',
	$map_sampling='8', $pixelsize='', $video_type='')
	{
		parent::__construct($expId, $extraHTML);
		//print "_POST:" . "<br>";
		//var_dump($_POST);
		//print "_GET:" . "<br>";
		//var_dump($_GET);
		//print "_SESSION:" . "<br>";
		//var_dump($_SESSION);
		
		global $imageinfo;
		$tiltseriesId = ($_POST['tiltseriesId']) ? $_POST['tiltseriesId'] : NULL;
		$particle = new particledata();
		$leginondata = new leginondata();
		$alltiltseries = $particle->getTiltSeries($_GET['expId']);
		$seriesselector_array = $particle->getTiltSeriesSelector($alltiltseries,$tiltseriesId);
		//$voltage=$_SESSION['high tension']/1000;   //Even though this is the right key, I can't call high tension???
		
		$iters=$_SESSION['recon_iter'];
		$coarse_param_file=$_SESSION['outdir'].'/'.$_SESSION['runname'].'/ready_for_batch/coarse_series'.sprintf('%04d',$_SESSION['tiltseries']).'.param';
		$refine_param_file=$_SESSION['outdir'].'/'.$_SESSION['runname'].'/ready_for_batch/refine_series'.sprintf('%04d',$_SESSION['tiltseries']).'.param';
		$recon_param_file=$_SESSION['outdir'].'/'.$_SESSION['runname'].'/ready_for_batch/recon_series'.sprintf('%04d',$_SESSION['tiltseries']).'.param';
		$link_recons=$_SESSION['outdir'].'/'.'batch_tiltseries_out/';
		$_POST['outdir']=$_SESSION['outdir'];
		$this->updateFormParams();
		$params = $this->getFormParams();
		$particle = new particledata();
		$alltiltseries = $particle->getTiltSeries($_GET['expId']);
		$num = count($alltiltseries);
		global $numtiltseries;
		$numtiltseries = $num;
		$tiltseriesranges="1-$numtiltseries";
		$_POST['pixelsize'] = $imageinfo['pixelsize']*pow(10,10);
		$sessionname=$_SESSION['sessionname'];
		$r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $imageinfo['dimx']*0.5;
		$r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $imageinfo['dimy']*0.5;
		$r1_kernel_x = $r2_kernel_x = $r3_kernel_x = $r4_kernel_x = intval($r1_region_x/$r1_sampling);
		$r1_kernel_y = $r2_kernel_y = $r3_kernel_y = $r4_kernel_y = intval($r1_region_y/$r1_sampling);
		$r1_mask_width_x = $r2_mask_width_x = $r3_mask_width_x = $r4_mask_width_x = intval($r1_region_x/$r1_sampling);
		$r1_mask_width_y = $r2_mask_width_y = $r3_mask_width_y = $r4_mask_width_y = intval($r1_region_y/$r1_sampling);
		$r1_mask_apod_x = $r2_mask_apod_x = $r3_mask_apod_x = $r4_mask_apod_x = intval($r1_region_x/$r1_sampling);
		$r1_mask_apod_y = $r2_mask_apod_y = $r3_mask_apod_y = $r4_mask_apod_y = intval($r1_region_y/$r1_sampling);
		$r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = round(pow(10,10)*$imageinfo['pixelsize']*8);
		$r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = round(pow(10,10)*$imageinfo['pixelsize']*8);
		$r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = round(($imageinfo['dimx']+$imageinfo['dimy'])/(2*8));
		$r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = round(($imageinfo['dimx']+$imageinfo['dimy'])/(2*8));
		$r1_lp_diam_x = $r2_lp_diam_x = $r3_lp_diam_x = $r4_lp_diam_x = round(pow(10,10)*$imageinfo['pixelsize']*8);
		$r1_lp_diam_y = $r2_lp_diam_y = $r3_lp_diam_y = $r4_lp_diam_y = round(pow(10,10)*$imageinfo['pixelsize']*8);
		
		global $html;
		
		//foreach(array_keys($imageinfo) as $paramName)
		//	echo $paramName . "<br>";
			//echo $imageinfo["$paramName"] . "<br>";
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('protomo','imodctf');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'batchrun' );
		$this->setTitle( 'Protomo Batch Refinement and Reconstruction Launcher' );
		$this->setHeading( 'Protomo Batch Refinement and Reconstruction' );
		$this->setExeFile( 'protomo2batch.py' );
		$this->setGuideURL( "http://www.electrontomography.org/?page_id=317" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "protomo" );
		
		$params->addParam( "tiltseries", $tiltseries, "Tilt-Series #" );
		$params->addParam( "raw_path", $raw_path, "Raw Image Path" );
		$params->addParam( "procs", $procs, "Number of Processors" );
		$params->addParam( "coarse_param_file", $coarse_param_file, "Coarse Alignment Param File" );
		$params->addParam( "refine_param_file", $refine_param_file, "Refinement Param File" );
		$params->addParam( "recon_param_file", $recon_param_file, "Reconstruction Param File" );
		$params->addParam( "link_recons", $link_recons, "Link Final Reconstructions to this Directory" );
		$params->addParam( "tiltseriesranges", $tiltseriesranges, "Tilt-Series to Process" );
		$params->addParam( "firststep", $firststep, "First Step" );
		$params->addParam( "laststep", $laststep, "Last Step" );
		$params->addParam( "shift_limit", $shift_limit, "Shift Limit" );
		$params->addParam( "angle_limit", $angle_limit, "Angle Limit" );
		$params->addParam( "r1_region_x", $r1_region_x, "R1" );
		$params->addParam( "r2_region_x", $r2_region_x, "R2" );
		$params->addParam( "r3_region_x", $r3_region_x, "R3" );
		$params->addParam( "r4_region_x", $r4_region_x, "R4" );
		$params->addParam( "r5_region_x", $r5_region_x, "R5 │ Window Size (x) (<strong>Critical Parameter</strong>)" );
		$params->addParam( "r1_region_y", $r1_region_y, "R1" );
		$params->addParam( "r2_region_y", $r2_region_y, "R2" );
		$params->addParam( "r3_region_y", $r3_region_y, "R3" );
		$params->addParam( "r4_region_y", $r4_region_y, "R4" );
		$params->addParam( "r5_region_y", $r5_region_y, "R5 │ Window Size (y) (<strong>Critical Parameter</strong>)" );
		$params->addParam( "r1_sampling", $r1_sampling, "R1" );
		$params->addParam( "r2_sampling", $r2_sampling, "R2" );
		$params->addParam( "r3_sampling", $r3_sampling, "R3" );
		$params->addParam( "r4_sampling", $r4_sampling, "R4" );
		$params->addParam( "r5_sampling", $r5_sampling, "R5 │ Sampling" );
		$params->addParam( "auto_r1_sampling", $auto_r1_sampling, "R1" );
		$params->addParam( "auto_r2_sampling", $auto_r2_sampling, "R2" );
		$params->addParam( "auto_r3_sampling", $auto_r3_sampling, "R3" );
		$params->addParam( "auto_r4_sampling", $auto_r4_sampling, "R4" );
		$params->addParam( "auto_r5_sampling", $auto_r5_sampling, "R5 │ Sampling" );
		$params->addParam( "auto_r6_sampling", $auto_r3_sampling, "R6" );
		$params->addParam( "auto_r7_sampling", $auto_r4_sampling, "R7" );
		$params->addParam( "auto_r8_sampling", $auto_r5_sampling, "R8 │ Sampling" );
		$params->addParam( "map_sampling", $map_sampling, "Sampling for Depiction" );
		$params->addParam( "thickness", $thickness, "Thickness, in angstroms (<strong>Critical Parameter</strong>)" );
		$params->addParam( "r1_kernel_x", $r1_kernel_x, "R1" );
		$params->addParam( "r2_kernel_x", $r2_kernel_x, "R2" );
		$params->addParam( "r3_kernel_x", $r3_kernel_x, "R3" );
		$params->addParam( "r4_kernel_x", $r4_kernel_x, "R4" );
		$params->addParam( "r5_kernel_x", $r5_kernel_x, "R5 │ Filter Window Size (x)" );
		$params->addParam( "r1_kernel_y", $r1_kernel_y, "R1" );
		$params->addParam( "r2_kernel_y", $r2_kernel_y, "R2" );
		$params->addParam( "r3_kernel_y", $r3_kernel_y, "R3" );
		$params->addParam( "r4_kernel_y", $r4_kernel_y, "R4" );
		$params->addParam( "r5_kernel_y", $r5_kernel_y, "R5 │ Filter Window Size (y)" );
		$params->addParam( "r1_mask_width_x", $r1_mask_width_x, "R1" );
		$params->addParam( "r2_mask_width_x", $r2_mask_width_x, "R2" );
		$params->addParam( "r3_mask_width_x", $r3_mask_width_x, "R3" );
		$params->addParam( "r4_mask_width_x", $r4_mask_width_x, "R4" );
		$params->addParam( "r5_mask_width_x", $r5_mask_width_x, "R5 │ Rectangular Mask Width (x)" );
		$params->addParam( "r1_mask_width_y", $r1_mask_width_y, "R1" );
		$params->addParam( "r2_mask_width_y", $r2_mask_width_y, "R2" );
		$params->addParam( "r3_mask_width_y", $r3_mask_width_y, "R3" );
		$params->addParam( "r4_mask_width_y", $r4_mask_width_y, "R4" );
		$params->addParam( "r5_mask_width_y", $r5_mask_width_y, "R5 │ Rectangular Mask Width (y)" );
		$params->addParam( "r1_lowpass_diameter_x", $r1_lp_diam_x, "R1" );
		$params->addParam( "r2_lowpass_diameter_x", $r2_lp_diam_x, "R2" );
		$params->addParam( "r3_lowpass_diameter_x", $r3_lp_diam_x, "R3" );
		$params->addParam( "r4_lowpass_diameter_x", $r4_lp_diam_x, "R4" );
		$params->addParam( "r5_lowpass_diameter_x", $r5_lp_diam_x, "R5 │ Lowpass Filter (x) (<strong>Critical Parameter</strong>)" );
		$params->addParam( "r6_lowpass_diameter_x", $r6_lp_diam_x, "R6" );
		$params->addParam( "r7_lowpass_diameter_x", $r7_lp_diam_x, "R7" );
		$params->addParam( "r8_lowpass_diameter_x", $r8_lp_diam_x, "R8 │ Lowpass Filter (x) (<strong>Critical Parameter</strong>)" );
		$params->addParam( "r1_lowpass_diameter_y", $r1_lp_diam_y, "R1" );
		$params->addParam( "r2_lowpass_diameter_y", $r2_lp_diam_y, "R2" );
		$params->addParam( "r3_lowpass_diameter_y", $r3_lp_diam_y, "R3" );
		$params->addParam( "r4_lowpass_diameter_y", $r4_lp_diam_y, "R4" );
		$params->addParam( "r5_lowpass_diameter_y", $r5_lp_diam_y, "R5 │ Lowpass Filter (y) (<strong>Critical Parameter</strong>)" );
		$params->addParam( "r6_lowpass_diameter_y", $r6_lp_diam_y, "R6" );
		$params->addParam( "r7_lowpass_diameter_y", $r7_lp_diam_y, "R7" );
		$params->addParam( "r8_lowpass_diameter_y", $r8_lp_diam_y, "R8 │ Lowpass Filter (y)" );
		$params->addParam( "r1_highpass_diameter_x", $r1_hp_diam_x, "R1" );
		$params->addParam( "r2_highpass_diameter_x", $r2_hp_diam_x, "R2" );
		$params->addParam( "r3_highpass_diameter_x", $r3_hp_diam_x, "R3" );
		$params->addParam( "r4_highpass_diameter_x", $r4_hp_diam_x, "R4" );
		$params->addParam( "r5_highpass_diameter_x", $r5_hp_diam_x, "R5 │ Highpass Filter (x)" );
		$params->addParam( "r1_highpass_diameter_y", $r1_hp_diam_y, "R1" );
		$params->addParam( "r2_highpass_diameter_y", $r2_hp_diam_y, "R2" );
		$params->addParam( "r3_highpass_diameter_y", $r3_hp_diam_y, "R3" );
		$params->addParam( "r4_highpass_diameter_y", $r4_hp_diam_y, "R4" );
		$params->addParam( "r5_highpass_diameter_y", $r5_hp_diam_y, "R5 │ Highpass Filter (y)" );
		$params->addParam( "r1_mask_apod_x", $r1_mask_apod_x, "R1" );
		$params->addParam( "r2_mask_apod_x", $r2_mask_apod_x, "R2" );
		$params->addParam( "r3_mask_apod_x", $r3_mask_apod_x, "R3" );
		$params->addParam( "r4_mask_apod_x", $r4_mask_apod_x, "R4" );
		$params->addParam( "r5_mask_apod_x", $r5_mask_apod_x, "R5 │ Apodization (x) for Masks" );
		$params->addParam( "r1_mask_apod_y", $r1_mask_apod_y, "R1" );
		$params->addParam( "r2_mask_apod_y", $r2_mask_apod_y, "R2" );
		$params->addParam( "r3_mask_apod_y", $r3_mask_apod_y, "R3" );
		$params->addParam( "r4_mask_apod_y", $r4_mask_apod_y, "R4" );
		$params->addParam( "r5_mask_apod_y", $r5_mask_apod_y, "R5 │ Apodization (y) for Masks" );
		$params->addParam( "r1_lowpass_apod_x", $r1_lp_apod_x, "R1" );
		$params->addParam( "r2_lowpass_apod_x", $r2_lp_apod_x, "R2" );
		$params->addParam( "r3_lowpass_apod_x", $r3_lp_apod_x, "R3" );
		$params->addParam( "r4_lowpass_apod_x", $r4_lp_apod_x, "R4" );
		$params->addParam( "r5_lowpass_apod_x", $r5_lp_apod_x, "R5 │ Lowpass Apodization Filter (x)" );
		$params->addParam( "r1_lowpass_apod_y", $r1_lp_apod_y, "R1" );
		$params->addParam( "r2_lowpass_apod_y", $r2_lp_apod_y, "R2" );
		$params->addParam( "r3_lowpass_apod_y", $r3_lp_apod_y, "R3" );
		$params->addParam( "r4_lowpass_apod_y", $r4_lp_apod_y, "R4" );
		$params->addParam( "r5_lowpass_apod_y", $r5_lp_apod_y, "R5 │ Lowpass Apodization Filter (y)" );
		$params->addParam( "r1_highpass_apod_x", $r1_hp_apod_x, "R1" );
		$params->addParam( "r2_highpass_apod_x", $r2_hp_apod_x, "R2" );
		$params->addParam( "r3_highpass_apod_x", $r3_hp_apod_x, "R3" );
		$params->addParam( "r4_highpass_apod_x", $r4_hp_apod_x, "R4" );
		$params->addParam( "r5_highpass_apod_x", $r5_hp_apod_x, "R5 │ Highpass Apodization Filter (x)" );
		$params->addParam( "r1_highpass_apod_y", $r1_hp_apod_y, "R1" );
		$params->addParam( "r2_highpass_apod_y", $r2_hp_apod_y, "R2" );
		$params->addParam( "r3_highpass_apod_y", $r3_hp_apod_y, "R3" );
		$params->addParam( "r4_highpass_apod_y", $r4_hp_apod_y, "R4" );
		$params->addParam( "r5_highpass_apod_y", $r5_hp_apod_y, "R5 │ Highpass Apodization Filter (y)" );
		$params->addParam( "r1_peak_search_radius_x", $r1_peak_search_radius_x, "R1" );
		$params->addParam( "r2_peak_search_radius_x", $r2_peak_search_radius_x, "R2" );
		$params->addParam( "r3_peak_search_radius_x", $r3_peak_search_radius_x, "R3" );
		$params->addParam( "r4_peak_search_radius_x", $r4_peak_search_radius_x, "R4" );
		$params->addParam( "r5_peak_search_radius_x", $r5_peak_search_radius_x, "R5 │ Peak Search Redius (x)" );
		$params->addParam( "r1_peak_search_radius_y", $r1_peak_search_radius_y, "R1" );
		$params->addParam( "r2_peak_search_radius_y", $r2_peak_search_radius_y, "R2" );
		$params->addParam( "r3_peak_search_radius_y", $r3_peak_search_radius_y, "R3" );
		$params->addParam( "r4_peak_search_radius_y", $r4_peak_search_radius_y, "R4" );
		$params->addParam( "r5_peak_search_radius_y", $r5_peak_search_radius_y, "R5 │ Peak Search Radius (y)" );
		$params->addParam( "r1_iters", $r1_iters, "R1" );
		$params->addParam( "r2_iters", $r2_iters, "R2" );
		$params->addParam( "r3_iters", $r3_iters, "R3" );
		$params->addParam( "r4_iters", $r4_iters, "R4" );
		$params->addParam( "r5_iters", $r5_iters, "R5 │ Alignment Iterations" );
		$params->addParam( "auto_r1_iters", $auto_r1_iters, "R1" );
		$params->addParam( "auto_r2_iters", $auto_r2_iters, "R2" );
		$params->addParam( "auto_r3_iters", $auto_r3_iters, "R3" );
		$params->addParam( "auto_r4_iters", $auto_r4_iters, "R4" );
		$params->addParam( "auto_r5_iters", $auto_r5_iters, "R5 │ Alignment Iterations" );
		$params->addParam( "auto_r6_iters", $auto_r6_iters, "R6" );
		$params->addParam( "auto_r7_iters", $auto_r7_iters, "R7" );
		$params->addParam( "auto_r8_iters", $auto_r8_iters, "R8 │ Additional Alignment Iterations" );
		$params->addParam( "auto_convergence", $auto_convergence, "Convergence Criteria" );
		$params->addParam( "auto_convergence_iters", $auto_convergence_iters, "Further Iterations After Convergence" );
		$params->addParam( "voltage", $voltage, "Microscope voltage" );
		$params->addParam( "cs", $cs, "Spherical aberration" );
		$params->addParam( "amp_contrast", $amp_contrast, "Amplitude Contrast" );
		$params->addParam( "iWidth", $iWidth, "Interpolation Width" );
		$params->addParam( "DefocusTol", $DefocusTol, "Defocus Tolerance" );
		$params->addParam( "all_tilt_videos", $all_tilt_videos, "Create Tilt-Series Videos" );
		$params->addParam( "all_recon_videos", $all_recon_videos, "Create Reconstruction Videos" );
		$params->addParam( "map_sampling", $map_sampling, "Sampling for Depiction" );
		$params->addParam( "video_type", $video_type, "Video Type" );
		
		
	}
		
	// Generate a form for the parameters that are specific to this program (not Appion params)
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		global $numtiltseries;
		global $sessionname;
		global $html;
		
		$fieldSize = 5;
		$fieldSize2 = 3;
		$fieldSize3 = 30;
		
		//Initialize steps
		if (!isset($_POST['firststep'])) {$_POST['firststep']=1;}
		if (!isset($_POST['laststep'])) {$_POST['laststep']=3;}
		//Check for impossible setting
		if ($_POST['firststep'] > $_POST['laststep']) {$_POST['laststep']=$_POST['firststep'];}
		if ($_POST['firststep'] == 5 or $_POST['firststep'] == 8 or $_POST['laststep'] == 5 or $_POST['laststep'] == 8) {$_POST['firststep']=1; $_POST['laststep']=3;}
		if (($_POST['firststep'] == 1 or $_POST['firststep'] == 2 or $_POST['firststep'] == 3 or $_POST['firststep'] == 4) and ($_POST['laststep'] == 6 or $_POST['laststep'] == 7 or $_POST['laststep'] == 9)) {$_POST['laststep']=4;}
		if ($_POST['firststep'] == 6){$_POST['laststep']=6;}
		if ($_POST['firststep'] == 7){$_POST['laststep']=7;}
		if ($_POST['firststep'] == 9){$_POST['laststep']=9;}
		
		$steps=array("File Preparation", "Coarse Alignment", "Refinement", "Reconstruction", "----------------", "Screening Mode", "CTF Correction", "----------------", "Fully Automated");
		$html .= "<br>
			<b><center>Number of tilt-series available to process for session $sessionname: <font size='5'>$numtiltseries</font></center></b>";
		
		$html.= '<br><select name="firststep" onchange=submit() style="width:130px">';
		for ($i = 1; $i < count($steps)+1; $i++) {
			$html.= '<option ';
			if ($i == $_POST['firststep']) {
				$html.= 'selected ';
			}
			$html.= 'value="'.$i.'">'.$steps[$i-1].'</option>';
		}
		$html.= '</select>'; $html.= docpop('protomo_firststep', ' First Step').'<font size="6"> &nbsp&nbsp&nbsp→ &nbsp&nbsp&nbsp</font>';
		
		$html.= '<select name="laststep" onchange=submit() style="width:130px">';
		for ($i = 1; $i < count($steps)+1; $i++) {
			$html.= '<option ';
			if ($i == $_POST['laststep']) {
				$html.= 'selected ';
			}
			$html.= 'value="'.$i.'">'.$steps[$i-1].'</option>';
		}
		$html.= '</select>'; $html.= docpop('protomo_laststep', ' Last Step').'<br>';
		
		$html .= "
		
		<br />
		<H4>Batch Parameters ".docpop('batch_info', '(Info)')."</H4>
		<hr />";
		
		$html.= $params->insertTextField( "procs", $fieldSize );
		$html.= $params->insertTextField( "tiltseriesranges", $fieldSize );
		
		$html .= "<br />";
		
		if ($_POST['firststep'] == 1)
		{
			$html .= "
		<H3>Preparation Parameters ".docpop('prep_info', '(Info)')."</H3>
		<hr />";
			$html.= $params->insertTextFieldInRow( "shift_limit", $fieldSize ).'│ ';
			$html.= $params->insertTextField( "angle_limit", $fieldSize );
		}
		if ($_POST['firststep'] <= 2 and $_POST['laststep'] >= 2)
		{
			$html .= "
		<br />
		<H3>Coarse Alignment Parameters ".docpop('coarse_info', '(Info)')."</H3>
		<hr />";
			$html.= $params->insertTextField( "coarse_param_file", $fieldSize3 );
		}
		
		if ($_POST['firststep'] <= 3 and $_POST['laststep'] >= 3)
		{
			$html .= "
		<br />
		<H3>Refinement Parameters ".docpop('refine_info', '(Info)')."</H3>
		<hr />";
			$html.= $params->insertTextField( "refine_param_file", $fieldSize3 );
			$html.= $params->insertTextFieldInRow( "r1_iters", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_iters", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_iters", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_iters", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_iters", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_sampling", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_sampling", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_sampling", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_sampling", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_sampling", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_kernel_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_kernel_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_kernel_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_kernel_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_kernel_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_kernel_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_kernel_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_kernel_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_kernel_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_kernel_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_region_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_region_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_region_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_region_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_region_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_region_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_region_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_region_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_region_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_region_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_mask_width_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_mask_width_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_mask_width_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_mask_width_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_mask_width_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_mask_width_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_mask_width_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_mask_width_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_mask_width_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_mask_width_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_lowpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_lowpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_lowpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_lowpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_lowpass_diameter_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_lowpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_lowpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_lowpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_lowpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_lowpass_diameter_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_highpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_highpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_highpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_highpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_highpass_diameter_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_highpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_highpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_highpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_highpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_highpass_diameter_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_mask_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_mask_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_mask_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_mask_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_mask_apod_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_mask_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_mask_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_mask_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_mask_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_mask_apod_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_lowpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_lowpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_lowpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_lowpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_lowpass_apod_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_lowpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_lowpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_lowpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_lowpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_lowpass_apod_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_highpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_highpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_highpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_highpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_highpass_apod_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_highpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_highpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_highpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_highpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_highpass_apod_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_peak_search_radius_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_peak_search_radius_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_peak_search_radius_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_peak_search_radius_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_peak_search_radius_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r1_peak_search_radius_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r2_peak_search_radius_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r3_peak_search_radius_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r4_peak_search_radius_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r5_peak_search_radius_y", $fieldSize2 );
			
		}
		
		if ($_POST['firststep'] <= 4 and $_POST['laststep'] == 4)
		{
			$html .= "
		<br />
		<H3>Reconstruction Parameters ".docpop('recon_info', '(Info)')."</H3>
		<hr />";
			$html.= $params->insertTextField( "recon_param_file", $fieldSize3 );
			$html.= $params->insertTextField( "link_recons", $fieldSize3 );
		}
		
		if ($_POST['firststep'] == 6 and $_POST['laststep'] == 6)
		{
			$html .= "
		<br />
		<H3>Screening Mode Parameters ".docpop('screening_info', '(Info)')."</H3>
		<hr />";
			$html.= $params->insertTextFieldInRow( "shift_limit", $fieldSize ).'│ ';
			$html.= $params->insertTextField( "angle_limit", $fieldSize );
			$html.= $params->insertTextField( "coarse_param_file", $fieldSize3 );
			
		}
		
		if ($_POST['firststep'] == 7 and $_POST['laststep'] == 7)
		{
			$html .= "
		<br />
		<H3>CTF Correction Parameters ".docpop('ctf_info', '(Info)')."</H3>
		<hr />";
			$html.= $params->insertTextField( "voltage", $fieldSize );
			$html.= $params->insertTextField( "cs", $fieldSize );
			$html.= $params->insertTextField( "amp_contrast", $fieldSize );
			$html.= $params->insertTextField( "iWidth", $fieldSize );
			$html.= $params->insertTextField( "DefocusTol", $fieldSize );
			
		}
		
		if ($_POST['firststep'] == 9 and $_POST['laststep'] == 9)
		{
			$html .= "
		<br />
		<H3>Fully Automated Parameters ".docpop('auto_info', '(Info)')."</H3>
		<hr />";
			$html.= $params->insertTextField( "coarse_param_file", $fieldSize3 );
			$html.= $params->insertTextField( "refine_param_file", $fieldSize3 );
			$html.= $params->insertTextField( "recon_param_file", $fieldSize3 );
			$html.= $params->insertTextFieldInRow( "auto_r1_iters", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "auto_r2_iters", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "auto_r3_iters", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "auto_r4_iters", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "auto_r5_iters", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "auto_r1_sampling", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "auto_r2_sampling", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "auto_r3_sampling", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "auto_r4_sampling", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "auto_r5_sampling", $fieldSize2 );
			$html.= $params->insertTextField( "auto_convergence", $fieldSize2 );
			$html.= $params->insertTextField( "auto_convergence_iters", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "auto_r6_iters", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "auto_r7_iters", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "auto_r8_iters", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "auto_r6_sampling", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "auto_r7_sampling", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "auto_r8_sampling", $fieldSize2 );
			$html.= $params->insertTextField( "voltage", $fieldSize );
			$html.= $params->insertTextField( "cs", $fieldSize );
			$html.= $params->insertTextField( "amp_contrast", $fieldSize );
			$html.= $params->insertTextField( "iWidth", $fieldSize );
			$html.= $params->insertTextField( "DefocusTol", $fieldSize );
			
		}
		
		//For some reason != and !== don't work???
		if ($_POST['firststep'] == 3 or $_POST['firststep'] == 4 or $_POST['firststep'] == 6 or $_POST['firststep'] == 9 or $_POST['laststep'] == 3 or $_POST['laststep'] == 4 or $_POST['laststep'] == 6 or $_POST['laststep'] == 9)
		{
			$html .= "
		<br />
		<H4>Depiction Parameters ".docpop('depictionparam_info', '(Info)')."</H4>
		<hr />";
			$html.= '<select name="create_tiltseriesvids" style="width:66px">';
			$html.= '<option value="true">true</option>';
			$html.= '<option selected value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_create_reconstruction', ' Create Tilt-Series Videos').'<br>';
			$html.= '<select name="create_reconstruction" style="width:66px">';
			$html.= '<option value="true">true</option>';
			$html.= '<option selected value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_create_reconstruction2', ' Create Reconstruction Videos').'<br>';
			$html.= '<select name="video_type" style="width:66px">';
			$html.= '<option value="gif">Gif</option>';
			$html.= '<option selected value="html5vid">HTML5</option>';
			$html.= '</select>'; $html.= docpop('protomo_video_type', ' Video Type').'<br>';
			$html.= $params->insertTextField( "map_sampling", $fieldSize );
		}
		
		// Only display link to next step in tomo processing if on completed Command page
		if (empty($_POST['procs']) AND empty($_POST['tiltseriesranges']))
		{
			$html .= "<hr /><br></br>
			<b><center>[Enter all Parameters and click 'Just Show Command' to proceed]</center></b>";
		}
		
		return $html;
	}	

	// Override the default build Command Function because the --session and coarse flags are not normal
	// for other Appion Loop methods and not included in the parent.
	public function buildCommand( $postArray )
	{
		$command   = parent::buildCommand( $postArray );
		
		global $sessionname;
		global $numtiltseries;
		
		//Determine what additonal commands need to be given
		if ($_POST['firststep'] == 1 or $_POST['firststep'] == 2 or $_POST['firststep'] == 3 or $_POST['firststep'] == 4 or $_POST['firststep'] == 6 or $_POST['firststep'] == 7) {$command.="--automation=False ";}
		if ($_POST['firststep'] == 1 and $_POST['laststep'] == 1) {$command.="--prep_files=True --coarse_align=False --refine=False --reconstruct=False ";}
		if ($_POST['firststep'] == 1 and $_POST['laststep'] == 2) {$command.="--prep_files=True --coarse_align=True --refine=False --reconstruct=False ";}
		if ($_POST['firststep'] == 1 and $_POST['laststep'] == 3) {$command.="--prep_files=True --coarse_align=True --refine=True --reconstruct=False ";}
		if ($_POST['firststep'] == 1 and $_POST['laststep'] == 4) {$command.="--prep_files=True --coarse_align=True --refine=True --reconstruct=True ";}
		if ($_POST['firststep'] == 2 and $_POST['laststep'] == 2) {$command.="--prep_files=False --coarse_align=True --refine=False --reconstruct=False ";}
		if ($_POST['firststep'] == 2 and $_POST['laststep'] == 3) {$command.="--prep_files=False --coarse_align=True --refine=True --reconstruct=False ";}
		if ($_POST['firststep'] == 2 and $_POST['laststep'] == 4) {$command.="--prep_files=False --coarse_align=True --refine=True --reconstruct=True ";}
		if ($_POST['firststep'] == 3 and $_POST['laststep'] == 3) {$command.="--prep_files=False --coarse_align=False --refine=True --reconstruct=False ";}
		if ($_POST['firststep'] == 3 and $_POST['laststep'] == 3) {$command.="--prep_files=False --coarse_align=False --refine=True --reconstruct=True ";}
		if ($_POST['firststep'] == 4 and $_POST['laststep'] == 4) {$command.="--prep_files=False --coarse_align=False --refine=False --reconstruct=True ";}
		if ($_POST['firststep'] == 7) {$command.="--prep_files=False --coarse_align=False --refine=False --reconstruct=False --ctf_correct=True ";}
		if ($_POST['firststep'] == 9) {$command.="--automation=True --auto_prep=True --auto_ctf_correct=True --auto_coarse_align=True --auto_refine=True --auto_recon=True --sampling=8 --auto_elevation=True --auto_scaling=True ";}
		
		
		$pixelsize=$_POST['pixelsize'];
		$dimx=$_SESSION['dimx'];
		$dimy=$_SESSION['dimy'];
		$command.="--sessionname=$sessionname ";
		$command.="--dimx=$dimx ";
		$command.="--dimy=$dimy ";
		$command.="--pixelsize=$pixelsize ";
		return $command." ";
	}	
	
	// Override the default ShowReference function because the user needs to be re-directed
	// to the next step of the Protomo workflow.
	public function showReference( $postArray )
	{
		$html = parent::showReference( $postArray );
		
		global $sessionname;
		global $imageinfo;
		global $numtiltseries;

		$_SESSION['runname'] = $_POST['runname'];
		$_SESSION['sessionname'] = $sessionname;
		$_SESSION['outdir'] = $_POST['outdir'];
		$_SESSION['imageinfo'] = $imageinfo;
		$_SESSION['iters'] = $_POST['iters'];
		$_SESSION['tiltseriesranges'] = $_POST['tiltseriesranges'];
		
		// Only display link to next step in tomo processing if on completed Command page
		if (isset($_POST['procs']) AND isset($_POST['refine_param_file']) AND isset($_POST['tiltseriesranges']))
		{
			//$trimmed_runname=preg_replace("/\d+$/","",$_POST['runname']);
			$folders='tiltseriesXXXX';
			$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2BatchSummary'><b><center>[Click here to View Batch Alignment and Reconstructon Results after protomo2batch.py has been run] <font size='5'>→</font></center></b></a>";
			$html .= "<br></br>
			<b><center>[Execution of this protomo2batch.py command will create folders '".$folders."'<br> in the protomo_alignments/runname directory, overwriting folders & files when necessary]</center></b>";
			$html .= "<br>
			<b><center>[It is recommended that you run protomo2batch.py either on a dedicated machine or using screen/tmux/nohup]</center></b>";
			$html .= "
			<b><center>[protomo2batch.py may require long CPU time limits depending on the number of tilt-series being processed]</center></b>";
		}
		
		return $html;
	}
}
?>
