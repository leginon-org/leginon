<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */
//ini_set('display_errors', '0');     # don't show any errors...
//error_reporting(E_ALL | E_STRICT);

require_once "basicLayoutForm.inc";
require_once "inc/processing.inc";
require_once "inc/appionloop.inc";

#Keep session alive for one week
ini_set('session.gc_maxlifetime', 604800);
session_set_cookie_params(604800);

session_start();
if (isset($_GET['manual'])){$_SESSION['manual'] = $_GET['manual'];}
if ($_SESSION['manual'] == 1 AND $_POST['submit'] != "Submit Manual Parameters")
{
	global $imageinfo;
	$imageinfo['dimx'] = $_POST['dimx'] = $_SESSION['dimx'];
	$imageinfo['dimy'] = $_POST['dimy'] = $_SESSION['dimy'];
	$imageinfo['pixelsize'] = $_POST['pixelsize'] = $_SESSION['pixelsize'];
	$imageinfo['tiltseries'] = $_POST['tiltseries'] = $_SESSION['tiltseries'];
}
	
class Protomo2CoarseAlignForm extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML, $region_x='512', $region_y='512', $sampling='8', $map_sampling='', $thickness='1000', $pixelsize='',
	$lp_diam_x='20', $lp_diam_y='20', $lp_apod_x='50', $lp_apod_y='50', $hp_diam_x='500', $hp_diam_y='500', $hp_apod_x='150', $hp_apod_y='150',
	$corr_mode='mcf', $iters='', $param='', $binning='true', $preprocessing='true', $select_images='', $exclude_images='', $border='100',
	$clip_low='3.5', $clip_high='3.5', $thr_low='', $thr_high='', $gradient='true', $iter_gradient='false', $filter='median', $kernel_x='', $kernel_y='',
	$grow='0', $window_area='0.95', $mask_apod_x='', $mask_apod_y='', $mask_width_x='', $mask_width_y='', $dimx='', $dimy='',$correlation_size_x='192',
	$correlation_size_y='192', $peak_search_radius_x='300', $peak_search_radius_y='300', $logging='true', $loglevel='2', $slab='true', $map_size_x='512',
	$map_size_y='512', $filename_prefix='', $image_file_type='', $cachedir='cache', $protomo_outdir='out', $grid_limit='2.0', $grid_step='0.1',
	$create_reconstruction='true', $show_window_size='true', $create_tilt_video='true', $keep_recons='false', $region_x='512', $video_type='',
	$shift_limit='30' , $angle_limit='40', $parallel='', $ctf_correct='', $amp_contrast='0.07', $iWidth='20', $DefocusTol='200',
	$dose_presets='', $dose_a='', $dose_b='', $dose_c='', $frame_aligned='')
	{
		parent::__construct($expId, $extraHTML);
		//print "_POST:" . "<br>";
		//var_dump($_POST);d
		//print "_GET:" . "<br>";
		//var_dump($_GET);
		//print "_SESSION:" . "<br>";
		//var_dump($_SESSION);
		
		global $imageinfo;
		
		global $html; //I can only get the selector form to pass variables properly by defining it globally in the constructor.
		if ($_SESSION['manual'] != 1){
			$html.= "
			<table border=0>
			<tr>
			<td Valign='TOP'>\n";
			$html.= "	<table border=0>
						<tr>
							<td Valign='TOP'>\n";
			$tiltseriesId = ($_POST['tiltseriesId']) ? $_POST['tiltseriesId'] : NULL;
			$tiltseriesId2 = ($_POST['tiltseriesId2']) ? $_POST['tiltseriesId2'] : NULL;
			$particle = new particledata();
			$leginondata = new leginondata();
			
			// Select tilt-series
			$alltiltseries = $particle->getTiltSeries($_GET['expId']);
			$seriesselector_array = $particle->getTiltSeriesSelector($alltiltseries,$tiltseriesId);
			$seriesselector_array2 = $particle->getTiltSeriesSelector($alltiltseries,$tiltseriesId2,'tiltseriesId2'); 
			$tiltSeriesSelector = $seriesselector_array[0];
			$html.=  "<input type='hidden' name='lasttiltseries' value='$tiltseriesId'>\n";
			if ($tiltseriesId) {
				$tiltseriesinfos = $particle ->getTiltSeriesInfo($tiltseriesId);
			} else {
				$tiltseriesinfos = array();
			}
			global $imageinfo;
			$imageinfo = $leginondata->getImageInfo($tiltseriesinfos[0]['imageid']);
			$tiltSeriesSelector2 = $seriesselector_array2[0];
			if ($tiltseriesId2) {
				$tiltseriesinfos2 = $particle ->getTiltSeriesInfo($tiltseriesId2);
			} else {
				$tiltseriesinfos2 = array();
			}
			$html.=  $seriesselector_array[0];
			$html.=  docpop('protomo_tiltseries', ' Tilt-Series');
			if (count($tiltseriesinfos) && $tiltseriesId) {
				$html.=  "
				<br/><br/><b>First Image in the Tilt-Series:</b><br/>"
					.$tiltseriesinfos[0]['filename'].".".pathinfo($imageinfo['filename'], PATHINFO_EXTENSION);
			} else {
				if ($tiltseriesId)
					$html.=  "<br/><b>Bad Tilt-Series! Do not use.</b><br/>";
			}
			
			// Hide secondary tilt-series until dual tilt is processable.
			// Dual tilt-series processing is not in Appion-Protomo (yet)
			if (false) {
				$html.=  "</td><td Valign='TOP'>\n";
				$html.=  $seriesselector_array2[0];
				$html.=  docpop('tiltseriestwo', 'Secondary Tilt-Series');
			}
			if (count($tiltseriesinfos2) && $tiltseriesId2) {
				if ($tiltseriesId2==$tiltseriesId){
					$html.=  "<br/><b>2nd tilt-series must be different.</b><br/>";
				} else {
					$html.=  "
						<br/><b>First Image in the Tilt-Series:</b><br/>"
						.$tiltseriesinfos2[0]['filename'].".".pathinfo($imageinfo['filename'], PATHINFO_EXTENSION);
				}
			} else {
				if ($tiltseriesId2)
					$html.=  "<br/><b>Bad Tilt-Series! Do not use.</b><br/>";
			}
		}
		elseif ($_SESSION['manual'] == 1 AND $_POST['submit'] == "Submit Manual Parameters")
		{
			global $imageinfo;
			$imageinfo['dimx'] = $_SESSION['dimx'] = $_POST['dimx'];
			$imageinfo['dimy'] = $_SESSION['dimy'] = $_POST['dimy'];
			$imageinfo['pixelsize'] = $_SESSION['pixelsize'] = $_POST['pixelsize']*pow(10,-10);
			$imageinfo['tiltseries'] = $_SESSION['tiltseries'] = $_POST['tiltseries'];
		}
		
		if (isset($tiltseriesinfos[0]['number']) or $_SESSION['manual'] == 1)
		{
			//Initialize Express/Basic/Advanced Settings
			if (!isset($_POST['settings'])) {$_POST['settings']=2;}
			
			$settings=array("Express", "Basic", "Advanced");
	
			$html.= '<br><br><select name="settings" onchange=submit() style="width:100px">';
			for ($i = 1; $i < count($settings)+1; $i++) {
				$html.= '<option ';
				if ($i == $_POST['settings']) {
					$html.= 'selected ';
				}
				$html.= 'value="'.$i.'">'.$settings[$i-1].'</option>';
			}
			$html.= '</select>'; $html.= docpop('protomo_refine_settings', ' Settings Verbosity<br>');
			
			$html .= "
			<br />
			<H4>Parameter Presets ".docpop('preset_info', '(Info)')."</H4>
			<hr />";
			
			//Initialize presets
			if (!isset($_POST['preset_size'])) {$_POST['preset_size']=1;}
			if (!isset($_POST['preset_search'])) {$_POST['preset_search']=1;}
			
			//Preset pulldown menus
			$size_presets=array("Generic", "10 nm", "25 nm", "50 nm", "100 nm", "250 nm", "500 nm", "1000 nm");
			$search_presets=array("Generic", "Tiny search (10%)", "Small search (25%)", "Medium search (50%)", "Large search (75%)", "Full search (90%)");
			$html.= '<select name="preset_size" onchange=submit() style="width:150px">';
			for ($i = 1; $i < count($size_presets)+1; $i++) {
				$html.= '<option ';
				if ($i == $_POST['preset_size']) {
					$html.= 'selected ';
				}
				$html.= 'value="'.$i.'">'.$size_presets[$i-1].'</option>';
			}
			$html.= '</select>'; $html.= docpop('protomo_coarse_presets_size', ' Object Size | ');
			
			$html.= '<select name="preset_search" onchange=submit() style="width:150px">';
			for ($i = 1; $i < count($search_presets)+1; $i++) {
				$html.= '<option ';
				if ($i == $_POST['preset_search']) {
					$html.= 'selected ';
				}
				$html.= 'value="'.$i.'">'.$search_presets[$i-1].'</option>';
			}
			$html.= '</select>'; $html.= docpop('protomo_coarse_presets_search', ' Search Area<br>');
		}
		
		if ($_SESSION['manual'] != 1) {
				$_SESSION['tiltseries'] = $tiltseriesinfos[0]['number'];
		}
		if ($imageinfo['dimx'] < 2049 or $imageinfo['dimy'] < 2049){
			$_POST['map_sampling'] = $map_sampling='4';
		}else{
			$_POST['map_sampling'] = $map_sampling='8';
		}
		$_POST['map_size_x'] = $map_size_x=intval($imageinfo['dimx']/$map_sampling);
		$_POST['map_size_y'] = $map_size_y=intval($imageinfo['dimy']/$map_sampling);
		
		if ($_POST['settings'] == 1 or $_POST['settings'] == 2)  //Express or Basic Settings
		{
			//General Parameters
			$_POST['logging'] = $logging = 'true';
			$_POST['loglevel'] = $loglevel='2';
			//Preprocessing Parameters
			$_POST['preprocessing'] = $preprocessing='true';
			$_POST['gradient'] = $gradient='true';
			$_POST['iter_gradient'] = $iter_gradient='false';
			$_POST['filter'] = $filter='median';
			$_POST['border'] = $border='100';
			$_POST['clip_low'] = $clip_low='3.5';
			$_POST['clip_high'] = $clip_high='3.5';
			$_POST['thr_low'] = $thr_low='';
			$_POST['thr_high'] = $thr_high='';
			$_POST['kernel_x'] = $kernel_x='5';
			$_POST['kernel_y'] = $kernel_y='5';
			$_POST['grow'] = $grow='0';
			//Window Parameters
			$_POST['window_area'] = $window_area='0.95';
			//Mask Parameters
			$_POST['mask_apod_x'] = $mask_apod_x='10';
			$_POST['mask_apod_y'] = $mask_apod_y='10';
			//Depiction Parameters
			$_POST['correlation_size_x'] = $correlation_size_x='192';
			$_POST['correlation_size_y'] = $correlation_size_y='192';
			$_POST['tilt_clip'] = $tilt_clip='true';
			$_POST['show_window_size'] = $show_window_size='true';
			$_POST['video_type'] = $video_type='html5vid';
			$_POST['keep_recons'] = $keep_recons='false';
		}
		
		////Preset Defaults////
		if ($_POST['process'] != "Just Show Command")
		{
			//Search Area Presets (placed before size presets because they depend on these)
			if ($_POST['preset_search'] == 1)  //Generic (50%)
			{
				$_POST['region_x'] = $region_x = intval($imageinfo['dimx']*0.5);
				$_POST['region_y'] = $region_y = intval($imageinfo['dimy']*0.5);
				$Nx=$region_x/$sampling;
				$Ny=$region_y/$sampling;
				$_POST['mask_width_x'] = $mask_width_x = $Nx-2.5*$mask_apod_x;
				$_POST['mask_width_y'] = $mask_width_y = $Ny-2.5*$mask_apod_y;
				$_POST['highpass_diameter_x'] = $hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($region_x, $region_y));
				$_POST['highpass_diameter_y'] = $hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($region_x, $region_y));
				$_POST['highpass_apod_x'] = $hp_apod_x=round($hp_diam_x/2);
				$_POST['highpass_apod_y'] = $hp_apod_y=round($hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 2)  //Tiny 10%
			{
				$_POST['region_x'] = $region_x = intval($imageinfo['dimx']*0.1);
				$_POST['region_y'] = $region_y = intval($imageinfo['dimy']*0.1);
				$Nx=$region_x/$sampling;
				$Ny=$region_y/$sampling;
				$_POST['mask_width_x'] = $mask_width_x = $Nx-2.5*$mask_apod_x;
				$_POST['mask_width_y'] = $mask_width_y = $Ny-2.5*$mask_apod_y;
				$_POST['highpass_diameter_x'] = $hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($region_x, $region_y));
				$_POST['highpass_diameter_y'] = $hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($region_x, $region_y));
				$_POST['highpass_apod_x'] = $hp_apod_x=round($hp_diam_x/2);
				$_POST['highpass_apod_y'] = $hp_apod_y=round($hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 3)  //Small 25%
			{
				$_POST['region_x'] = $region_x = intval($imageinfo['dimx']*0.25);
				$_POST['region_y'] = $region_y = intval($imageinfo['dimy']*0.25);
				$Nx=$region_x/$sampling;
				$Ny=$region_y/$sampling;
				$_POST['mask_width_x'] = $mask_width_x = $Nx-2.5*$mask_apod_x;
				$_POST['mask_width_y'] = $mask_width_y = $Ny-2.5*$mask_apod_y;
				$_POST['highpass_diameter_x'] = $hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($region_x, $region_y));
				$_POST['highpass_diameter_y'] = $hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($region_x, $region_y));
				$_POST['highpass_apod_x'] = $hp_apod_x=round($hp_diam_x/2);
				$_POST['highpass_apod_y'] = $hp_apod_y=round($hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 4)  //Medium 50%
			{
				$_POST['region_x'] = $region_x = intval($imageinfo['dimx']*0.5);
				$_POST['region_y'] = $region_y = intval($imageinfo['dimy']*0.5);
				$Nx=$region_x/$sampling;
				$Ny=$region_y/$sampling;
				$_POST['mask_width_x'] = $mask_width_x = $Nx-2.5*$mask_apod_x;
				$_POST['mask_width_y'] = $mask_width_y = $Ny-2.5*$mask_apod_y;
				$_POST['highpass_diameter_x'] = $hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($region_x, $region_y));
				$_POST['highpass_diameter_y'] = $hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($region_x, $region_y));
				$_POST['highpass_apod_x'] = $hp_apod_x=round($hp_diam_x/2);
				$_POST['highpass_apod_y'] = $hp_apod_y=round($hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 5)  //Large 75%
			{
				$_POST['region_x'] = $region_x = intval($imageinfo['dimx']*0.75);
				$_POST['region_y'] = $region_y = intval($imageinfo['dimy']*0.75);
				$Nx=$region_x/$sampling;
				$Ny=$region_y/$sampling;
				$_POST['mask_width_x'] = $mask_width_x = $Nx-2.5*$mask_apod_x;
				$_POST['mask_width_y'] = $mask_width_y = $Ny-2.5*$mask_apod_y;
				$_POST['highpass_diameter_x'] = $hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($region_x, $region_y));
				$_POST['highpass_diameter_y'] = $hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($region_x, $region_y));
				$_POST['highpass_apod_x'] = $hp_apod_x=round($hp_diam_x/2);
				$_POST['highpass_apod_y'] = $hp_apod_y=round($hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 6)  //Full 90%
			{
				$_POST['region_x'] = $region_x = intval($imageinfo['dimx']*0.9);
				$_POST['region_y'] = $region_y = intval($imageinfo['dimy']*0.9);
				$Nx=$region_x/$sampling;
				$Ny=$region_y/$sampling;
				$_POST['mask_width_x'] = $mask_width_x = $Nx-2.5*$mask_apod_x;
				$_POST['mask_width_y'] = $mask_width_y = $Ny-2.5*$mask_apod_y;
				$_POST['highpass_diameter_x'] = $hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($region_x, $region_y));
				$_POST['highpass_diameter_y'] = $hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($region_x, $region_y));
				$_POST['highpass_apod_x'] = $hp_apod_x=round($hp_diam_x/2);
				$_POST['highpass_apod_y'] = $hp_apod_y=round($hp_diam_y/2);
			}
			
			
			//Size Presets
			if ($_POST['preset_size'] == 1)  //Generic
			{
				$_POST['lowpass_diameter_x'] = $lp_diam_x = min(round(pow(10,10)*$imageinfo['pixelsize']*75), round(0.75*$hp_diam_x));
				$_POST['lowpass_diameter_y'] = $lp_diam_y = min(round(pow(10,10)*$imageinfo['pixelsize']*75), round(0.75*$hp_diam_x));
				$_POST['lowpass_apod_x'] = $lp_apod_x = 2.5*$lp_diam_x;
				$_POST['lowpass_apod_y'] = $lp_apod_y = 2.5*$lp_diam_y;
				$_POST['thickness'] = $thickness = 1500;
			}
			
			if ($_POST['preset_size'] == 2)  //Size 10 nm
			{
				$_POST['lowpass_diameter_x'] = $lp_diam_x = min(50, round(0.75*$hp_diam_x));
				$_POST['lowpass_diameter_y'] = $lp_diam_y = min(50, round(0.75*$hp_diam_x));
				$_POST['lowpass_apod_x'] = $lp_apod_x = 2.5*$lp_diam_x;
				$_POST['lowpass_apod_y'] = $lp_apod_y = 2.5*$lp_diam_y;
				$_POST['thickness'] = $thickness = 500;
			}
			
			if ($_POST['preset_size'] == 3)  //Size 25 nm
			{
				$_POST['lowpass_diameter_x'] = $lp_diam_x = min(125, round(0.75*$hp_diam_x));
				$_POST['lowpass_diameter_y'] = $lp_diam_y = min(125, round(0.75*$hp_diam_x));
				$_POST['lowpass_apod_x'] = $lp_apod_x = 2.5*$lp_diam_x;
				$_POST['lowpass_apod_y'] = $lp_apod_y = 2.5*$lp_diam_y;
				$_POST['thickness'] = $thickness = 1250;
			}
			
			if ($_POST['preset_size'] == 4)  //Size 50 nm
			{
				$_POST['lowpass_diameter_x'] = $lp_diam_x = min(250, round(0.75*$hp_diam_x));
				$_POST['lowpass_diameter_y'] = $lp_diam_y = min(250, round(0.75*$hp_diam_x));
				$_POST['lowpass_apod_x'] = $lp_apod_x = 2.5*$lp_diam_x;
				$_POST['lowpass_apod_y'] = $lp_apod_y = 2.5*$lp_diam_y;
				$_POST['thickness'] = $thickness = 2500;
			}
			
			if ($_POST['preset_size'] == 5)  //Size 100 nm
			{
				$_POST['lowpass_diameter_x'] = $lp_diam_x = min(500, round(0.75*$hp_diam_x));
				$_POST['lowpass_diameter_y'] = $lp_diam_y = min(500, round(0.75*$hp_diam_x));
				$_POST['lowpass_apod_x'] = $lp_apod_x = 2.5*$lp_diam_x;
				$_POST['lowpass_apod_y'] = $lp_apod_y = 2.5*$lp_diam_y;
				$_POST['thickness'] = $thickness = 5000;
			}
			
			if ($_POST['preset_size'] == 6)  //Size 250 nm
			{
				$_POST['lowpass_diameter_x'] = $lp_diam_x = min(1250, round(0.75*$hp_diam_x));
				$_POST['lowpass_diameter_y'] = $lp_diam_y = min(1250, round(0.75*$hp_diam_x));
				$_POST['lowpass_apod_x'] = $lp_apod_x = 2.5*$lp_diam_x;
				$_POST['lowpass_apod_y'] = $lp_apod_y = 2.5*$lp_diam_y;
				$_POST['thickness'] = $thickness = 12500;
			}
			
			if ($_POST['preset_size'] == 7)  //Size 500 nm
			{
				$_POST['lowpass_diameter_x'] = $lp_diam_x = min(2500, round(0.75*$hp_diam_x));
				$_POST['lowpass_diameter_y'] = $lp_diam_y = min(2500, round(0.75*$hp_diam_x));
				$_POST['lowpass_apod_x'] = $lp_apod_x = 2.5*$lp_diam_x;
				$_POST['lowpass_apod_y'] = $lp_apod_y = 2.5*$lp_diam_y;
				$_POST['thickness'] = $thickness = 25000;
			}
			
			if ($_POST['preset_size'] == 8)  //Size 1000 nm
			{
				$_POST['lowpass_diameter_x'] = $lp_diam_x = min(5000, round(0.75*$hp_diam_x));
				$_POST['lowpass_diameter_y'] = $lp_diam_y = min(5000, round(0.75*$hp_diam_x));
				$_POST['lowpass_apod_x'] = $lp_apod_x = 2.5*$lp_diam_x;
				$_POST['lowpass_apod_y'] = $lp_apod_y = 2.5*$lp_diam_y;
				$_POST['thickness'] = $thickness = 50000;
			}
		}
		
		//These parameters don't change with Presets
		
		$kernel_x = '5';
		$kernel_y = '5';
		$mask_apod_x='10';
		$mask_apod_y='10';
		$voltage=$_POST['voltage']=$imageinfo['high tension']/1000;
		if ($_SESSION['manual'] == 1){
			$_POST['dimx'] = $imageinfo['dimx'];
			$_POST['dimy'] = $imageinfo['dimy'];
			$_POST['tiltseries'] = $imageinfo['tiltseries'];
			$_POST['image_file_type'] = 'mrc';
		}else{
			$_SESSION['dimx'] = $imageinfo['dimx'];
			$_SESSION['dimy'] = $imageinfo['dimy'];
			$_SESSION['pixelsize'] = $imageinfo['pixelsize']*pow(10,10);
			$image_file_type = pathinfo($imageinfo['filename'], PATHINFO_EXTENSION);
			$_POST['image_file_type'] = $image_file_type;
		}
		$_SESSION['imageinfo'] = $imageinfo;
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('appion-protomo', 'protomo','imodctf', 'dose_comp');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'protomorun' );
		$this->setTitle( 'Protomo Coarse Alignment Launcher' );
		$this->setHeading( 'Protomo Coarse Alignment' );
		$this->setExeFile( 'protomo2aligner.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Align_Tilt-Series" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( True ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "protomo" );
		
		$params->addParam( "tiltseries", $tiltseries, "Tilt-Series #" );
		$params->addParam( "dose_presets", $dose_presets, "Dose Compensation Type" );
		$params->addParam( "dose_a", $dose_a, "a" );
		$params->addParam( "dose_b", $dose_b, "b" );
		$params->addParam( "dose_c", $dose_c, "c" );
		$params->addParam( "frame_aligned", $frame_aligned, "Use Frame Aligned Images" );
		$params->addParam( "ctf_correct", $ctf_correct, "Correct for CTF" );
		$params->addParam( "parallel", $parallel, "Parallelize Non-Protomo Processes" );
		$params->addParam( "region_x", $region_x, "Window Size (x) (<strong>Critical Parameter</strong>)" );
		$params->addParam( "region_y", $region_y, "Window Size (y) (<strong>Critical Parameter</strong>)" );
		$params->addParam( "sampling", $sampling, "Sampling" );
		$params->addParam( "map_sampling", $map_sampling, "Sampling for Depiction" );
		$params->addParam( "thickness", $thickness, "Thickness (<strong>Critical Parameter</strong>)" );
		$params->addParam( "lowpass_diameter_x", $lp_diam_x, "Lowpass Filter (x) (<strong>Critical Parameter</strong>)" );
		$params->addParam( "lowpass_diameter_y", $lp_diam_y, "Lowpass Filter (y) (<strong>Critical Parameter</strong>)" );
		$params->addParam( "lowpass_apod_x", $lp_apod_x, "Lowpass Apodization Filter (x)" );
		$params->addParam( "lowpass_apod_y", $lp_apod_y, "Lowpass Apodization Filter (y)" );
		$params->addParam( "highpass_diameter_x", $hp_diam_x, "Highpass Filter (x)" );
		$params->addParam( "highpass_diameter_y", $hp_diam_y, "Highpass Filter (y)" );
		$params->addParam( "highpass_apod_x", $hp_apod_x, "Highpass Apodization Filter (x)" );
		$params->addParam( "highpass_apod_y", $hp_apod_y, "Highpass Apodization Filter (y)" );
		$params->addParam( "corr_mode", $corr_mode, "Correlation Mode (xcf, mcf, pcf, dbl)" );
		$params->addParam( "iters", $iters, "Alignment Iterations" );
		$params->addParam( "param_file", $param, "External Param File" );
		$params->addParam( "binning", $binning, "Raw Image Binning" );
		$params->addParam( "preprocessing", $preprocessing, "Raw Image Preprocessing" );
		$params->addParam( "select_images", $select_images, "Select Specific Images" );
		$params->addParam( "exclude_images", $exclude_images, "Exclude Specific Images" );
		$params->addParam( "border", $border, "Border Width for Exclusion" );
		$params->addParam( "clip_low", $clip_low, "Lower Clip (in SDs)" );
		$params->addParam( "clip_high", $clip_high, "Upper Clip (in SDs)" );
		$params->addParam( "thr_low", $thr_low, "Lower Threshold (in density values)" );
		$params->addParam( "thr_high", $thr_high, "Upper Threshold (in density values)" );
		$params->addParam( "gradient", $gradient, "Linear Gradient Subtraction" );
		$params->addParam( "iter_gradient", $iter_gradient, "Iterate Gradient Subtraction Once" );
		$params->addParam( "filter", $filter, "Preprocessing median/gauss Filter" );
		$params->addParam( "kernel_x", $kernel_x, "Filter Window Size (x)" );
		$params->addParam( "kernel_y", $kernel_y, "Filter Window Size (y)" );
		$params->addParam( "grow", $grow, "Grow Binary Mask" );
		$params->addParam( "window_area", $window_area, "Window Area Fraction" );
		$params->addParam( "mask_apod_x", $mask_apod_x, "Apodization (x) for Masks" );
		$params->addParam( "mask_apod_y", $mask_apod_y, "Apodization (y) for Masks" );
		$params->addParam( "mask_width_x", $mask_width_x, "Rectangular Mask Width (x)" );
		$params->addParam( "mask_width_y", $mask_width_y, "Rectangular Mask Width (y)" );
		$params->addParam( "correlation_size_x", $correlation_size_x, "Size (x) of Cross-Correlation Video" );
		$params->addParam( "correlation_size_y", $correlation_size_y, "Size (y) of Cross-Correlation Video" );
		$params->addParam( "peak_search_radius_x", $peak_search_radius_x, "Peak Search Radius (x)" );
		$params->addParam( "peak_search_radius_y", $peak_search_radius_y, "Peak Search Radius (y)" );
		$params->addParam( "logging", $logging, "Logging" );
		$params->addParam( "loglevel", $loglevel, "Logging Level" );
		$params->addParam( "filename_prefix", $filename_prefix, "Filename Prefix" );
		$params->addParam( "image_file_type", $image_file_type, "Image Extension" );
		$params->addParam( "cachedir", $cachedir, "Cache Directory" );
		$params->addParam( "protomo_outdir", $protomo_outdir, "Output Directory" );
		$params->addParam( "gridsearch_limit", $grid_limit, "Grid Search +-Angle Limit" );
		$params->addParam( "gridsearch_step", $grid_step, "Grid Search Angle Step Size" );
		$params->addParam( "create_tilt_video", $create_tilt_video, "Create Tilt-Series Videos" );
		$params->addParam( "create_reconstruction", $create_reconstruction, "Create a Reconstruction Video" );
		$params->addParam( "show_window_size", $show_window_size, "Show Window Size in Reconstruction Video" );
		$params->addParam( "keep_recons", $keep_recons, "Keep Intermediate Reconstruction" );
		$params->addParam( "slab", $slab, "Slab-Like Object" );
		$params->addParam( "map_size_x", $map_size_x, "Reconstructon Size (x)" );
		$params->addParam( "map_size_y", $map_size_y, "Reconstructon Size (y)" );
		$params->addParam( "video_type", $video_type, "Video Type" );
		$params->addParam( "shift_limit", $shift_limit, "Shift Limit" );
		$params->addParam( "angle_limit", $angle_limit, "Angle Limit" );
		$params->addParam( "amp_contrast", $amp_contrast, "Amplitude Contrast" );
		$params->addParam( "iWidth", $iWidth, "Interpolation Width" );
		$params->addParam( "DefocusTol", $DefocusTol, "Defocus Tolerance" );
		
		
		// Validations
		if ($_POST['settings'] == 2 or $_POST['settings'] == 3)  //Basic or Advanced Settings
		{
			$params->addValidation( "region_x", "req" );
			$params->addValidation( "region_x", "num" );
			$params->addValidation( "region_y", "req" );
			$params->addValidation( "region_y", "num" );
			$params->addValidation( "thickness", "req" );
			$params->addValidation( "thickness", "num" );
		}
	}
		
	// Generate a form for the parameters that are specific to this program (not Appion params)
	public function generateAdditionalFormLeft()
	{
		if ($_SESSION['erase_coarse']==1)
		{
			$html .= "<br></br>
			<b><center>Remove the previous Coarse Alignment by running this command:</center></b>";
			$html .= "<br></br>
			<center><code>rm -r ".$_SESSION['outdir'].'/'.$_SESSION['runname']."</code></center>";
			$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2CoarseAlignForm'><b><center>Click here or Refresh this page to continue.</center></b></a>";	
			$_SESSION['erase_coarse'] = 0;
		}
		elseif (empty($_POST['tiltseriesId']) AND $_SESSION['erase_coarse']!=1 AND $_SESSION['manual'] != 1)
		{
			global $html;
			$html .= "<br></br>
			<b><center>[Choose a Tilt-Series to align to proceed]</center></b>
			<b><center>[For manual tilt-series setup <a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2CoarseAlignForm&manual=1'>Click here</a>]</center></b><br>";
		}
		elseif ($_GET['manual'] == 1 AND $_POST['submit'] != "Submit Manual Parameters")
		{
			$html .= "
			<br />
			<H4>Manual Setup Parameters ".docpop('manual_info', '(Info)')."</H4>
			<hr />";
			$html .= '<form method="post">';
			$html .= '<input type="text" name="dimx" size="4">'.docpop('protomo_dimx', ' Dim (x)').'| ';
			$html .= '<input type="text" name="dimy" size="4">'.docpop('protomo_dimy', ' Dim (y)').'<br>';
			$html .= '<input type="text" name="pixelsize" size="4">'.docpop('protomo_pixelsize', ' Pixelsize').'<br>';
			$html .= '<input type="text" name="tiltseries" size="4">'.docpop('protomo_tiltseries_manual', ' Tilt-Series Number').'<br>';
			$html .= '<br><center><input type="submit" name="submit" value="Submit Manual Parameters"><center> </form>';
		}
		else
		{
			$this->updateFormParams();
			$params = $this->getFormParams();
			
			global $html;
			
			$fieldSize = 5;
			if ($_POST['settings'] == 1 or $_POST['settings'] == 2)  //Express or Basic Settings
			{
				
				if ($_POST['settings'] == 1)  //Express Settings just hide all of the Basic Settings. Basic Settings are still required to be on the webpage somewhere.
					{$html.= '<div id="express" style="display:none">';}
				if ($_SESSION['manual'] != 1) {
					$html .= "
					<br />
					<H4>CTF Correction Parameters ".docpop('ctf_info', '(Info)')."</H4>
					<hr />";
					
					$html.= '<select name="ctf_correct" style="width:66px">';
					$html.= '<option value="True">True</option>';
					$html.= '<option selected value="False">False</option>';
					$html.= '</select>'; $html.= docpop('ctf_correct', ' Correct for CTF').'<br>';
				
					$html .= "
					<br>
					<H4>Dose Compensation Parameters ".docpop('dose_info', '(Info)')."</H4>
					<hr />";
					
					$html.= '<select name="dose_presets" style="width:66px">';
					$html.= '<option selected value="False">None</option>';
					$html.= '<option value="Light">Light</option>';
					$html.= '<option value="Moderate">Moderate</option>';
					$html.= '<option value="Heavy">Heavy</option>';
					$html.= '</select>'; $html.= docpop('dose_presets', ' Dose Compensation Type').'<br>';
				}
				
				$html .= "
				<br>
				<H4>General Parameters ".docpop('genparam_info', '(Info)')."</H4>
				<hr />";
				
				$html.= $params->insertTextField( "sampling", $fieldSize );
				if ($_SESSION['manual']!=1) {
						$html.= '<select name="frame_aligned" style="width:66px">';
						$html.= '<option selected value="True">True</option>';
						$html.= '<option value="False">False</option>';
						$html.= '</select>'; $html.= docpop('protomo_frame_aligned', ' Use Frame Aligned Images').'<br>';
				}
				$html.= $params->insertTextFieldInRow( "shift_limit", $fieldSize ).'│ ';
				$html.= $params->insertTextField( "angle_limit", $fieldSize );
				$html.= '<select name="parallel" style="width:66px">';
				$html.= '<option selected value="True">true</option>';
				$html.= '<option value="False">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_parallel', ' Parallelize Non-Protomo Processes').'<br>';
				
				$html .= "
			    <br />
			    <H4>Window Parameters ".docpop('windowparam_info', '(Info)')."</H4>
			    <hr />";
			    
				$html.= $params->insertTextField( "region_x", $fieldSize );
				$html.= $params->insertTextField( "region_y", $fieldSize );
				$html.= $params->insertTextField( "thickness", $fieldSize );
				
				$html .= "
			    <br />
			    <H4>Mask Parameters ".docpop('maskparam_info', '(Info)')."</H4>
			    <hr />";
			    
				$html.= $params->insertTextField( "lowpass_diameter_x", $fieldSize );
				$html.= $params->insertTextField( "lowpass_diameter_y", $fieldSize );
				$html.= $params->insertTextField( "highpass_diameter_x", $fieldSize );
				$html.= $params->insertTextField( "highpass_diameter_y", $fieldSize );
				$html.= $params->insertTextField( "mask_width_x", $fieldSize );
				$html.= $params->insertTextField( "mask_width_y", $fieldSize );
				$html.= $params->insertTextField( "lowpass_apod_x", $fieldSize );
				$html.= $params->insertTextField( "lowpass_apod_y", $fieldSize );
				$html.= $params->insertTextField( "highpass_apod_x", $fieldSize );
				$html.= $params->insertTextField( "highpass_apod_y", $fieldSize );
				
				$html .= "
				<br />
				<H4>Coarse Grid Search Parameters ".docpop('gridsearchparam_info', '(Info)')."</H4>
				<hr />";
				
				$html.= $params->insertTextField( "gridsearch_limit", $fieldSize );
				$html.= $params->insertTextField( "gridsearch_step", $fieldSize );
				
				$html .= "
				<br />
				<H4>Cross-Correlation Parameters ".docpop('crosscorrparam_info', '(Info)')."</H4>
				<hr />";
				
				$html.= '<select name="corr_mode" style="width:66px">';
				$html.= '<option value="xcf">xcf</option>';
				$html.= '<option selected value="mcf">mcf</option>';
				$html.= '<option value="pcf">pcf</option>';
				$html.= '<option value="dbl">dbl</option>';
				$html.= '</select>'; $html.= docpop('protomo_corr_mode', ' Correlation Mode (xcf, mcf, pcf, dbl)').'<br>';
				$html.= $params->insertTextField( "peak_search_radius_x", $fieldSize );
				$html.= $params->insertTextField( "peak_search_radius_y", $fieldSize );
				
				$html .= "
			    <br />
			    <H4>Back-Projection Map Parameters ".docpop('mapparam_info', '(Info)')."</H4>
			    <hr />";
				
				$html.= '<select name="slab" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_slab', ' Slab-like Objects').'<br>';
				
				$html .= "
				<br />
				<H4>Depiction Parameters ".docpop('depictionparam_info', '(Info)')."</H4>
				<hr />";
				
				$html.= '<select name="create_tilt_video" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_create_tilt_video', ' Create Tilt-Series Videos').'<br>';
				$html.= '<select name="create_reconstruction" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_create_reconstruction', ' Create a Reconstruction Video').'<br>';
				
				$html .= "<hr />";
				if ($_POST['settings'] == 1)  //Express Settings
					{$html.= "</div>";}
			}
			
			if ($_POST['settings'] == 3)  //Advanced Settings
			{
				if ($_SESSION['manual'] != 1) {
					$html .= "
					<br />
					<H4>CTF Correction Parameters ".docpop('ctf_info', '(Info)')."</H4>
					<hr />";
					
					$html.= '<select name="ctf_correct" style="width:66px">';
					$html.= '<option value="True">True</option>';
					$html.= '<option selected value="False">False</option>';
					$html.= '</select>'; $html.= docpop('ctf_correct', ' Correct for CTF').'<br>';
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
				}
				
				$html .= "
				<br>
				<H4>General Parameters ".docpop('genparam_info', '(Info)')."</H4>
				<hr />";
				
				$html.= $params->insertTextField( "sampling", $fieldSize );
				if ($_SESSION['manual']!=1) {
						$html.= '<select name="frame_aligned" style="width:66px">';
						$html.= '<option selected value="True">True</option>';
						$html.= '<option value="False">False</option>';
						$html.= '</select>'; $html.= docpop('protomo_frame_aligned', ' Use Frame Aligned Images').'<br>';
				}
				//$html.= $params->insertTextField( "select_images", $fieldSize );
				$html.= $params->insertTextField( "exclude_images", $fieldSize );
				$html.= $params->insertTextFieldInRow( "shift_limit", $fieldSize ).'│ ';
				$html.= $params->insertTextField( "angle_limit", $fieldSize );
				$html.= '<select name="parallel" style="width:66px">';
				$html.= '<option selected value="True">true</option>';
				$html.= '<option value="False">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_parallel', ' Parallelize Non-Protomo Processes').'<br>';
				$html.= '<select name="logging" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_logging', ' Logging').'<br>';
				$html.= $params->insertTextField( "loglevel", $fieldSize );
				
				$html .= "
				<br />
				<H4>Preprocessing Parameters ".docpop('preprocparam_info', '(Info)')."</H4>
				<hr />";
				
				$html.= '<select name="preprocessing" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_preprocessing', ' Raw Image Preprocessing').'<br>';
				$html.= '<select name="gradient" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_gradient', ' Linear Gradient Subtraction').'<br>';
				$html.= '<select name="iter_gradient" style="width:66px">';
				$html.= '<option value="true">true</option>';
				$html.= '<option selected value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_iter_gradient', ' Iterate Gradient Subtraction Once').'<br>';
				$html.= '<select name="filter" style="width:66px">';
				$html.= '<option selected value="median">median</option>';
				$html.= '<option value="gauss">gauss</option>';
				$html.= '</select>'; $html.= docpop('protomo_filter', ' Preprocessing median/gauss Filter').'<br>';
				$html.= $params->insertTextField( "border", $fieldSize );
				$html.= $params->insertTextField( "clip_low", $fieldSize );
				$html.= $params->insertTextField( "clip_high", $fieldSize );
				$html.= $params->insertTextField( "thr_low", $fieldSize );
				$html.= $params->insertTextField( "thr_high", $fieldSize );
				$html.= $params->insertTextField( "kernel_x", $fieldSize );
				$html.= $params->insertTextField( "kernel_y", $fieldSize );
				$html.= $params->insertTextField( "grow", $fieldSize );
				
				$html .= "
				<br />
				<H4>Window Parameters ".docpop('windowparam_info', '(Info)')."</H4>
				<hr />";
				
				$html.= $params->insertTextField( "region_x", $fieldSize );
				$html.= $params->insertTextField( "region_y", $fieldSize );
				$html.= $params->insertTextField( "thickness", $fieldSize );
				$html.= $params->insertTextField( "window_area", $fieldSize );
				
				$html .= "
				<br />
				<H4>Mask Parameters ".docpop('maskparam_info', '(Info)')."</H4>
				<hr />";
				
				$html.= $params->insertTextField( "lowpass_diameter_x", $fieldSize );
				$html.= $params->insertTextField( "lowpass_diameter_y", $fieldSize );
				$html.= $params->insertTextField( "highpass_diameter_x", $fieldSize );
				$html.= $params->insertTextField( "highpass_diameter_y", $fieldSize );
				$html.= $params->insertTextField( "mask_width_x", $fieldSize );
				$html.= $params->insertTextField( "mask_width_y", $fieldSize );
				$html.= $params->insertTextField( "mask_apod_x", $fieldSize );
				$html.= $params->insertTextField( "mask_apod_y", $fieldSize );
				$html.= $params->insertTextField( "lowpass_apod_x", $fieldSize );
				$html.= $params->insertTextField( "lowpass_apod_y", $fieldSize );
				$html.= $params->insertTextField( "highpass_apod_x", $fieldSize );
				$html.= $params->insertTextField( "highpass_apod_y", $fieldSize );
				
				$html .= "
				<br />
				<H4>Coarse Grid Search Parameters ".docpop('gridsearchparam_info', '(Info)')."</H4>
				<hr />";
				
				$html.= $params->insertTextField( "gridsearch_limit", $fieldSize );
				$html.= $params->insertTextField( "gridsearch_step", $fieldSize );
				
				$html .= "
				<br />
				<H4>Cross-Correlation Parameters ".docpop('crosscorrparam_info', '(Info)')."</H4>
				<hr />";
				
				$html.= '<select name="corr_mode" style="width:66px">';
				$html.= '<option value="xcf">xcf</option>';
				$html.= '<option selected value="mcf">mcf</option>';
				$html.= '<option value="pcf">pcf</option>';
				$html.= '<option value="dbl">dbl</option>';
				$html.= '</select>'; $html.= docpop('protomo_corr_mode', ' Correlation Mode (xcf, mcf, pcf, dbl)').'<br>';
				$html.= $params->insertTextField( "peak_search_radius_x", $fieldSize );
				$html.= $params->insertTextField( "peak_search_radius_y", $fieldSize );
				
				$html .= "
			    <br />
			    <H4>Back-Projection Map Parameters ".docpop('mapparam_info', '(Info)')."</H4>
			    <hr />";
				
				$html.= '<select name="slab" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_slab', ' Slab-like Objects').'<br>';
				
				$html .= "
				<br />
				<H4>Depiction Parameters ".docpop('depictionparam_info', '(Info)')."</H4>
				<hr />";
				
				$html.= $params->insertTextField( "correlation_size_x", $fieldSize );
				$html.= $params->insertTextField( "correlation_size_y", $fieldSize );
				$html.= '<select name="create_tilt_video" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_create_tilt_video', ' Create Tilt-Series Videos').'<br>';
				$html.= '<select name="create_reconstruction" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_create_reconstruction', ' Create a Reconstruction Video').'<br>';
				$html.= '<select name="show_window_size" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_show_window_size', ' Show Window Size in Reconstruction Videos').'<br>';
				$html.= '<select name="video_type" style="width:66px">';
				$html.= '<option value="gif">Gif</option>';
				$html.= '<option selected value="html5vid">HTML5</option>';
				$html.= '</select>'; $html.= docpop('protomo_video_type', ' Video Type').'<br>';
				$html.= $params->insertTextField( "map_sampling", $fieldSize );
				$html.= $params->insertTextField( "map_size_x", $fieldSize );
				$html.= $params->insertTextField( "map_size_y", $fieldSize );
				$html.= '<select name="keep_recons" style="width:66px">';
				$html.= '<option value="true">true</option>';
				$html.= '<option selected value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_keep_recons', ' Keep Intermediate Reconstruction').'<br>';
		
				$html .= "<hr />";
			}
			
			// Only display link to next step in tomo processing if on completed Command page
			if ((empty($_POST['tiltseries']) OR empty($_POST['region_x']) OR empty($_POST['region_y']) OR empty($_POST['thickness']) OR empty($_POST['grid_limit']) OR empty($_POST['grid_step'])) AND !isset($_POST['process']))
			{
				$html .= "<br></br>
				<b><center>[Choose appropriate presets and/or edit desired parameters then click 'Just Show Command' to proceed]</center><br></b>";
			}
		}
		return $html;
	}	

	// Override the default build Command Function because the --session and coarse flags are not normal
	// for other Appion Loop methods and not included in the parent.
	public function buildCommand( $postArray )
	{
		$command   = parent::buildCommand( $postArray );
		
		$sessionname=$_POST['sessionname'];
		$tiltseries=$_SESSION['tiltseries'];
		$pixelsize=$_SESSION['pixelsize'];
		if ($_SESSION['manual'] == 1) {$pixelsize=$pixelsize*pow(10,10);}
		$dimx=$_SESSION['dimx'];
		$dimy=$_SESSION['dimy'];
		$image_file_type=$_POST['image_file_type'];
		$ctf_correct=$_POST['ctf_correct'];
		if ($_SESSION['manual']!=1){$command.="--tiltseries=$tiltseries ";}
		if ($_SESSION['manual']==1){$command.="--my_tlt=True ";}
		$command.="--sessionname=$sessionname ";
		$command.="--pixelsize=$pixelsize ";
		$command.="--dimx=$dimx ";
		$command.="--dimy=$dimy ";
		$command.="--coarse=True ";
		
		return $command." ";
	}	
	
	// Override the default ShowReference function because the user needs to be re-directed
	// to the next step of the Protomo workflow.
	public function showReference( $postArray )
	{
		$html = parent::showReference( $postArray );
		
		global $imageinfo;
		
		$_SESSION['tiltseries'] = $_SESSION['tiltseries'];
		$_SESSION['runname'] = $_POST['runname'];
		$_SESSION['sessionname'] = $_POST['sessionname'];
		$_SESSION['outdir'] = $_POST['outdir'];
		$_SESSION['imageinfo'] = $imageinfo;

		// Only display link to next step in tomo processing if on completed Command page
		if (isset($_POST['region_x']) AND isset($_POST['region_y']) AND isset($_POST['thickness']) AND isset($_POST['gridsearch_limit']) AND isset($_POST['gridsearch_step']) AND isset($_POST['process']))
		{
			$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2CoarseAlignSummary'><b><center>[Click here to <font size='4'>View Coarse Alignment Results</font> after protomo2aligner.py --coarse has been run] <font size='5'>→</font></center></b></a>";	
		}
		
		return $html;
	}
}
?>
