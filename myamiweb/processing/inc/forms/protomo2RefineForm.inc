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
require_once "inc/processing.inc";
require_once "inc/appionloop.inc";
require_once "inc/html_elements.inc";

ini_set('session.gc_maxlifetime', 604800);
session_set_cookie_params(604800);

session_start();
$tiltseries=$_SESSION['tiltseries'];
$sessionname=$_SESSION['sessionname'];
$imageinfo=$_SESSION['imageinfo'];
$_SESSION['erase_coarse'] = 0;
if ($_SESSION['manual'] == 1) {$_POST['image_file_type']='mrc';}

class Protomo2RefineForm extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML, $sessionname='', $tiltseries='', $dimx='', $dimy='', $r1_region_x='', $r2_region_x='', $r3_region_x='',
	$r4_region_x='', $r5_region_x='', $r1_region_y='', $r2_region_y='', $r3_region_y='', $r4_region_y='', $r5_region_y='', $r1_sampling='8',
	$r2_sampling='4', $r3_sampling='2', $r4_sampling='1', $r5_sampling='1', $map_sampling='8', $thickness='1000', $pixelsize='', $r1_lp_diam_x='15',
	$r2_lp_diam_x='15', $r3_lp_diam_x='15', $r4_lp_diam_x='15', $r5_lp_diam_x='', $r1_lp_apod_x='25', $r2_lp_apod_x='20', $r3_lp_apod_x='15',
	$r4_lp_apod_x='10', $r5_lp_apod_x='', $r1_lp_diam_y='15', $r2_lp_diam_y='15', $r3_lp_diam_y='15', $r4_lp_diam_y='15', $r5_lp_diam_y='',
	$r1_mask_apod_x='10', $r2_mask_apod_x='10', $r3_mask_apod_x='10', $r4_mask_apod_x='10', $r5_mask_apod_x='10',
	$r1_mask_apod_y='10', $r2_mask_apod_y='10', $r3_mask_apod_y='10', $r4_mask_apod_y='10', $r5_mask_apod_y='10',
	$r1_lp_apod_y='25', $r2_lp_apod_y='20', $r3_lp_apod_y='15', $r4_lp_apod_y='10', $r5_lp_apod_y='', $r1_hp_diam_x='250', $r2_hp_diam_x='350',
	$r3_hp_diam_x='450',$r4_hp_diam_x='550', $r5_hp_diam_x='', $r1_hp_diam_y='250', $r2_hp_diam_y='350', $r3_hp_diam_y='450', $r4_hp_diam_y='550',
	$r5_hp_diam_y='', $r1_hp_apod_x='75', $r2_hp_apod_x='100', $r3_hp_apod_x='150', $r4_hp_apod_x='200', $r5_hp_apod_x='', $r1_hp_apod_y='75',
	$r2_hp_apod_y='100', $r3_hp_apod_y='150', $r4_hp_apod_y='200', $r5_hp_apod_y='', $r1_iters='15', $r2_iters='10', $r3_iters='5',
	$r4_iters='5', $r5_iters='0', $param='', $binning='true', $preprocessing='true', $select_images='', $exclude_images_by_angle='', $exclude_images_by_angle_accuracy='0.05',
	$border='100', $clip_low='3.5', $clip_high='3.5', $thr_low='', $thr_high='', $gradient='true', $r1_corr_mode='mcf', $r2_corr_mode='mcf', $r3_corr_mode='mcf',
	$r4_corr_mode='mcf', $r5_corr_mode='', $gradient_switch='', $iter_gradient='', $iter_gradient_switch='', $filter='median', $r1_kernel_x='',
	$r2_kernel_x='', $r3_kernel_x='', $r4_kernel_x='', $r5_kernel_x='', $r1_kernel_y='', $r2_kernel_y='',$r3_kernel_y='', $r4_kernel_y='',
	$r5_kernel_y='', $grow='0', $window_area='0.95', $mask_width_x='', $mask_width_y='', $tilt_azimuth='', $do_estimation='false',
	$norotations='false', $max_correction='', $correlation_size_x='160', $correlation_size_y='160', $r1_peak_search_radius_x='300',
	$r2_peak_search_radius_x='300', $r3_peak_search_radius_x='300', $r4_peak_search_radius_x='300', $r5_peak_search_radius_x='300',
	$r1_peak_search_radius_y='300', $r2_peak_search_radius_y='300', $r3_peak_search_radius_y='300', $r4_peak_search_radius_y='300', $r5_peak_search_radius_y='300',
	$r1_cmdiameter_x='12.5', $r2_cmdiameter_x='25', $r3_cmdiameter_x='50', $r4_cmdiameter_x='100', $r5_cmdiameter_x='100',
	$r1_cmdiameter_y='12.5', $r2_cmdiameter_y='25', $r3_cmdiameter_y='50', $r4_cmdiameter_y='100', $r5_cmdiameter_y='100',
	$r1_cmdiameter='false', $r2_cmdiameter='false', $r3_cmdiameter='false', $r4_cmdiameter='false', $r5_cmdiameter='false',
	$translimit='1000', $orientation='true', $orientation_switch='', $azimuth='true', $azimuth_switch='', $elevation='false',
	$elevation_switch='', $rotation='true', $rotation_switch='', $scale='false', $scale_switch='', $logging='true', $loglevel='2', $slab='true',
	$map_size_x='512', $map_size_y='512', $filename_prefix='', $image_file_type='', $cachedir='cache', $protomo_outdir='out', $tilt_clip='',
	$create_reconstruction='true', $show_window_size='true', $create_tilt_video='true', $keep_recons='false', $video_type='', $restart_cycle='',
	$parallel='', $negative='', $positive='', $starting_tlt_file='', $defocus_save='', $restart_from_run='', $restart_from_iteration='',
	$azimuth_stability_check='False', $azimuth_max_deviation='3', $change_refimg='True', $desired_ref_tilt_angle=0)
	{
		parent::__construct($expId, $extraHTML);
		//print "_POST:" . "<br>";
		//var_dump($_POST);
		//print "_GET:" . "<br>";
		//var_dump($_GET);
		//print "_SESSION:" . "<br>";
		//var_dump($_SESSION);
		
		global $html; //I can only get the selector form to pass variables properly by defining it globally in the constructor.
		
		//Initialize Express/Basic/Advanced Settings
		if (!isset($_POST['settings'])) {$_POST['settings']=1;}
		if ($_GET['basic'] == 1) {$_POST['settings']=2;}
		if ($_GET['advanced'] == 1) {$_POST['settings']=3;}
		
		$settings=array("Express", "Basic", "Advanced");

		$html.= '<select name="settings" onchange=submit() style="width:100px">';
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
		
		//Determine maximum usable search area from alignment file
		$maxsearch_coarse1 = glob($_SESSION['outdir']."/".$_SESSION['runname']."/coarse_series".sprintf('%04d',$_SESSION['tiltseries']).".tlt.maxsearch.*");
		$maxsearch_coarse2 = glob($_SESSION['outdir']."/".$_SESSION['runname']."/coarse_series".sprintf('%04d',$_SESSION['tiltseries'])."_iter2.tlt.maxsearch.*");
		$maxsearch_imod_coarse = glob($_SESSION['outdir']."/".$_SESSION['runname']."/imod_coarse_series".sprintf('%04d',$_SESSION['tiltseries']).".tlt.maxsearch.*");
		$maxsearch_manual = glob($_SESSION['outdir']."/".$_SESSION['runname']."/manual_series".sprintf('%04d',$_SESSION['tiltseries']).".tlt.maxsearch.*");
		$maxsearch_initial = glob($_SESSION['outdir']."/".$_SESSION['runname']."/original.tlt.maxsearch.*");
		$maxsearch_my = glob($_SESSION['outdir']."/".$_SESSION['runname']."/series".sprintf('%04d',$_SESSION['tiltseries']).".tlt.maxsearch.*");
		$maxsearch_coarse1_file = array_reverse(explode('.',$maxsearch_coarse1[0]));
		$maxsearch_coarse1_x = intval($maxsearch_coarse1_file[1]); $maxsearch_coarse1_y = intval($maxsearch_coarse1_file[0]);
		$maxsearch_coarse2_file = array_reverse(explode('.',$maxsearch_coarse2[0]));
		if (count($maxsearch_coarse2) > 0) {$maxsearch_coarse2_x = intval($maxsearch_coarse2_file[1]); $maxsearch_coarse2_y = intval($maxsearch_coarse2_file[0]);}
		$maxsearch_imod_coarse_file = array_reverse(explode('.',$maxsearch_imod_coarse[0]));
		if (count($maxsearch_imod_coarse) > 0) {$maxsearch_imod_coarse_x = intval($maxsearch_imod_coarse_file[1]); $maxsearch_imod_coarse_y = intval($maxsearch_imod_coarse_file[0]);}
		$maxsearch_manual_file = array_reverse(explode('.',$maxsearch_manual[0]));
		if (count($maxsearch_manual) > 0) {$maxsearch_manual_x = intval($maxsearch_manual_file[1]); $maxsearch_manual_y = intval($maxsearch_manual_file[0]);}
		$maxsearch_initial_file = array_reverse(explode('.',$maxsearch_initial[0]));
		if (count($maxsearch_initial) > 0) {$maxsearch_initial_x = intval($maxsearch_initial_file[1]); $maxsearch_initial_y = intval($maxsearch_initial_file[0]);}
		$maxsearch_my_file = array_reverse(explode('.',$maxsearch_my[0]));
		if (count($maxsearch_my) > 0) {$maxsearch_my_x = intval($maxsearch_my_file[1]); $maxsearch_my_y = intval($maxsearch_my_file[0]);}
		
		//Initialize presets
		if (!isset($_POST['preset_size'])) {$_POST['preset_size']=1;}
		if (isset($_GET['preset_size']) && !empty($_GET['preset_size'])) {$_POST['preset_size']=$_GET['preset_size'];}
		if (!isset($_POST['preset_search'])) {$_POST['preset_search']=1;}
		if (isset($_GET['preset_search']) && !empty($_GET['preset_search'])) {$_POST['preset_search']=$_GET['preset_search'];}
		if (!isset($_POST['preset_type'])) {$_POST['preset_type']=1;}
		if (isset($_GET['preset_type']) && !empty($_GET['preset_type'])) {$_POST['preset_type']=$_GET['preset_type'];}
		if (count($maxsearch_coarse2) > 0 and (!isset($_POST['starting_tlt_file']))) {$_POST['starting_tlt_file']=2;} elseif (count($maxsearch_coarse2) == 0 and (!isset($_POST['starting_tlt_file']))) {$_POST['starting_tlt_file']=1;}
		if (isset($_GET['starting_tlt_file']) && !empty($_GET['starting_tlt_file'])) {$_POST['starting_tlt_file']=$_GET['starting_tlt_file'];}
		if ($_POST['preset_size'] == 6) {$_POST['preset_size']=1;} //The dotted line divider
		if ($_POST['preset_size'] == 11) {$_POST['preset_size']=1;} //The dotted line divider
		if ($_POST['preset_search'] == 9) {$_POST['preset_search']=1;} //The dotted line divider
		if ((count($maxsearch_coarse2) == 0) and $_POST['starting_tlt_file'] == 2) {$_POST['starting_tlt_file']=1; echo "<b>Error:</b> 'Coarse Iter 2' alignment does not exist.<br><br>";}
		if ((count($maxsearch_imod_coarse) == 0) and $_POST['starting_tlt_file'] == 3) {$_POST['starting_tlt_file']=1; echo "<b>Error:</b> 'Imod Coarse' alignment does not exist.<br><br>";}
		if ((count($maxsearch_manual) == 0) and $_POST['starting_tlt_file'] == 4) {$_POST['starting_tlt_file']=1; echo "<b>Error:</b> 'Manual' alignment does not exist.<br><br>";}
		if ((count($maxsearch_initial) == 0) and $_POST['starting_tlt_file'] == 5) {$_POST['starting_tlt_file']=1; echo "<b>Error:</b> 'Initial' alignment does not exist.<br><br>";}
		$my_tlt_file = glob($_SESSION['outdir']."/".$_SESSION['runname']."/series".sprintf('%04d',$_SESSION['tiltseries']).".*tlt");
		if ((count($my_tlt_file) == 0) and $_POST['starting_tlt_file'] == 6) {$_POST['starting_tlt_file']=1; echo "Error: 'My tlt file' <b>does not exist</b>. Place series".sprintf('%04d',$_SESSION['tiltseries']).".tlt in the run directory and remove the corresponding series".sprintf('%04d',$_SESSION['tiltseries']).".tlt.maxsearch file to use this option.<br><br>";}
		elseif ((count($my_tlt_file) > 0) and $_POST['starting_tlt_file'] == 6) {echo "series".sprintf('%04d',$_SESSION['tiltseries']).".tlt found in the run directory. If you placed this file here, then proceed normally to use it. If not, then overwrite this file with your own.<br><br>";}
		if ((count($maxsearch_my) == 0) and $_POST['starting_tlt_file'] == 6 and $_POST['preset_search'] < 9) {$_POST['preset_search'] = 13;}
		if ($_POST['starting_tlt_file'] == 1) {$maxsearch_x = $maxsearch_coarse1_x; $maxsearch_y = $maxsearch_coarse1_y;}
		if ($_POST['starting_tlt_file'] == 2) {$maxsearch_x = $maxsearch_coarse2_x; $maxsearch_y = $maxsearch_coarse2_y;}
		if ($_POST['starting_tlt_file'] == 3) {$maxsearch_x = $maxsearch_imod_coarse_x; $maxsearch_y = $maxsearch_imod_coarse_y;}
		if ($_POST['starting_tlt_file'] == 4) {$maxsearch_x = $maxsearch_manual_x; $maxsearch_y = $maxsearch_manual_y;}
		if ($_POST['starting_tlt_file'] == 5) {$maxsearch_x = $maxsearch_initial_x; $maxsearch_y = $maxsearch_initial_y;}
		if ($_POST['starting_tlt_file'] == 6) {$maxsearch_x = $maxsearch_my_x; $maxsearch_y = $maxsearch_my_y;}
		$maxsearch_avg = ($maxsearch_x + $maxsearch_y)/2;
		if ($maxsearch_avg < 100 and $_POST['starting_tlt_file'] != 6) {$_POST['starting_tlt_file']=1; echo "<b>Error:</b> There is not enough search area in common between all tilt images for the given 'Starting Alignment'.<br>If you would like to use this 'Starting Alignment', then manually align or remove the offending tilt images before performing Coarse Alignment.<br><br>";}
		
		//Preset pulldown menus
		$size_presets=array("Generic", "10 nm objects(s) - Steep lowpass", "25 nm objects(s) - Steep lowpass", "50 nm objects(s) - Steep lowpass", "100 nm objects(s) - Steep lowpass", "------------------", "10 nm objects(s) - Decreasing lowpass", "25 nm objects(s) - Decreasing lowpass", "50 nm objects(s) - Decreasing lowpass", "100 nm objects(s) - Decreasing lowpass", "------------------", "10 nm objects(s) - Constant lowpass", "25 nm objects(s) - Constant lowpass", "50 nm objects(s) - Constant lowpass", "100 nm objects(s) - Constant lowpass");
		$search_presets=array("Generic", "10% of max search", "25% of max search", "40% of max search", "50% of max search", "60% of max search", "75% of max search", "90% of max search", "------------------", "Tiny search (10%)", "Small search (25%)", "Med-Sm search (40%)", "Medium search (50%)", "Med-Lg search (60%)", "Large search (75%)", "Full search (90%)");
		$type_presets=array("Generic", "Quick refinement", "Modest refinement", "Full refinement", "Exhaustive refinement");
		$starting_tlt_file=array("Coarse Iter 1", "Coarse Iter 2", "Imod Coarse", "Manual", "Initial", "My tlt file");
		
		$html .= openRoundBorder();
		$html.= '<center><select name="preset_size" onchange=submit() style="width:150px">';
		for ($i = 1; $i < count($size_presets)+1; $i++) {
			$html.= '<option ';
			if ($i == $_POST['preset_size']) {
				$html.= 'selected ';
			}
			$html.= 'value="'.$i.'">'.$size_presets[$i-1].'</option>';
		}
		$html.= '</select>'; $html.= docpop('protomo_refine_presets_size', ' Object Size | ');
		
		$html.= '<select name="preset_search" onchange=submit() style="width:150px">';
		for ($i = 1; $i < count($search_presets)+1; $i++) {
			$html.= '<option ';
			if ($i == $_POST['preset_search']) {
				$html.= 'selected ';
			}
			$html.= 'value="'.$i.'">'.$search_presets[$i-1].'</option>';
		}
		$html.= '</select>'; $html.= docpop('protomo_refine_presets_search', ' Search Area</center>');
		
		$html.= '<br><center><select name="starting_tlt_file" onchange=submit() style="width:150px">';
		for ($i = 1; $i < count($starting_tlt_file)+1; $i++) {
			$html.= '<option ';
			if ($i == $_POST['starting_tlt_file']) {
				$html.= 'selected ';
			}
			$html.= 'value="'.$i.'">'.$starting_tlt_file[$i-1].'</option>';
		}
		$html.= '</select>'; $html.= docpop('protomo_starting_tlt_file', ' Starting Alignment | ');
		
		$html.= '<select name="preset_type" onchange=submit() style="width:150px">';
		for ($i = 1; $i < count($type_presets)+1; $i++) {
			$html.= '<option ';
			if ($i == $_POST['preset_type']) {
				$html.= 'selected ';
			}
			$html.= 'value="'.$i.'">'.$type_presets[$i-1].'</option>';
		}
		$html.= '</select>'; $html.= docpop('protomo_refine_presets_type', ' Refinement Type</center>');
		$html .= closeRoundBorder();
		
		global $imageinfo;
		$_POST['runname']=$_SESSION['runname'];
		$_POST['outdir']=$_SESSION['outdir'];
		//if ($imageinfo['dimx'] < 2049 or $imageinfo['dimy'] < 2049){
		//	$_POST['map_sampling'] = $map_sampling='4';
		//}else{
		//	$_POST['map_sampling'] = $map_sampling='8';
		//}
		$_POST['map_sampling'] = $map_sampling='8';
		
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
			$_POST['r1_kernel_x'] = $r1_kernel_x='5';
			$_POST['r2_kernel_x'] = $r2_kernel_x='5';
			$_POST['r3_kernel_x'] = $r3_kernel_x='5';
			$_POST['r4_kernel_x'] = $r4_kernel_x='5';
			$_POST['r5_kernel_x'] = $r5_kernel_x='5';
			$_POST['r1_kernel_y'] = $r1_kernel_y='5';
			$_POST['r2_kernel_y'] = $r2_kernel_y='5';
			$_POST['r3_kernel_y'] = $r3_kernel_y='5';
			$_POST['r4_kernel_y'] = $r4_kernel_y='5';
			$_POST['r5_kernel_y'] = $r5_kernel_y='5';
			$_POST['grow'] = $grow='0';
			//Window Parameters
			$_POST['window_area'] = $window_area='0.95';
			//Mask Parameters
			$_POST['r1_mask_apod_x'] = $r1_mask_apod_x='10';
			$_POST['r2_mask_apod_x'] = $r2_mask_apod_x='10';
			$_POST['r3_mask_apod_x'] = $r3_mask_apod_x='10';
			$_POST['r4_mask_apod_x'] = $r4_mask_apod_x='10';
			$_POST['r5_mask_apod_x'] = $r5_mask_apod_x='10';
			$_POST['r1_mask_apod_y'] = $r1_mask_apod_y='10';
			$_POST['r2_mask_apod_y'] = $r2_mask_apod_y='10';
			$_POST['r3_mask_apod_y'] = $r3_mask_apod_y='10';
			$_POST['r4_mask_apod_y'] = $r4_mask_apod_y='10';
			$_POST['r5_mask_apod_y'] = $r5_mask_apod_y='10';
			//Area Matching Parameters
			$_POST['do_estimation'] = $do_estimation='false';
			$_POST['norotations'] = $norotations='false';
			$_POST['translimit'] = intval(0.1*($imageinfo['dimx']+$imageinfo['dimy'])/2);
			//Depiction Parameters
			$_POST['correlation_size_x'] = $correlation_size_x='160';
			$_POST['correlation_size_y'] = $correlation_size_y='160';
			$_POST['tilt_clip'] = $tilt_clip='true';
			$_POST['show_window_size'] = $show_window_size='true';
			$_POST['video_type'] = $video_type='html5vid';
			$_POST['map_size_x'] = $map_size_x=intval($imageinfo['dimx']/$map_sampling);
			$_POST['map_size_y'] = $map_size_x=intval($imageinfo['dimy']/$map_sampling);
			$_POST['keep_recons'] = $keep_recons='false';
		}
		
		////Preset Defaults////
		if ($_POST['process'] != "Just Show Command")
		{
			//Search Area Presets (placed before size presets because they depend on these)
			if ($_POST['preset_search'] == 1)  //Generic (85% of max search)
			{
				$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = intval($maxsearch_x*0.85);
				$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = intval($maxsearch_y*0.85);
				$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
				$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
				$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
				$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
				$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
				$_POST['r1_mask_width_x'] = $r1_mask_width_x = max(intval($Nx1*0.9),intval($Nx1-2.5*$r1_mask_apod_x));$_POST['r1_mask_width_y'] = $r1_mask_width_y = max(intval($Ny1*0.9),intval($Ny1-2.5*$r1_mask_apod_y));
				$_POST['r2_mask_width_x'] = $r2_mask_width_x = max(intval($Nx2*0.9),intval($Nx2-2.5*$r2_mask_apod_x));$_POST['r2_mask_width_y'] = $r2_mask_width_y = max(intval($Ny2*0.9),intval($Ny2-2.5*$r2_mask_apod_y));
				$_POST['r3_mask_width_x'] = $r3_mask_width_x = max(intval($Nx3*0.9),intval($Nx3-2.5*$r3_mask_apod_x));$_POST['r3_mask_width_y'] = $r3_mask_width_y = max(intval($Ny3*0.9),intval($Ny3-2.5*$r3_mask_apod_y));
				$_POST['r4_mask_width_x'] = $r4_mask_width_x = max(intval($Nx4*0.9),intval($Nx4-2.5*$r4_mask_apod_x));$_POST['r4_mask_width_y'] = $r4_mask_width_y = max(intval($Ny4*0.9),intval($Ny4-2.5*$r4_mask_apod_y));
				$_POST['r5_mask_width_x'] = $r5_mask_width_x = max(intval($Nx5*0.9),intval($Nx5-2.5*$r5_mask_apod_x));$_POST['r5_mask_width_y'] = $r5_mask_width_y = max(intval($Ny5*0.9),intval($Ny5-2.5*$r5_mask_apod_y));
				$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = round($r1_hp_diam_x/2);
				$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = round($r1_hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 2)  //10% of max search
			{
				$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = intval($maxsearch_x*0.1);
				$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = intval($maxsearch_y*0.1);
				$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
				$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
				$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
				$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
				$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
				$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
				$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
				$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
				$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
				$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
				$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = round($r1_hp_diam_x/2);
				$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = round($r1_hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 3)  //25% of max search
			{
				$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = intval($maxsearch_x*0.25);
				$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = intval($maxsearch_y*0.25);
				$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
				$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
				$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
				$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
				$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
				$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
				$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
				$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
				$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
				$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
				$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = round($r1_hp_diam_x/2);
				$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = round($r1_hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 4)  //40% of max search
			{
				$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = intval($maxsearch_x*0.4);
				$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = intval($maxsearch_y*0.4);
				$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
				$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
				$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
				$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
				$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
				$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
				$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
				$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
				$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
				$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
				$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = round($r1_hp_diam_x/2);
				$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = round($r1_hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 5)  //50% of max search
			{
				$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = intval($maxsearch_x*0.5);
				$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = intval($maxsearch_y*0.5);
				$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
				$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
				$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
				$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
				$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
				$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
				$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
				$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
				$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
				$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
				$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = round($r1_hp_diam_x/2);
				$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = round($r1_hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 6)  //60% of max search
			{
				$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = intval($maxsearch_x*0.6);
				$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = intval($maxsearch_y*0.6);
				$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
				$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
				$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
				$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
				$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
				$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
				$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
				$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
				$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
				$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
				$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = round($r1_hp_diam_x/2);
				$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = round($r1_hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 7)  //75% of max search
			{
				$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = intval($maxsearch_x*0.75);
				$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = intval($maxsearch_y*0.75);
				$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
				$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
				$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
				$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
				$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
				$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
				$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
				$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
				$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
				$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
				$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = round($r1_hp_diam_x/2);
				$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = round($r1_hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 8)  //90% of max search
			{
				$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = intval($maxsearch_x*0.9);
				$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = intval($maxsearch_y*0.9);
				$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
				$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
				$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
				$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
				$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
				$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
				$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
				$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
				$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
				$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
				$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = round($r1_hp_diam_x/2);
				$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = round($r1_hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 2)  //Tiny 10%
			{
				$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = intval($imageinfo['dimx']*0.1);
				$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = intval($imageinfo['dimy']*0.1);
				$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
				$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
				$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
				$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
				$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
				$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
				$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
				$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
				$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
				$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
				$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = round($r1_hp_diam_x/2);
				$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = round($r1_hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 10)  //Small 25%
			{
				$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = intval($imageinfo['dimx']*0.25);
				$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = intval($imageinfo['dimy']*0.25);
				$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
				$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
				$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
				$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
				$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
				$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
				$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
				$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
				$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
				$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
				$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = round($r1_hp_diam_x/2);
				$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = round($r1_hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 11)  //Medium-Small 40%
			{
				$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = intval($imageinfo['dimx']*0.4);
				$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = intval($imageinfo['dimy']*0.4);
				$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
				$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
				$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
				$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
				$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
				$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
				$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
				$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
				$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
				$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
				$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = round($r1_hp_diam_x/2);
				$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = round($r1_hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 12)  //Medium 50%
			{
				$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = intval($imageinfo['dimx']*0.5);
				$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = intval($imageinfo['dimy']*0.5);
				$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
				$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
				$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
				$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
				$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
				$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
				$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
				$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
				$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
				$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
				$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = round($r1_hp_diam_x/2);
				$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = round($r1_hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 13)  //Medium-Large 60%
			{
				$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = intval($imageinfo['dimx']*0.6);
				$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = intval($imageinfo['dimy']*0.6);
				$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
				$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
				$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
				$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
				$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
				$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
				$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
				$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
				$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
				$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
				$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = round($r1_hp_diam_x/2);
				$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = round($r1_hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 14)  //Large 75%
			{
				$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = intval($imageinfo['dimx']*0.75);
				$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = intval($imageinfo['dimy']*0.75);
				$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
				$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
				$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
				$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
				$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
				$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
				$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
				$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
				$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
				$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
				$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = round($r1_hp_diam_x/2);
				$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = round($r1_hp_diam_y/2);
			}
			
			if ($_POST['preset_search'] == 15)  //Full 90%
			{
				$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = intval($imageinfo['dimx']*0.9);
				$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = intval($imageinfo['dimy']*0.9);
				$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
				$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
				$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
				$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
				$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
				$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
				$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
				$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
				$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
				$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
				$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
				$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = round($r1_hp_diam_x/2);
				$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = round($r1_hp_diam_y/2);
			}
			
			
			//Size Presets
			if ($_POST['preset_size'] == 1)  //Generic
			{
				$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(16*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(8*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(4*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(2*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
				$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
				$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
				$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
				$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
				$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
				$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
				$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
				$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
				$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
				$_POST['thickness'] = $thickness = "50,250,800,1500";
			}
			
			if ($_POST['preset_size'] == 2)  //Size 10 nm - Steep lowpass
			{
				$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(16*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(8*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(4*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(2*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
				$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
				$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
				$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
				$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
				$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
				$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
				$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
				$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
				$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
				$_POST['thickness'] = $thickness = "50,150,300,450";
			}
			
			if ($_POST['preset_size'] == 3)  //Size 25 nm - Steep lowpass
			{
				$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(32*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(16*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(8*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(4*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(2*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
				$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
				$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
				$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
				$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
				$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
				$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
				$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
				$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
				$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
				$_POST['thickness'] = $thickness = "400,750,1000,1250";
			}
			
			if ($_POST['preset_size'] == 4)  //Size 50 nm - Steep lowpass
			{
				$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(64*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(32*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(16*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(8*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(4*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
				$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
				$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
				$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
				$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
				$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
				$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
				$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
				$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
				$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
				$_POST['thickness'] = $thickness = "1200,1500,1900,2250";
			}
			
			if ($_POST['preset_size'] == 5)  //Size 100 nm - Steep lowpass
			{
				$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(128*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(64*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(32*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(16*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(8*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
				$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
				$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
				$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
				$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
				$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
				$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
				$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
				$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
				$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
				$_POST['thickness'] = $thickness = "2000,3000,4000,5000";
			}
			
			
			if ($_POST['preset_size'] == 7)  //Size 10 nm - Decreasing lowpass
			{
				$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(20*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(15*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(10*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(5*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(2*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
				$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
				$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
				$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
				$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
				$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
				$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
				$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
				$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
				$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
				$_POST['thickness'] = $thickness = "50,150,300,450";
			}
			
			if ($_POST['preset_size'] == 8)  //Size 25 nm - Decreasing lowpass
			{
				$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(40*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(30*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(20*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(10*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(5*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
				$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
				$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
				$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
				$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
				$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
				$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
				$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
				$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
				$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
				$_POST['thickness'] = $thickness = "400,750,1000,1250";
			}
			
			if ($_POST['preset_size'] == 9)  //Size 50 nm - Decreasing lowpass
			{
				$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(75*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(60*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(45*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(30*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(15*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
				$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
				$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
				$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
				$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
				$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
				$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
				$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
				$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
				$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
				$_POST['thickness'] = $thickness = "1200,1500,1900,2250";
			}
			
			if ($_POST['preset_size'] == 10)  //Size 100 nm - Decreasing lowpass
			{
				$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(350*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(200*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(150*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(100*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(50*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
				$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
				$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
				$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
				$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
				$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
				$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
				$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
				$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
				$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
				$_POST['thickness'] = $thickness = "2000,3000,4000,5000";
			}
			
			
			if ($_POST['preset_size'] == 12)  //Size 10 nm - Constant lowpass
			{
				$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=min(4*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=min(4*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_y));
				$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = round(2.5*$r1_lp_diam_x);
				$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = round(2.5*$r1_lp_diam_y);
				$_POST['thickness'] = $thickness = "50,150,300,450";
			}
			
			if ($_POST['preset_size'] == 13)  //Size 25 nm - Constant lowpass
			{
				$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=min(8*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=min(8*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_y));
				$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = round(2.5*$r1_lp_diam_x);
				$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = round(2.5*$r1_lp_diam_y);
				$_POST['thickness'] = $thickness = "400,750,1000,1250";
			}
			
			if ($_POST['preset_size'] == 14)  //Size 50 nm - Constant lowpass
			{
				$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=min(15*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=min(15*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_y));
				$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = round(2.5*$r1_lp_diam_x);
				$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = round(2.5*$r1_lp_diam_y);
				$_POST['thickness'] = $thickness = "1200,1500,1900,2250";
			}
			
			if ($_POST['preset_size'] == 15)  //Size 100 nm - Constant lowpass
			{
				$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=min(25*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_x));
				$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=min(25*round($imageinfo['pixelsize']*pow(10,10),2)*2, round(0.75*$r1_hp_diam_y));
				$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = round(2.5*$r1_lp_diam_x);
				$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = round(2.5*$r1_lp_diam_y);
				$_POST['thickness'] = $thickness = "2000,3000,4000,5000";
			}
			
			
			//Refinement Type Presets
			if ($_POST['preset_type'] == 1 or $_GET['preset_type'] == 1)  //Generic refinement
			{
				$_POST['r1_iters'] = $r1_iters = '10';
				$_POST['r2_iters'] = $r2_iters = '10';
				$_POST['r3_iters'] = $r3_iters = '5';
				$_POST['r4_iters'] = $r4_iters = '10';
				$_POST['r5_iters'] = $r5_iters = '0';
				$_POST['elevation_switch'] = $elevation_switch='';
				$_POST['scale_switch'] = $scale_switch='31';
				$_POST['rotation_switch'] = $rotation_switch='';
				$_POST['azimuth_switch'] = $azimuth_switch='';
				$_POST['orientation_switch'] = $orientation_switch='';
			}
			
			if ($_POST['preset_type'] == 2)  //Quick refinement
			{
				$_POST['r1_iters'] = $r1_iters = '10';
				$_POST['r2_iters'] = $r2_iters = '5';
				$_POST['r3_iters'] = $r3_iters = '5';
				$_POST['r4_iters'] = $r4_iters = '5';
				$_POST['r5_iters'] = $r5_iters = '0';
				$_POST['elevation_switch'] = $elevation_switch='';
				$_POST['scale_switch'] = $scale_switch='';
				$_POST['rotation_switch'] = $rotation_switch='';
				$_POST['azimuth_switch'] = $azimuth_switch='';
				$_POST['orientation_switch'] = $orientation_switch='';
			}
			
			if ($_POST['preset_type'] == 3)  //Modest refinement
			{
				$_POST['r1_iters'] = $r1_iters = '20';
				$_POST['r2_iters'] = $r2_iters = '15';
				$_POST['r3_iters'] = $r3_iters = '10';
				$_POST['r4_iters'] = $r4_iters = '10';
				$_POST['r5_iters'] = $r5_iters = '0';
				$_POST['elevation_switch'] = $elevation_switch='';
				$_POST['scale_switch'] = $scale_switch='51';
				$_POST['rotation_switch'] = $rotation_switch='';
				$_POST['azimuth_switch'] = $azimuth_switch='';
				$_POST['orientation_switch'] = $orientation_switch='';
			}
			
			if ($_POST['preset_type'] == 4)  //Full refinement
			{
				$_POST['r1_iters'] = $r1_iters = '20';
				$_POST['r2_iters'] = $r2_iters = '20';
				$_POST['r3_iters'] = $r3_iters = '20';
				$_POST['r4_iters'] = $r4_iters = '20';
				$_POST['r5_iters'] = $r5_iters = '0';
				$_POST['elevation_switch'] = $elevation_switch='';
				$_POST['scale_switch'] = $scale_switch='71';
				$_POST['rotation_switch'] = $rotation_switch='';
				$_POST['azimuth_switch'] = $azimuth_switch='';
				$_POST['orientation_switch'] = $orientation_switch='';
			}
			
			if ($_POST['preset_type'] == 5 or $_GET['preset_type'] == 5)  //Exhaustive refinement
			{
				$_POST['r1_iters'] = $r1_iters = '20';
				$_POST['r2_iters'] = $r2_iters = '20';
				$_POST['r3_iters'] = $r3_iters = '20';
				$_POST['r4_iters'] = $r4_iters = '40';
				$_POST['r5_iters'] = $r5_iters = '20';
				$_POST['elevation_switch'] = $elevation_switch='';
				$_POST['scale_switch'] = $scale_switch='81';
				$_POST['rotation_switch'] = $rotation_switch='';
				$_POST['azimuth_switch'] = $azimuth_switch='';
				$_POST['orientation_switch'] = $orientation_switch='';
				
			}
			
		}

		//These parameters don't change with Presets
		
		$map_size_x = intval($imageinfo['dimx']/$map_sampling);
		$map_size_y = intval($imageinfo['dimy']/$map_sampling);
		$r1_kernel_x = $r2_kernel_x = $r3_kernel_x = $r4_kernel_x = $r5_kernel_x = 5;
		$r1_kernel_y = $r2_kernel_y = $r3_kernel_y = $r4_kernel_y = $r5_kernel_y = 5;
		$r1_mask_apod_x = $r2_mask_apod_x = $r3_mask_apod_x = $r4_mask_apod_x = $r5_mask_apod_x = 10;
		$r1_mask_apod_y = $r2_mask_apod_y = $r3_mask_apod_y = $r4_mask_apod_y = $r5_mask_apod_y = 10;
		//$restart_cycle = $_SESSION['restart_cycle'];
		$image_file_type = pathinfo($imageinfo['filename'], PATHINFO_EXTENSION);
		$_SESSION['image_file_type'] = $image_file_type;
		$_SESSION['dimx'] = $imageinfo['dimx'];
		$_SESSION['dimy'] = $imageinfo['dimy'];
		$_POST['pixelsize'] = $imageinfo['pixelsize']*pow(10,10);
		$_POST['r1_sampling'] = 8; $_POST['r2_sampling'] = 4; $_POST['r3_sampling'] = 2; $_POST['r4_sampling'] = 1; $_POST['r5_sampling'] = 1;
		$_POST['translimit'] = intval(0.1*($imageinfo['dimx']+$imageinfo['dimy'])/2);
		
		// Shift rounds to the left
		if (intval($_GET['shift_left']) > 0 or intval($_SESSION['shift_left']) > 0)
		{
			if ($_POST['process'] != "Just Show Command") {
				for ($i = 1; $i <= intval($_GET['shift_left']); $i++) {
					if ($_POST['r2_iters'] != 0) {$_POST['r1_iters'] = $r1_iters = $_POST['r2_iters'];} $_POST['r2_iters'] = $r2_iters = $_POST['r3_iters']; $_POST['r3_iters'] = $r3_iters = $_POST['r4_iters']; $_POST['r4_iters'] = $r4_iters = $_POST['r5_iters']; $_POST['r5_iters'] = $r5_iters = 0;
					$_POST['r1_sampling'] = $r1_sampling = $_POST['r2_sampling']; $_POST['r2_sampling'] = $r2_sampling = $_POST['r3_sampling']; $_POST['r3_sampling'] = $r3_sampling = $_POST['r4_sampling']; $_POST['r4_sampling'] = $r4_sampling = $_POST['r5_sampling']; $_POST['r5_sampling'] = $r5_sampling = 1;
					$_POST['r1_mask_width_x'] = $r1_mask_width_x = $_POST['r2_mask_width_x']; $_POST['r2_mask_width_x'] = $r2_mask_width_x = $_POST['r3_mask_width_x']; $_POST['r3_mask_width_x'] = $r3_mask_width_x = $_POST['r4_mask_width_x']; $_POST['r4_mask_width_x'] = $r4_mask_width_x = $_POST['r5_mask_width_x'];
					$_POST['r1_mask_width_y'] = $r1_mask_width_y = $_POST['r2_mask_width_y']; $_POST['r2_mask_width_y'] = $r2_mask_width_y = $_POST['r3_mask_width_y']; $_POST['r3_mask_width_y'] = $r3_mask_width_y = $_POST['r4_mask_width_y']; $_POST['r4_mask_width_y'] = $r4_mask_width_y = $_POST['r5_mask_width_y'];
					$_POST['r1_highpass_apod_x'] = $r1_highpass_apod_x = $_POST['r2_highpass_apod_x']; $_POST['r2_highpass_apod_x'] = $r2_highpass_apod_x = $_POST['r3_highpass_apod_x']; $_POST['r3_highpass_apod_x'] = $r3_highpass_apod_x = $_POST['r4_highpass_apod_x']; $_POST['r4_highpass_apod_x'] = $r4_highpass_apod_x = $_POST['r5_highpass_apod_x'];
					$_POST['r1_highpass_apod_y'] = $r1_highpass_apod_y = $_POST['r2_highpass_apod_y']; $_POST['r2_highpass_apod_y'] = $r2_highpass_apod_y = $_POST['r3_highpass_apod_y']; $_POST['r3_highpass_apod_y'] = $r3_highpass_apod_y = $_POST['r4_highpass_apod_y']; $_POST['r4_highpass_apod_y'] = $r4_highpass_apod_y = $_POST['r5_highpass_apod_y'];
					$_POST['r1_lowpass_diameter_x'] = $r1_lowpass_diameter_x = $_POST['r2_lowpass_diameter_x']; $_POST['r2_lowpass_diameter_x'] = $r2_lowpass_diameter_x = $_POST['r3_lowpass_diameter_x']; $_POST['r3_lowpass_diameter_x'] = $r3_lowpass_diameter_x = $_POST['r4_lowpass_diameter_x']; $_POST['r4_lowpass_diameter_x'] = $r4_lowpass_diameter_x = $_POST['r5_lowpass_diameter_x'];
					$_POST['r1_lowpass_diameter_y'] = $r1_lowpass_diameter_y = $_POST['r2_lowpass_diameter_y']; $_POST['r2_lowpass_diameter_y'] = $r2_lowpass_diameter_y = $_POST['r3_lowpass_diameter_y']; $_POST['r3_lowpass_diameter_y'] = $r3_lowpass_diameter_y = $_POST['r4_lowpass_diameter_y']; $_POST['r4_lowpass_diameter_y'] = $r4_lowpass_diameter_y = $_POST['r5_lowpass_diameter_y'];
					$_POST['r1_lowpass_apod_x'] = $r1_lowpass_apod_x = $_POST['r2_lowpass_apod_x']; $_POST['r2_lowpass_apod_x'] = $r2_lowpass_apod_x = $_POST['r3_lowpass_apod_x']; $_POST['r3_lowpass_apod_x'] = $r3_lowpass_apod_x = $_POST['r4_lowpass_apod_x']; $_POST['r4_lowpass_apod_x'] = $r4_lowpass_apod_x = $_POST['r5_lowpass_apod_x'];
					$_POST['r1_lowpass_apod_y'] = $r1_lowpass_apod_y = $_POST['r2_lowpass_apod_y']; $_POST['r2_lowpass_apod_y'] = $r2_lowpass_apod_y = $_POST['r3_lowpass_apod_y']; $_POST['r3_lowpass_apod_y'] = $r3_lowpass_apod_y = $_POST['r4_lowpass_apod_y']; $_POST['r4_lowpass_apod_y'] = $r4_lowpass_apod_y = $_POST['r5_lowpass_apod_y'];
				}
				$_SESSION['shift_left'] = $_GET['shift_left'];
			} else {
				for ($i = 1; $i <= intval($_SESSION['shift_left']); $i++) {
					$_POST['r1_sampling'] = $r1_sampling = $_POST['r2_sampling']; $_POST['r2_sampling'] = $r2_sampling = $_POST['r3_sampling']; $_POST['r3_sampling'] = $r3_sampling = $_POST['r4_sampling']; $_POST['r4_sampling'] = $r4_sampling = $_POST['r5_sampling']; $_POST['r5_sampling'] = $r5_sampling = 1;
				}
			}
		}
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('appion-protomo', 'protomo');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'protomorun' );
		$this->setTitle( 'Protomo Refinement Launcher' );
		$this->setHeading( 'Protomo Refinement' );
		$this->setExeFile( 'protomo2aligner.py' );
		$this->setGuideURL( "https://github.com/nysbc/appion-protomo#example" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( True ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "protomo" );
				
		$params->addParam( "tiltseries", $tiltseries, "Tilt-Series #" );
		$params->addParam( "parallel", $parallel, "Parallelize Non-Protomo Processes" );
		$params->addParam( "starting_tlt_file", $starting_tlt_file, "Begin with Coarse Alignment Results, Manual Alignment, or Initial Alignment?" );
		$params->addParam( "negative", $negative, "<strong>–</strong> Angle Limit" );
		$params->addParam( "positive", $positive, "<strong>+</strong> Angle Limit" );
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
		$params->addParam( "map_sampling", $map_sampling, "Sampling for Depiction" );
		$params->addParam( "thickness", $thickness, "Thickness(es) (<strong>Critical Parameter</strong>)" );
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
		$params->addParam( "r1_lowpass_diameter_y", $r1_lp_diam_y, "R1" );
		$params->addParam( "r2_lowpass_diameter_y", $r2_lp_diam_y, "R2" );
		$params->addParam( "r3_lowpass_diameter_y", $r3_lp_diam_y, "R3" );
		$params->addParam( "r4_lowpass_diameter_y", $r4_lp_diam_y, "R4" );
		$params->addParam( "r5_lowpass_diameter_y", $r5_lp_diam_y, "R5 │ Lowpass Filter (y) (<strong>Critical Parameter</strong>)" );
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
		$params->addParam( "r1_corr_mode", $r1_corr_mode, "R1" );
		$params->addParam( "r2_corr_mode", $r2_corr_mode, "R2" );
		$params->addParam( "r3_corr_mode", $r3_corr_mode, "R3" );
		$params->addParam( "r4_corr_mode", $r4_corr_mode, "R4" );
		$params->addParam( "r5_corr_mode", $r5_corr_mode, "R5 | Correlation Mode (xcf, mcf, pcf, dbl)" );
		$params->addParam( "r1_iters", $r1_iters, "R1" );
		$params->addParam( "r2_iters", $r2_iters, "R2" );
		$params->addParam( "r3_iters", $r3_iters, "R3" );
		$params->addParam( "r4_iters", $r4_iters, "R4" );
		$params->addParam( "r5_iters", $r5_iters, "R5 │ Alignment Iterations" );
		$params->addParam( "param_file", $param, "External Param File" );
		$params->addParam( "binning", $binning, "Raw Image Binning" );
		$params->addParam( "preprocessing", $preprocessing, "Raw Image Preprocessing" );
		$params->addParam( "select_images", $select_images, "Select Specific Images" );
		$params->addParam( "tilt_azimuth", $tilt_azimuth, "Override Tilt Azimuth" );
		$params->addParam( "azimuth_stability_check", $azimuth_stability_check, "Check Azimuth Stability" );
		$params->addParam( "azimuth_max_deviation", $azimuth_max_deviation, "Maximum Deviation Allowed" );
		//$params->addParam( "exclude_images", $exclude_images, "Exclude Specific Images" );
		$params->addParam( "exclude_images_by_angle", $exclude_images_by_angle, "Exclude Images by Tilt Angles" );
		$params->addParam( "exclude_images_by_angle_accuracy", $exclude_images_by_angle_accuracy, "Accuracy" );
		$params->addParam( "border", $border, "Border Width for Exclusion" );
		$params->addParam( "clip_low", $clip_low, "Lower Clip (in SDs)" );
		$params->addParam( "clip_high", $clip_high, "Upper Clip (in SDs)" );
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
		$params->addParam( "r4_kernel_x", $r4_kernel_x, "R4" );
		$params->addParam( "r5_kernel_x", $r5_kernel_x, "R5 │ Filter Window Size (x)" );
		$params->addParam( "r1_kernel_y", $r1_kernel_y, "R1" );
		$params->addParam( "r2_kernel_y", $r2_kernel_y, "R2" );
		$params->addParam( "r3_kernel_y", $r3_kernel_y, "R3" );
		$params->addParam( "r4_kernel_y", $r4_kernel_y, "R4" );
		$params->addParam( "r5_kernel_y", $r5_kernel_y, "R5 │ Filter Window Size (y)" );
		$params->addParam( "grow", $grow, "Grow Binary Mask" );
		$params->addParam( "window_area", $window_area, "Window Area Fraction" );
		$params->addParam( "do_estimation", $do_estimation, "Estimate Geometric Parameters" );
		$params->addParam( "norotations", "$norotations", "No In-plane Rotations" );
		$params->addParam( "max_correction", $max_correction, "Correction Cutoff" );
		$params->addParam( "correlation_size_x", $correlation_size_x, "Size (x) of Cross-Correlation Video" );
		$params->addParam( "correlation_size_y", $correlation_size_y, "Size (y) of Cross-Correlation Video" );
		$params->addParam( "r1_peak_search_radius_x", $r1_peak_search_radius_x, "R1" );
		$params->addParam( "r2_peak_search_radius_x", $r2_peak_search_radius_x, "R2" );
		$params->addParam( "r3_peak_search_radius_x", $r3_peak_search_radius_x, "R3" );
		$params->addParam( "r4_peak_search_radius_x", $r4_peak_search_radius_x, "R4" );
		$params->addParam( "r5_peak_search_radius_x", $r5_peak_search_radius_x, "R5 │ Peak Search Radius (x)" );
		$params->addParam( "r1_peak_search_radius_y", $r1_peak_search_radius_y, "R1" );
		$params->addParam( "r2_peak_search_radius_y", $r2_peak_search_radius_y, "R2" );
		$params->addParam( "r3_peak_search_radius_y", $r3_peak_search_radius_y, "R3" );
		$params->addParam( "r4_peak_search_radius_y", $r4_peak_search_radius_y, "R4" );
		$params->addParam( "r5_peak_search_radius_y", $r5_peak_search_radius_y, "R5 │ Peak Search Radius (y)" );
		$params->addParam( "r1_cmdiameter_x", $r1_cmdiameter_x, "R1" );
		$params->addParam( "r2_cmdiameter_x", $r2_cmdiameter_x, "R2" );
		$params->addParam( "r3_cmdiameter_x", $r3_cmdiameter_x, "R3" );
		$params->addParam( "r4_cmdiameter_x", $r4_cmdiameter_x, "R4" );
		$params->addParam( "r5_cmdiameter_x", $r5_cmdiameter_x, "R5 │ Center of Mass Radius (x)" );
		$params->addParam( "r1_cmdiameter_y", $r1_cmdiameter_y, "R1" );
		$params->addParam( "r2_cmdiameter_y", $r2_cmdiameter_y, "R2" );
		$params->addParam( "r3_cmdiameter_y", $r3_cmdiameter_y, "R3" );
		$params->addParam( "r4_cmdiameter_y", $r4_cmdiameter_y, "R4" );
		$params->addParam( "r5_cmdiameter_y", $r5_cmdiameter_y, "R5 │ Center of Mass Radius (y)" );
		$params->addParam( "r1_cmdiameter", $r1_cmdiameter, "R1" );
		$params->addParam( "r2_cmdiameter", $r2_cmdiameter, "R2" );
		$params->addParam( "r3_cmdiameter", $r3_cmdiameter, "R3" );
		$params->addParam( "r4_cmdiameter", $r4_cmdiameter, "R4" );
		$params->addParam( "r5_cmdiameter", $r5_cmdiameter, "R5 │ Center of Mass Refinement" );
		$params->addParam( "translimit", $translimit, "Translational Limit" );
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
		$params->addParam( "create_tilt_video", $create_tilt_video, "Create Tilt-Series Videos" );
		$params->addParam( "create_reconstruction", $create_reconstruction, "Create a Reconstruction Video" );
		$params->addParam( "show_window_size", $show_window_size, "Show Window Size in Reconstruction Video" );
		$params->addParam( "keep_recons", $keep_recons, "Keep Intermediate Reconstruction" );
		$params->addParam( "slab", $slab, "Slab-Like Object" );
		$params->addParam( "map_size_x", $map_size_x, "Reconstructon Size (x)" );
		$params->addParam( "map_size_y", $map_size_y, "Reconstructon Size (y)" );
		$params->addParam( "tilt_clip", $tilt_clip, "Clip Tilt-Series Video Pixel Values" );
		$params->addParam( "video_type", $video_type, "Video Type" );
		$params->addParam( "restart_cycle", $restart_cycle, "Restart Refinement at Iteration" );
		$params->addParam( "change_refimg", $change_refimg, "Change Reference Image to Tilt Angle Closest to " );
		$params->addParam( "desired_ref_tilt_angle", $desired_ref_tilt_angle, "degrees" );
		$params->addParam( "defocus_save", $defocus_save, "Save Defocus Value" );
		$params->addParam( "restart_from_run", $restart_from_run, "Restart Refinement from Run at the " );
		$params->addParam( "restart_from_iteration", $restart_from_iteration, "Iteration" );
		
		// Validations
		if ($_POST['settings'] == 2 or $_POST['settings'] == 3)  //Basic or Advanced Settings
		{
			$params->addValidation( "r1_region_x", "req" );
			$params->addValidation( "r1_region_x", "num" );
			$params->addValidation( "r1_region_y", "req" );
			$params->addValidation( "r1_region_y", "num" );
			$params->addValidation( "thickness", "req" );
			//$params->addValidation( "thickness", "num" );
			$params->addValidation( "r1_iters", "req" );
			$params->addValidation( "r1_iters", "num" );
		}
	}
		
	// Generate a form for the parameters that are specific to this program (not Appion params)
	public function generateAdditionalFormLeft()
	{
		if ($_SESSION['erase_refine']==1)
		{
			$html .= "<br></br>
			<b><center>Either remove all previous Refinements by copying and pasting this series of commands into a terminal window (you can copy them all at once):</center></b>";
			$html .= "<br></br>
			<center><code>rm ".$_SESSION['outdir']."/".$_SESSION['runname']."/media/correlations/series".sprintf('%04d',$_SESSION['tiltseries'])."*<br>
			rm ".$_SESSION['outdir']."/".$_SESSION['runname']."/media/reconstructions/series".sprintf('%04d',$_SESSION['tiltseries'])."*<br>
			rm ".$_SESSION['outdir']."/".$_SESSION['runname']."/media/corrplots/series".sprintf('%04d',$_SESSION['tiltseries'])."*<br>
			rm ".$_SESSION['outdir']."/".$_SESSION['runname']."/media/tiltseries/series".sprintf('%04d',$_SESSION['tiltseries'])."*<br>
			rm ".$_SESSION['outdir']."/".$_SESSION['runname']."/media/quality_assessment/series".sprintf('%04d',$_SESSION['tiltseries'])."*<br>
			rm ".$_SESSION['outdir']."/".$_SESSION['runname']."/media/angle_refinement/series".sprintf('%04d',$_SESSION['tiltseries'])."*<br>
			rm ".$_SESSION['outdir']."/".$_SESSION['runname']."/cache/series".sprintf('%04d',$_SESSION['tiltseries'])."*<br>
			rm ".$_SESSION['outdir']."/".$_SESSION['runname']."/out/series".sprintf('%04d',$_SESSION['tiltseries'])."*<br>
			rm ".$_SESSION['outdir']."/".$_SESSION['runname']."/series".sprintf('%04d',$_SESSION['tiltseries']).".i3t<br>
			rm ".$_SESSION['outdir']."/".$_SESSION['runname']."/series".sprintf('%04d',$_SESSION['tiltseries']).".param<br>
			rm ".$_SESSION['outdir']."/".$_SESSION['runname']."/series".sprintf('%04d',$_SESSION['tiltseries'])."[0,1,2,3,4,5,6,7,8,9]*<br>
			rm ".$_SESSION['outdir']."/".$_SESSION['runname']."/best.*<br>
			rm ".$_SESSION['outdir']."/".$_SESSION['runname']."/worst.*<br></code></center>";
			
			$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineForm'><b><center>and then Click here or Refresh this page to continue</center></b></a>";
			$html .= "<br></br>
			<b><center>Or to continue from a refinement iteration, leave all files in place and <a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineForm'>Refresh</a> this page.</center></b>"; //<br>Then enter the iteration you would like to restart from into the 'Restart Refinement at Iteration' box.
			$_SESSION['erase_refine'] = 0;
			
		}
		else
		{
			$this->updateFormParams();
			$params = $this->getFormParams();
			
			global $html;
			
			$fieldSize = 5;
			$fieldSize2 = 3;
			$fieldSize3 = 10;
			
			if ($_POST['settings'] == 1 or $_POST['settings'] == 2)  //Express or Basic Settings
			{
				if ($_POST['settings'] == 1)  //Express Settings just hide all of the Basic Settings. Basic Settings are still required to be on the webpage somewhere.
					{$html.= '<div id="express" style="display:none">';}
				
				$html .= "
			    <br />
			    <H4>General Parameters ".docpop('genparam_info2', '(Info)')."</H4>
			    <hr />";
				$shift_left = $_GET['shift_left'] + 1;
				$html .= "<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineForm&shift_left=".$shift_left."&basic=1&preset_size=".$_POST['preset_size']."&preset_search=".$_POST['preset_search']."&preset_type=".$_POST['preset_type']."'><b><font size='3'>←</font>Shift Rounds Left</b></a><br>";
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
				$html.= $params->insertTextFieldInRow( "negative", $fieldSize ).'│ ';
				$html.= $params->insertTextField( "positive", $fieldSize );
				$html.= $params->insertTextFieldInRow( "exclude_images_by_angle", $fieldSize ).'│ ';
				$html.= $params->insertTextField( "exclude_images_by_angle_accuracy", $fieldSize );
				//$html.= '<select name="starting_tlt_file" style="width:111px">';
				//$html.= '<option value="Coarse_Iter_1">Coarse Iter 1</option>';
				//$html.= '<option selected value="Coarse_Iter_2">Coarse Iter 2</option>';
				//$html.= '<option value="Imod_Coarse">Imod Coarse</option>';
				//$html.= '<option value="Manual">Manual</option>';
				//$html.= '<option value="MoreManual">More Manual</option>';
				//$html.= '<option value="Initial">Initial</option>';
				//$html.= '<option value="My_tlt_file">My tlt file</option>';
				//$html.= '</select>'; $html.= docpop('protomo_starting_tlt_file', ' Begin with Coarse Alignment Results, Manual Alignment, or Initial Alignment?').'<br>';
				$html.= '<select name="parallel" style="width:51px">';
				$html.= '<option selected value="True">true</option>';
				$html.= '<option value="False">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_parallel', ' Parallelize Non-Protomo Processes').'<br>';
				//$html.= $params->insertTextField( "restart_cycle", $fieldSize2 );  //Not fully tested. Will be in a future release?
				
				$html .= "
			    <br />
			    <H4>Window Parameters ".docpop('windowparam_info', '(Info)')."</H4>
			    <hr />";
			    
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
				$html.= $params->insertTextField( "thickness", $fieldSize2 );
				
				$html .= "
			    <br />
			    <H4>Mask Parameters ".docpop('maskparam_info', '(Info)')."</H4>
			    <hr />";
			    
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
				
				$html .= "
			    <br />
			    <H4>Cross-Correlation Parameters ".docpop('crosscorrparam_info', '(Info)')."</H4>
			    <hr />";
				
				$html.= '<select name="r1_corr_mode" style="width:51px">';
				$html.= '<option value="xcf">xcf</option>';
				$html.= '<option selected value="mcf">mcf</option>';
				$html.= '<option value="pcf">pcf</option>';
				$html.= '<option value="dbl">dbl</option>';
				$html.= '</select>'; $html.= docpop('protomo_r1_corr_mode', ' R1').'│ ';
				$html.= '<select name="r2_corr_mode" style="width:51px">';
				$html.= '<option value="xcf">xcf</option>';
				$html.= '<option selected value="mcf">mcf</option>';
				$html.= '<option value="pcf">pcf</option>';
				$html.= '<option value="dbl">dbl</option>';
				$html.= '</select>'; $html.= docpop('protomo_r2_corr_mode', ' R2').'│ ';
				$html.= '<select name="r3_corr_mode" style="width:51px">';
				$html.= '<option value="xcf">xcf</option>';
				$html.= '<option selected value="mcf">mcf</option>';
				$html.= '<option value="pcf">pcf</option>';
				$html.= '<option value="dbl">dbl</option>';
				$html.= '</select>'; $html.= docpop('protomo_r3_corr_mode', ' R3').'│ ';
				$html.= '<select name="r4_corr_mode" style="width:51px">';
				$html.= '<option value="xcf">xcf</option>';
				$html.= '<option selected value="mcf">mcf</option>';
				$html.= '<option value="pcf">pcf</option>';
				$html.= '<option value="dbl">dbl</option>';
				$html.= '</select>'; $html.= docpop('protomo_r4_corr_mode', ' R4').'│ ';
				$html.= '<select name="r5_corr_mode" style="width:51px">';
				$html.= '<option value="xcf">xcf</option>';
				$html.= '<option value="mcf">mcf</option>';
				$html.= '<option selected value="pcf">pcf</option>';
				$html.= '<option value="dbl">dbl</option>';
				$html.= '</select>'; $html.= docpop('protomo_r5_corr_mode', ' R5 | Correlation Mode').'<br>';
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
				$html.= '<select name="r1_cmdiameter" style="width:51px">';
				$html.= '<option value="true">true</option>';
				$html.= '<option selected value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_r1_cmdiameter', ' R1').'│ ';
				$html.= '<select name="r2_cmdiameter" style="width:51px">';
				$html.= '<option value="true">true</option>';
				$html.= '<option selected value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_r2_cmdiameter', ' R2').'│ ';
				$html.= '<select name="r3_cmdiameter" style="width:51px">';
				$html.= '<option value="true">true</option>';
				$html.= '<option selected value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_r3_cmdiameter', ' R3').'│ ';
				$html.= '<select name="r4_cmdiameter" style="width:51px">';
				$html.= '<option value="true">true</option>';
				$html.= '<option selected value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_r4_cmdiameter', ' R4').'│ ';
				$html.= '<select name="r5_cmdiameter" style="width:51px">';
				$html.= '<option value="true">true</option>';
				$html.= '<option selected value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_r5_cmdiameter', ' R5 | Center of Mass Refinement').'<br>';
				
				$html .= "
			    <br />
			    <H4>Geometry Refinement Parameters ".docpop('geomrefineparam_info', '(Info)')."</H4>
			    <hr />";
				
				$html.= '<select name="orientation" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_orientation', ' Include Orientation Angles in Refinement').'│ ';
				$html.= $params->insertTextField( "orientation_switch", $fieldSize );
				$html.= '<select name="azimuth" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_azimuth', ' Include Tilt Azimuth in Refinement').'│ ';
				$html.= $params->insertTextField( "azimuth_switch", $fieldSize );
				$html.= '<select name="elevation" style="width:66px">';
				$html.= '<option value="true">true</option>';
				$html.= '<option selected value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_elevation', ' Include Tilt Axis Elevation in Refinement').'│ ';
				$html.= $params->insertTextField( "elevation_switch", $fieldSize );
				$html.= '<select name="rotation" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_rotation', ' Include In-plane Rotations in Refinement').'│ ';
				$html.= $params->insertTextField( "rotation_switch", $fieldSize );
				$html.= '<select name="scale" style="width:66px">';
				$html.= '<option value="true">true</option>';
				$html.= '<option selected value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_scale', ' Include Scale Factors (Magnification) in Refinement').'│ ';
				$html.= $params->insertTextField( "scale_switch", $fieldSize );
				
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
				$html.= '</select>'; $html.= docpop('protomo_create_tilt_video2', ' Create Tilt-Series Videos').'<br>';
				$html.= '<select name="create_reconstruction" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_create_reconstruction2', ' Create Reconstruction Videos').'<br>';
				$html.= '<select name="video_type" style="width:66px">';
				$html.= '<option value="gif">Gif</option>';
				$html.= '<option selected value="html5vid">HTML5</option>';
				$html.= '</select>'; $html.= docpop('protomo_video_type', ' Video Type').'<br>';
				
				$html .= "<hr />";
				if ($_POST['settings'] == 1)  //Express Settings
					{$html.= "</div>";}
			}
			
			if ($_POST['settings'] == 3)  //Advanced Settings
			{
				$html .= "
			    <br />
			    <H4>General Parameters ".docpop('genparam_info2', '(Info)')."</H4>
			    <hr />";
				$shift_left = $_GET['shift_left'] + 1;
				$html .= "<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineForm&shift_left=".$shift_left."&advanced=1&preset_size=".$_POST['preset_size']."&preset_search=".$_POST['preset_search']."&preset_type=".$_POST['preset_type']."'><b><font size='3'>←</font>Shift Rounds Left</b></a><br>";
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
				//$html.= $params->insertTextField( "select_images", $fieldSize );
				$html.= $params->insertTextFieldInRow( "negative", $fieldSize ).'│ ';
				$html.= $params->insertTextField( "positive", $fieldSize );
				$html.= $params->insertTextFieldInRow( "exclude_images_by_angle", $fieldSize ).'│ ';
				$html.= $params->insertTextField( "exclude_images_by_angle_accuracy", $fieldSize );
				$html.= '<select name="change_refimg" style="width:66px">';
				$html.= '<option value="True">True</option>';
				$html.= '<option selected value="False">False</option>';
				$html.= '</select>'; $html.= docpop('protomo_change_refimg', ' Change Reference Image to Tilt Angle Closest to ');
				$html.= $params->insertTextField( "desired_ref_tilt_angle", $fieldSize );
				//$html.= '<select name="starting_tlt_file" style="width:111px">';
				//$html.= '<option value="Coarse_Iter_1">Coarse Iter 1</option>';
				//$html.= '<option selected value="Coarse_Iter_2">Coarse Iter 2</option>';
				//$html.= '<option value="Imod_Coarse">Imod Coarse</option>';
				//$html.= '<option value="Manual">Manual</option>';
				//$html.= '<option value="MoreManual">More Manual</option>';
				//$html.= '<option value="Initial">Initial</option>';
				//$html.= '<option value="My_tlt_file">My tlt file</option>';
				//$html.= '</select>'; $html.= docpop('protomo_starting_tlt_file', ' Begin with Coarse Alignment Results or Initial Alignment?').'<br>';
				$html.= $params->insertTextField( "tilt_azimuth", $fieldSize );
				$html.= '<select name="azimuth_stability_check" style="width:66px">';
				$html.= '<option value="True">True</option>';
				$html.= '<option selected value="False">False</option>';
				$html.= '</select>'; $html.= docpop('protomo_azimuth_stability_check', ' Check Azimuth Stability').' | ';
				$html.= $params->insertTextField( "azimuth_max_deviation", $fieldSize );
				//$html.= $params->insertTextField( "exclude_images", $fieldSize );
				$html.= '<select name="parallel" style="width:66px">';
				$html.= '<option selected value="True">true</option>';
				$html.= '<option value="False">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_parallel', ' Parallelize Non-Protomo Processes').'<br>';
				$html.= '<select name="logging" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_logging', ' Logging').'<br>';
				$html.= $params->insertTextField( "loglevel", $fieldSize );
				//$html.= $params->insertTextField( "restart_cycle", $fieldSize );
				$html.= $params->insertTextField( "defocus_save", $fieldSize );
				$html.= $params->insertTextFieldInRow( "restart_from_run", $fieldSize3 );
				$html.= $params->insertTextField( "restart_from_iteration", $fieldSize );
				
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
				$html.= '</select>'; $html.= docpop('protomo_gradient', ' Linear Gradient Subtraction').'│ ';
				$html.= $params->insertTextField( "gradient_switch", $fieldSize );
				$html.= '<select name="iter_gradient" style="width:66px">';
				$html.= '<option value="true">true</option>';
				$html.= '<option selected value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_iter_gradient', ' Iterate Gradient Subtraction Once').'│ ';
				$html.= $params->insertTextField( "iter_gradient_switch", $fieldSize );
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
				$html.= $params->insertTextFieldInRow( "r4_kernel_x", $fieldSize2 ).'│ ';
				$html.= $params->insertTextField( "r5_kernel_x", $fieldSize2 );
				$html.= $params->insertTextFieldInRow( "r1_kernel_y", $fieldSize2 ).'│ ';
				$html.= $params->insertTextFieldInRow( "r2_kernel_y", $fieldSize2 ).'│ ';
				$html.= $params->insertTextFieldInRow( "r3_kernel_y", $fieldSize2 ).'│ ';
				$html.= $params->insertTextFieldInRow( "r4_kernel_y", $fieldSize2 ).'│ ';
				$html.= $params->insertTextField( "r5_kernel_y", $fieldSize2 );
				$html.= $params->insertTextField( "grow", $fieldSize );
				
				$html .= "
			    <br />
			    <H4>Window Parameters ".docpop('windowparam_info', '(Info)')."</H4>
			    <hr />";
			    
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
				$html.= $params->insertTextField( "window_area", $fieldSize );
				$html.= $params->insertTextField( "thickness", $fieldSize );
				
				$html .= "
			    <br />
			    <H4>Mask Parameters ".docpop('maskparam_info', '(Info)')."</H4>
			    <hr />";
			    
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
				
				$html .= "
			    <br />
			    <H4>Cross-Correlation Parameters ".docpop('crosscorrparam_info', '(Info)')."</H4>
			    <hr />";
				
				$html.= '<select name="r1_corr_mode" style="width:51px">';
				$html.= '<option value="xcf">xcf</option>';
				$html.= '<option selected value="mcf">mcf</option>';
				$html.= '<option value="pcf">pcf</option>';
				$html.= '<option value="dbl">dbl</option>';
				$html.= '</select>'; $html.= docpop('protomo_r1_corr_mode', ' R1').'│ ';
				$html.= '<select name="r2_corr_mode" style="width:51px">';
				$html.= '<option value="xcf">xcf</option>';
				$html.= '<option selected value="mcf">mcf</option>';
				$html.= '<option value="pcf">pcf</option>';
				$html.= '<option value="dbl">dbl</option>';
				$html.= '</select>'; $html.= docpop('protomo_r2_corr_mode', ' R2').'│ ';
				$html.= '<select name="r3_corr_mode" style="width:51px">';
				$html.= '<option value="xcf">xcf</option>';
				$html.= '<option selected value="mcf">mcf</option>';
				$html.= '<option value="pcf">pcf</option>';
				$html.= '<option value="dbl">dbl</option>';
				$html.= '</select>'; $html.= docpop('protomo_r3_corr_mode', ' R3').'│ ';
				$html.= '<select name="r4_corr_mode" style="width:51px">';
				$html.= '<option value="xcf">xcf</option>';
				$html.= '<option selected value="mcf">mcf</option>';
				$html.= '<option value="pcf">pcf</option>';
				$html.= '<option value="dbl">dbl</option>';
				$html.= '</select>'; $html.= docpop('protomo_r4_corr_mode', ' R4').'│ ';
				$html.= '<select name="r5_corr_mode" style="width:51px">';
				$html.= '<option value="xcf">xcf</option>';
				$html.= '<option value="mcf">mcf</option>';
				$html.= '<option selected value="pcf">pcf</option>';
				$html.= '<option value="dbl">dbl</option>';
				$html.= '</select>'; $html.= docpop('protomo_r5_corr_mode', ' R5 | Correlation Mode').'<br>';
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
				$html.= $params->insertTextField( "translimit", $fieldSize );
				
				$html .= "
			    <br />
			    <H4>Area Matching Parameters ".docpop('areamatchinparam_info', '(Info)')."</H4>
			    <hr />";
				
				$html.= '<select name="do_estimation" style="width:66px">';
				$html.= '<option value="true">true</option>';
				$html.= '<option selected value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_do_estimation', ' Estimate Geometric Parameters').'<br>';
				$html.= '<select name="norotations" style="width:66px">';
				$html.= '<option value="true">true</option>';
				$html.= '<option selected value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_norotations', ' No In-plane Rotations').'<br>';
				
				$html .= "
			    <br />
			    <H4>Geometry Refinement Parameters ".docpop('geomrefineparam_info', '(Info)')."</H4>
			    <hr />";
				
				$html.= '<select name="orientation" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_orientation', ' Include Orientation Angles in Refinement').'│ ';
				$html.= $params->insertTextField( "orientation_switch", $fieldSize );
				$html.= '<select name="azimuth" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_azimuth', ' Include Tilt Azimuth in Refinement').'│ ';
				$html.= $params->insertTextField( "azimuth_switch", $fieldSize );
				$html.= '<select name="elevation" style="width:66px">';
				$html.= '<option value="true">true</option>';
				$html.= '<option selected value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_elevation', ' Include Tilt Axis Elevation in Refinement').'│ ';
				$html.= $params->insertTextField( "elevation_switch", $fieldSize );
				$html.= '<select name="rotation" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_rotation', ' Include In-plane Rotations in Refinement').'│ ';
				$html.= $params->insertTextField( "rotation_switch", $fieldSize );
				$html.= '<select name="scale" style="width:66px">';
				$html.= '<option value="true">true</option>';
				$html.= '<option selected value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_scale', ' Include Scale Factors (Magnification) in Refinement').'│ ';
				$html.= $params->insertTextField( "scale_switch", $fieldSize );
				
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
				$html.= '</select>'; $html.= docpop('protomo_create_tilt_video2', ' Create Tilt-Series Videos').'<br>';
				$html.= '<select name="tilt_clip" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_tilt_clip', ' Clip Tilt-Series Video Pixel Values').'<br>';
				$html.= '<select name="create_reconstruction" style="width:66px">';
				$html.= '<option selected value="true">true</option>';
				$html.= '<option value="false">false</option>';
				$html.= '</select>'; $html.= docpop('protomo_create_reconstruction2', ' Create Reconstruction Videos').'<br>';
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
				$html.= '</select>'; $html.= docpop('protomo_keep_recons', ' Keep Intermediate Reconstructions').'<br>';
				
				$html .= "<hr />";
			}
			
			// Only display link to next step in tomo processing if on completed Command page
			if (!isset($_POST['process']))
			{
				$html .= "<br></br>
				<b><center>[Choose appropriate presets and/or edit desired parameters then click 'Just Show Command']</center></b><br>";
			}
		}
		return $html;
	}		

	// Override the default build Command Function because the --session flag is not normal
	// for other Appion Loop methods and not included in the parent.
	public function buildCommand( $postArray )
	{
		$command   = parent::buildCommand( $postArray );global $tiltseries;
		global $sessionname;
		
		$pixelsize=$_POST['pixelsize'];
		$dimx=$_SESSION['dimx'];
		$dimy=$_SESSION['dimy'];
		$image_file_type=$_SESSION['image_file_type'];
		$command.="--tiltseries=$tiltseries ";
		$command.="--sessionname=$sessionname ";
		$command.="--pixelsize=$pixelsize ";
		$command.="--dimx=$dimx ";
		$command.="--dimy=$dimy ";
		if ($_SESSION['manual'] != 1) {$command.="--image_file_type=$image_file_type ";}
		$command.="--coarse=False ";
		if ($_POST['starting_tlt_file'] == 1) {$command = str_replace("--starting_tlt_file=1","--starting_tlt_file=Coarse_Iter_1",$command);}
		elseif ($_POST['starting_tlt_file'] == 2) {$command = str_replace("--starting_tlt_file=2","--starting_tlt_file=Coarse_Iter_2",$command);}
		elseif ($_POST['starting_tlt_file'] == 3) {$command = str_replace("--starting_tlt_file=3","--starting_tlt_file=Imod_Coarse",$command);}
		elseif ($_POST['starting_tlt_file'] == 4) {$command = str_replace("--starting_tlt_file=4","--starting_tlt_file=Manual",$command);}
		elseif ($_POST['starting_tlt_file'] == 5) {$command = str_replace("--starting_tlt_file=5","--starting_tlt_file=Initial",$command);}
		elseif ($_POST['starting_tlt_file'] == 6) {$command = str_replace("--starting_tlt_file=6","--starting_tlt_file=My_tlt_file",$command);}
		if (!is_numeric($_POST['thickness']) && strpos($_POST['thickness'], ".") == false){
			print gettype($_POST['thickness']);
			$command = str_replace("protomo2aligner.py","protomo2multirefine.py",$command);
			$command = str_replace("--thickness=","--thicknesses=",$command);
		}
		
		//Replace default presets with user-defined presets
		
		return $command." ";
	}
	
	// Use form footer to re-direct user
	// to the next step of the Protomo workflow.
	public function generateFormFooter()
	{
		global $tiltseries;
		global $sessionname;
		global $imageinfo;
		
		$_SESSION['thickness'] = $_POST['thickness'];
		$_SESSION['tiltseries'] = $tiltseries;
		$_SESSION['runname'] = $_POST['runname'];
		$_SESSION['sessionname'] = $sessionname;
		$_SESSION['outdir'] = $_POST['outdir'];
		$_SESSION['iters'] = $_POST['r1_iters'] + $_POST['r2_iters'] + $_POST['r3_iters'] + $_POST['r4_iters'] + $_POST['r5_iters'];
		$_SESSION['imageinfo'] = $imageinfo;
		$_SESSION['protomo_outdir'] = $_POST['protomo_outdir'];
		$_SESSION['preset_size'] = $_POST['preset_size'];
		$_SESSION['preset_search'] = $_POST['preset_search'];
		$_SESSION['preset_type'] = $_POST['preset_type'];

		// Only display link to next step in tomo processing if on completed Command page
		if (!is_numeric($_POST['thickness']) && strpos($_POST['thickness'], ".") == false AND isset($_POST['process']))
		{
			$html .= openRoundBorder();
			$html .= "<table border='0'>";
			$html .= "<br></br>
				<b><center>[This command runs multiple refinements with the different requested thicknesses.<br>To access a particular refinement run, return back to 'Align Tilt-Series' on the left and input the appropriate runname.]</center></b><br>";
			$html .= "<br>
				<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2ReconstructionForm'><b><center>[Click here to continue onto <font size='4'>Reconstruction</font> for ".$_SESSION['runname']."] <font size='5'>→</font></center></b></a>";
			$html .= "<br></tr>\n";
			$html .= "</table>\n";
			$html .= closeRoundBorder();
		} elseif (isset($_POST['r1_region_x']) AND isset($_POST['r1_region_y']) AND isset($_POST['thickness']) AND isset($_SESSION['iters']) AND isset($_POST['process']))
		{
			$html .= openRoundBorder();
			$html .= "<table border='0'>";
			$html .= "<br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2RefineSummary'><b><center>[Click here to <font size='4'>View Refinement Results</font> after protomo2aligner.py has been run] <font size='5'>→</font></center></b></a>";
			$html .= "
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2BatchSummary&refine=1'><b><center>[Click here to <font size='4'>View Batch Refinement Results</font>] <font size='5'>→</font></center></b></a>";
			$html .= "<br></tr>\n";
			$html .= "</table>\n";
			$html .= closeRoundBorder();
		}
		return $html;
	}
		
}
?>
