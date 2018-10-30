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
require_once "inc/leginon.inc";

ini_set('session.gc_maxlifetime', 604800);
session_set_cookie_params(604800);

session_start();
$recon_thickness=$_SESSION['thickness'];
$sessionname=$_SESSION['sessionname'];
$imageinfo=$_SESSION['imageinfo'];
$preset_size = $_SESSION['preset_size'];
$preset_search = $_SESSION['preset_search'];
$preset_type = $_SESSION['preset_type'];

class Protomo2BatchForm extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML, $sessionname='', $raw_path='', $dimx='', $dimy='', $procs='all',$coarse_param_file='',
	$refine_param_file='', $recon_param_file='', $cachedir='', $protomo_outdir='', $link_recons='', $tiltseriesranges='', $firststep='1',
	$laststep='3', $shift_limit='90' , $angle_limit='60',  $imod_coarse_align='True', $r1_sampling='8', $r2_sampling='4', $r3_sampling='2', $r4_sampling='1', $r5_sampling='1',
	$r6_sampling='', $r7_sampling='', $r8_sampling='',$r1_iters='20', $r2_iters='15', $r3_iters='10', $r4_iters='5', $r5_iters='', $r6_iters='',
	$r7_iters='', $r8_iters='',$r1_lp_diam_x='15', $r2_lp_diam_x='15', $r3_lp_diam_x='15', $r4_lp_diam_x='15', $r5_lp_diam_x='',
	$r6_lp_diam_x='', $r7_lp_diam_x='', $r8_lp_diam_x='', $r1_lp_diam_y='', $r2_lp_diam_y='', $r3_lp_diam_y='', $r4_lp_diam_y='',
	$r5_lp_diam_y='', $r6_lp_diam_y='', $r7_lp_diam_y='', $r8_lp_diam_y='', $r1_region_x='', $r2_region_x='', $r3_region_x='',
	$r4_region_x='', $r5_region_x='', $r6_region_x='', $r7_region_x='', $r8_region_x='', $r1_region_y='', $r2_region_y='', $r3_region_y='',
	$r4_region_y='', $r5_region_y='', $r6_region_y='', $r7_region_y='', $r8_region_y='', $r1_lp_apod_x='', $r2_lp_apod_x='', $r3_lp_apod_x='',
	$r4_lp_apod_x='', $r5_lp_apod_x='', $r6_lp_apod_x='', $r7_lp_apod_x='', $r8_lp_apod_x='', $r1_lp_apod_y='', $r2_lp_apod_y='', $r3_lp_apod_y='',
	$r4_lp_apod_y='', $r5_lp_apod_y='', $r6_lp_apod_y='', $r7_lp_apod_y='', $r8_lp_apod_y='', $r1_hp_apod_x='', $r2_hp_apod_x='', $r3_hp_apod_x='',
	$r4_hp_apod_x='', $r5_hp_apod_x='', $r6_hp_apod_x='', $r7_hp_apod_x='', $r8_hp_apod_x='', $r1_hp_apod_y='', $r2_hp_apod_y='', $r3_hp_apod_y='',
	$r4_hp_apod_y='', $r5_hp_apod_y='', $r6_hp_apod_y='', $r7_hp_apod_y='', $r8_hp_apod_y='', $r1_mask_apod_x='10',
	$r2_mask_apod_x='10', $r3_mask_apod_x='10', $r4_mask_apod_x='10', $r5_mask_apod_x='10', $r6_mask_apod_x='10', $r7_mask_apod_x='', $r8_mask_apod_x='',
	$r1_mask_apod_y='10', $r2_mask_apod_y='10', $r3_mask_apod_y='10', $r4_mask_apod_y='10', $r5_mask_apod_y='10', $r6_mask_apod_y='10', $r7_mask_apod_y='',
	$r8_mask_apod_y='', $r1_peak_search_radius_x='300', $r2_peak_search_radius_x='300', $r3_peak_search_radius_x='300', $r4_peak_search_radius_x='300',
	$r5_peak_search_radius_x='300', $r6_peak_search_radius_x='', $r7_peak_search_radius_x='', $r8_peak_search_radius_x='', $r1_peak_search_radius_y='300',
	$r2_peak_search_radius_y='300', $r3_peak_search_radius_y='300', $r4_peak_search_radius_y='300', $r5_peak_search_radius_y='300', $r6_peak_search_radius_y='',
	$r7_peak_search_radius_y='', $r8_peak_search_radius_y='', $all_tilt_videos="false", $all_recon_videos="false", $r1_kernel_x='5', $r2_kernel_x='5',
	$r3_kernel_x='5', $r4_kernel_x='5', $r5_kernel_x='5', $r6_kernel_x='', $r7_kernel_x='', $r8_kernel_x='', $r1_kernel_y='5', $r2_kernel_y='5', $r3_kernel_y='5',
	$r4_kernel_y='5', $r5_kernel_y='5', $r6_kernel_y='', $r7_kernel_y='', $r8_kernel_y='', $r1_corr_mode='mcf', $r2_corr_mode='mcf', $r3_corr_mode='mcf',
	$r4_corr_mode='mcf', $r5_corr_mode='pcf', $r6_corr_mode='', $r7_corr_mode='', $r8_corr_mode='', $negative='', $positive='', 
	$orientation='true', $orientation_switch='', $azimuth='true', $azimuth_switch='', $elevation='false', $tilt_azimuth='',
	$elevation_switch='', $rotation='true', $rotation_switch='', $scale='false', $scale_switch='', $screening_start='1', $center_all_images='False',
	$recon_map_sampling='2', $recon_map_size_x='2048', $recon_map_size_y='2048', $recon_thickness='1500', $recon_iter='',$recon_iter_presets='',
	$auto_convergence='0.015', $auto_convergence_iters='5', $auto_ctf_correct='', $ctf_correct='', $amp_contrast_ctf='0.07', $iWidth='20', $DefocusTol='200',
	$map_sampling='8', $tilt_clip='', $show_window_size='', $pixelsize='', $video_type='', $dose_presets='', $dose_a='', $dose_b='', $dose_c='', $frame_aligned='',
	$defocus_estimate='', $defocus_min='', $defocus_max='', $defocus_difference='0.2', $amp_contrast_defocus='0.07', $res_min='10000', $res_max='10',
	$defocus_tlt='', $defocus_tlt_iteration='', $picking_gpu_or_cpu='', $template_location='', $estimated_particles='200', $distance_from_edges='25',
	$junk_tolerance='7', $change_refimg='', $desired_ref_tilt_angle=0)
	{
		parent::__construct($expId, $extraHTML);
		//print "_POST:" . "<br>";
		//var_dump($_POST);
		//print "_GET:" . "<br>";
		//var_dump($_GET);
		//print "_SESSION:" . "<br>";
		//var_dump($_SESSION);
		
		//foreach(array_keys($imageinfo) as $paramName){
		//	echo $paramName . "<br>";
		//	echo $imageinfo["$paramName"] . "<br>";}
		
		global $html;
		global $imageinfo;
		$particle = new particledata();
		$alltiltseries = $particle->getTiltSeries($_GET['expId']);
		$numtiltseries = count($alltiltseries);
		$tiltseriesranges="1-$numtiltseries";
		
		if (intval($imageinfo["dimx"] > 1)) {
			//Initialize steps
			if (!isset($_POST['firststep'])) {$_POST['firststep']=1;}
			if (!isset($_POST['laststep'])) {$_POST['laststep']=3;}
			//Check for impossible setting
			if ($_POST['firststep'] > $_POST['laststep']) {$_POST['laststep']=$_POST['firststep'];}
			if ($_POST['firststep'] == 5 or $_POST['firststep'] == 11 or $_POST['laststep'] == 5 or $_POST['laststep'] == 11) {$_POST['firststep']=1; $_POST['laststep']=3;}
			if (($_POST['firststep'] == 1 or $_POST['firststep'] == 2 or $_POST['firststep'] == 3 or $_POST['firststep'] == 4) and ($_POST['laststep'] == 6 or $_POST['laststep'] == 7 or $_POST['laststep'] == 8 or $_POST['laststep'] == 9 or $_POST['laststep'] == 10 or $_POST['laststep'] == 12)) {$_POST['laststep']=4;}
			if ($_POST['firststep'] == 6){$_POST['laststep']=6;}
			if ($_POST['firststep'] == 7){$_POST['laststep']=7;}
			if ($_POST['firststep'] == 8){$_POST['laststep']=8;}
			if ($_POST['firststep'] == 9){$_POST['laststep']=9;}
			if ($_POST['firststep'] == 10){$_POST['laststep']=10;}
			if ($_POST['firststep'] == 12){$_POST['laststep']=12;}
			if ($_POST['firststep'] == 14){$_POST['laststep']=14;}
			
			$steps=array("File Preparation", "Coarse Alignment", "Refinement", "Reconstruction", "----------------", "Screening Mode", "Defocus Estimation", "CTF Correction", "Dose Compensation", "3D Picking", "----------------", "Fully Automated", "----------------", "Export Tilt-Series");
			$html .= "<br>
				<b><center>Number of tilt-series available to process for session $sessionname: <font size='5'>$numtiltseries</font></center></b>";
			$html .= "
				<center>(Batch processing only operates on tiltseries#### directories)</center>";
			
			$html.= '<br><center><select name="firststep" onchange=submit() style="width:145px">';
			for ($i = 1; $i < count($steps)+1; $i++) {
				$html.= '<option ';
				if ($i == $_POST['firststep']) {
					$html.= 'selected ';
				}
				$html.= 'value="'.$i.'">'.$steps[$i-1].'</option>';
			}
			$html.= '</select>'; $html.= docpop('protomo_firststep', ' First Step').'<font size="6"> &nbsp&nbsp&nbsp→ &nbsp&nbsp&nbsp</font>';
			
			$html.= '<select name="laststep" onchange=submit() style="width:145px">';
			for ($i = 1; $i < count($steps)+1; $i++) {
				$html.= '<option ';
				if ($i == $_POST['laststep']) {
					$html.= 'selected ';
				}
				$html.= 'value="'.$i.'">'.$steps[$i-1].'</option>';
			}
			$html.= '</select>'; $html.= docpop('protomo_laststep', ' Last Step').'</center><br>';
			
			global $html2;
			global $html3;
			$html2 .= docpop('preset_info', 'Parameter Presets<br>');
			
			//Initialize presets
			if (!isset($_POST['preset_size'])) {$_POST['preset_size']=1;}
			if (!isset($_POST['preset_search'])) {$_POST['preset_search']=1;}
			if (!isset($_POST['preset_type'])) {$_POST['preset_type']=1;}
			if ($_POST['preset_size'] == 9) {$_POST['preset_size']=1;} //The dotted line divider
			if ($_POST['preset_size'] == 17) {$_POST['preset_size']=1;} //The dotted line divider
			
			//Preset pulldown menus
			$size_presets=array("Generic", "10 nm objects(s) - Steep lowpass", "25 nm objects(s) - Steep lowpass", "50 nm objects(s) - Steep lowpass", "100 nm objects(s) - Steep lowpass", "250 nm objects(s) - Steep lowpass", "500 nm objects(s) - Steep lowpass", "1000 nm objects(s) - Steep lowpass", "------------------", "10 nm objects(s) - Decreasing lowpass", "25 nm objects(s) - Decreasing lowpass", "50 nm objects(s) - Decreasing lowpass", "100 nm objects(s) - Decreasing lowpass", "250 nm objects(s) - Decreasing lowpass", "500 nm objects(s) - Decreasing lowpass", "1000 nm objects(s) - Decreasing lowpass", "------------------", "10 nm objects(s) - Constant lowpass", "25 nm objects(s) - Constant lowpass", "50 nm objects(s) - Constant lowpass", "100 nm objects(s) - Constant lowpass", "250 nm objects(s) - Constant lowpass", "500 nm objects(s) - Constant lowpass", "1000 nm objects(s) - Constant lowpass");
			$search_presets=array("Generic", "Tiny search (10%)", "Small search (25%)", "Med-Sm search (40%)", "Medium search (50%)", "Med-Lg search (60%)", "Large search (75%)", "Full search (90%)");		$type_presets=array("Generic", "Quick refinement", "Modest refinement", "Full refinement", "Exhaustive refinement");
			$html2.= '<select name="preset_size" onchange=submit() style="width:150px">';
			for ($i = 1; $i < count($size_presets)+1; $i++) {
				$html2.= '<option ';
				if ($i == $_POST['preset_size']) {
					$html2.= 'selected ';
				}
				$html2.= 'value="'.$i.'">'.$size_presets[$i-1].'</option>';
			}
			$html2.= '</select>'; $html2.= docpop('protomo_refine_presets_size', ' Object Size');
			
			$html2.= ' | <select name="preset_search" onchange=submit() style="width:150px">';
			for ($i = 1; $i < count($search_presets)+1; $i++) {
				$html2.= '<option ';
				if ($i == $_POST['preset_search']) {
					$html2.= 'selected ';
				}
				$html2.= 'value="'.$i.'">'.$search_presets[$i-1].'</option>';
			}
			$html2.= '</select>'; $html2.= docpop('protomo_refine_presets_search', ' Search Area');
			
			$html3.= ' | <select name="preset_type" onchange=submit() style="width:150px">';
			for ($i = 1; $i < count($type_presets)+1; $i++) {
				$html3.= '<option ';
				if ($i == $_POST['preset_type']) {
					$html3.= 'selected ';
				}
				$html3.= 'value="'.$i.'">'.$type_presets[$i-1].'</option>';
			}
			$html3.= '</select>'; $html3.= docpop('protomo_refine_presets_type', ' Refinement Type<br><br>');
			
			global $recon_thickness;
			$recon_map_size_x = $imageinfo['dimx'];
			$recon_map_size_y = $imageinfo['dimy'];
			$recon_thickness = $recon_thickness;
			$recon_lp_diam_x = round(pow(10,10)*$imageinfo['pixelsize']*8);
			$recon_lp_diam_y = round(pow(10,10)*$imageinfo['pixelsize']*8);
			$_POST['pixelsize'] = $imageinfo['pixelsize']*pow(10,10);
			$_POST['runname']=$_SESSION['runname'];
			$_POST['outdir']=$_SESSION['outdir'];
			$sessionname=$_SESSION['sessionname'];
			$defocus_min = $imageinfo['defocus']*pow(10,6)*-0.8;
			$defocus_max = $imageinfo['defocus']*pow(10,6)*-1.2;
			$res_max = round($imageinfo['pixelsize']*4*pow(10,10),1);
			
			$coarse_param_file=$_SESSION['outdir'].'/'.$_SESSION['runname'].'/ready_for_batch/coarse_series'.sprintf('%04d',$_SESSION['tiltseries']).'.param';
			$refine_param_file=$_SESSION['outdir'].'/'.$_SESSION['runname'].'/ready_for_batch/refine_series'.sprintf('%04d',$_SESSION['tiltseries']).'.param';
			$recon_param_file=$_SESSION['outdir'].'/'.$_SESSION['runname'].'/ready_for_batch/recon_series'.sprintf('%04d',$_SESSION['tiltseries']).'.param';
			$link_recons=$_SESSION['outdir'].'/'.'batch_tiltseries_out/';
			
			$_POST['tilt_clip'] = $tilt_clip='true';
			$_POST['show_window_size'] = $show_window_size='true';
			if ($imageinfo['dimx'] < 2049 or $imageinfo['dimy'] < 2049){
				$_POST['map_sampling'] = $map_sampling='4';
			}else{
				$_POST['map_sampling'] = $map_sampling='8';
			}
			
			if ($_POST['settings'] == 1 or $_POST['settings'] == 2)  //Express or Basic Settings
			{
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
			}
			
			////Refinement Preset Defaults////
			if ($_POST['process'] != "Just Show Command")
			{
				//Search Area Presets (placed before size presets because they depend on these)
				if ($_POST['preset_search'] == 1)  //Generic (50%)
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
				
				if ($_POST['preset_search'] == 3)  //Small 25%
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
				
				if ($_POST['preset_search'] == 4)  //Medium-Small 40%
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
				
				if ($_POST['preset_search'] == 5)  //Medium 50%
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
				
				if ($_POST['preset_search'] == 6)  //Medium-Large 60%
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
				
				if ($_POST['preset_search'] == 7)  //Large 75%
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
				
				if ($_POST['preset_search'] == 8)  //Full 90%
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
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(175, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(150, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(125, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(100, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(75, round(0.75*$r1_hp_diam_x));
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
					$_POST['thickness'] = $thickness = 1000;
				}
				
				if ($_POST['preset_size'] == 2)  //Size 10 nm - Steep lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(50, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(25, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(12.5, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(6.25, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(3.125, round(0.75*$r1_hp_diam_x));
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
					$_POST['thickness'] = $thickness = 500;
				}
				
				if ($_POST['preset_size'] == 3)  //Size 25 nm - Steep lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(125, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(62.5, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(31.25, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(15.625, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(7.8125, round(0.75*$r1_hp_diam_x));
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
					$_POST['thickness'] = $thickness = 1250;
				}
				
				if ($_POST['preset_size'] == 4)  //Size 50 nm - Steep lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(250, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(125, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(62.5, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(31.25, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(15.625, round(0.75*$r1_hp_diam_x));
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
					$_POST['thickness'] = $thickness = 2500;
				}
				
				if ($_POST['preset_size'] == 5)  //Size 100 nm - Steep lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(500, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(250, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(125, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(62.5, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(31.25, round(0.75*$r1_hp_diam_x));
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
					$_POST['thickness'] = $thickness = 5000;
				}
				
				if ($_POST['preset_size'] == 6)  //Size 250 nm - Steep lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(1250, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(625, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(312.5, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(156.25, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(78.125, round(0.75*$r1_hp_diam_x));
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
					$_POST['thickness'] = $thickness = 12500;
				}
				
				if ($_POST['preset_size'] == 7)  //Size 500 nm - Steep lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(2500, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(1250, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(625, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(312.5, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(156.25, round(0.75*$r1_hp_diam_x));
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
					$_POST['thickness'] = $thickness = 25000;
				}
				
				if ($_POST['preset_size'] == 8)  //Size 1000 nm - Steep lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(5000, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(2500, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(1250, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(625, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(310, round(0.75*$r1_hp_diam_x));
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
					$_POST['thickness'] = $thickness = 50000;
				}
				
				
				if ($_POST['preset_size'] == 10)  //Size 10 nm - Decreasing lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(100, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(75, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(50, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(30, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(10, round(0.75*$r1_hp_diam_x));
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
					$_POST['thickness'] = $thickness = 500;
				}
				
				if ($_POST['preset_size'] == 11)  //Size 25 nm - Decreasing lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(150, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(125, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(100, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(75, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(50, round(0.75*$r1_hp_diam_x));
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
					$_POST['thickness'] = $thickness = 1250;
				}
				
				if ($_POST['preset_size'] == 12)  //Size 50 nm - Decreasing lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(400, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(300, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(200, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(150, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(100, round(0.75*$r1_hp_diam_x));
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
					$_POST['thickness'] = $thickness = 2500;
				}
				
				if ($_POST['preset_size'] == 13)  //Size 100 nm - Decreasing lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(800, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(600, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(400, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(300, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(200, round(0.75*$r1_hp_diam_x));
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
					$_POST['thickness'] = $thickness = 5000;
				}
				
				if ($_POST['preset_size'] == 14)  //Size 250 nm - Decreasing lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(1500, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(1250, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(1000, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(750, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(500, round(0.75*$r1_hp_diam_x));
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
					$_POST['thickness'] = $thickness = 12500;
				}
				
				if ($_POST['preset_size'] == 15)  //Size 500 nm - Decreasing lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(4000, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(3000, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(2000, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(1500, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(1000, round(0.75*$r1_hp_diam_x));
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
					$_POST['thickness'] = $thickness = 25000;
				}
				
				if ($_POST['preset_size'] == 16)  //Size 1000 nm - Decreasing lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(8000, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(6000, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(4000, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(3000, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(2000, round(0.75*$r1_hp_diam_x));
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
					$_POST['thickness'] = $thickness = 50000;
				}
				
				
				if ($_POST['preset_size'] == 18)  //Size 10 nm - Constant lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=min(50, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=min(50, round(0.75*$r1_hp_diam_y));
					$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['thickness'] = $thickness = 500;
				}
				
				if ($_POST['preset_size'] == 19)  //Size 25 nm - Constant lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=min(125, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=min(125, round(0.75*$r1_hp_diam_y));
					$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['thickness'] = $thickness = 1250;
				}
				
				if ($_POST['preset_size'] == 20)  //Size 50 nm - Constant lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=min(250, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=min(250, round(0.75*$r1_hp_diam_y));
					$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['thickness'] = $thickness = 2500;
				}
				
				if ($_POST['preset_size'] == 21)  //Size 100 nm - Constant lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=min(500, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=min(500, round(0.75*$r1_hp_diam_y));
					$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['thickness'] = $thickness = 5000;
				}
				
				if ($_POST['preset_size'] == 22)  //Size 250 nm - Constant lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=min(1250, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=min(1250, round(0.75*$r1_hp_diam_y));
					$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['thickness'] = $thickness = 12500;
				}
				
				if ($_POST['preset_size'] == 23)  //Size 500 nm - Constant lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=min(2500, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=min(2500, round(0.75*$r1_hp_diam_y));
					$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['thickness'] = $thickness = 25000;
				}
				
				if ($_POST['preset_size'] == 24)  //Size 1000 nm - Constant lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=min(5000, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=min(5000, round(0.75*$r1_hp_diam_y));
					$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['thickness'] = $thickness = 50000;
				}
				
				
				//Refinement Type Presets
				if ($_POST['preset_type'] == 1)  //Generic refinement
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
				
				if ($_POST['preset_type'] == 5)  //Exhaustive refinement
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
			
			#Auto Refine Presets
			if ($_POST['firststep'] == 12 and $_POST['process'] != "Just Show Command"){
				$_POST['r1_iters'] = $r1_iters = '20';
				$_POST['r2_iters'] = $r2_iters = '20';
				$_POST['r3_iters'] = $r3_iters = '20';
				$_POST['r4_iters'] = $r4_iters = '20';
				$_POST['r5_iters'] = $r5_iters = '20';
				$_POST['r6_iters'] = $r6_iters = '20';
				$_POST['r7_iters'] = $r7_iters = '20';
				$_POST['r8_iters'] = $r8_iters = '20';
				$_POST['r1_sampling'] = $r1_sampling = '8';
				$_POST['r2_sampling'] = $r2_sampling = '6';
				$_POST['r3_sampling'] = $r3_sampling = '4';
				$_POST['r4_sampling'] = $r4_sampling = '2';
				$_POST['r5_sampling'] = $r5_sampling = '1';
				$_POST['r6_sampling'] = $r6_sampling = '4';
				$_POST['r7_sampling'] = $r7_sampling = '2';
				$_POST['r8_sampling'] = $r8_sampling = '1';
				$_POST['elevation_switch'] = $elevation_switch='131';
				$_POST['scale_switch'] = $scale_switch='101';
				$_POST['r6_kernel_x'] = $r6_kernel_x='5';
				$_POST['r7_kernel_x'] = $r7_kernel_x='5';
				$_POST['r8_kernel_x'] = $r8_kernel_x='5';
				$_POST['r6_kernel_y'] = $r6_kernel_y='5';
				$_POST['r7_kernel_y'] = $r7_kernel_y='5';
				$_POST['r8_kernel_y'] = $r8_kernel_y='5';
				$_POST['r6_mask_apod_x'] = $r6_mask_apod_x='10';
				$_POST['r7_mask_apod_x'] = $r7_mask_apod_x='10';
				$_POST['r8_mask_apod_x'] = $r8_mask_apod_x='10';
				$_POST['r6_mask_apod_y'] = $r6_mask_apod_y='10';
				$_POST['r7_mask_apod_y'] = $r7_mask_apod_y='10';
				$_POST['r8_mask_apod_y'] = $r8_mask_apod_y='10';
				$_POST['r6_peak_search_radius_x'] = $r6_peak_search_radius_x='300';
				$_POST['r7_peak_search_radius_x'] = $r7_peak_search_radius_x='300';
				$_POST['r8_peak_search_radius_x'] = $r8_peak_search_radius_x='300';
				$_POST['r6_peak_search_radius_y'] = $r6_peak_search_radius_y='300';
				$_POST['r7_peak_search_radius_y'] = $r7_peak_search_radius_y='300';
				$_POST['r8_peak_search_radius_y'] = $r8_peak_search_radius_y='300';
				
				//Search Area Presets (placed before size presets because they depend on these)
				if ($_POST['preset_search'] == 1)  //Generic (50%)
				{
					$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $_POST['r6_region_x'] = $_POST['r7_region_x'] = $_POST['r8_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = $r6_region_x = $r7_region_x = $r8_region_x = intval($imageinfo['dimx']*0.5);
					$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $_POST['r6_region_y'] = $_POST['r7_region_y'] = $_POST['r8_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = $r6_region_y = $r7_region_y = $r8_region_y = intval($imageinfo['dimy']*0.5);
					$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
					$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
					$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
					$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
					$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
					$Nx6=$r6_region_x/$r6_sampling;$Ny6=$r6_region_y/$r6_sampling;
					$Nx7=$r7_region_x/$r7_sampling;$Ny7=$r7_region_y/$r7_sampling;
					$Nx8=$r8_region_x/$r8_sampling;$Ny8=$r8_region_y/$r8_sampling;
					$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
					$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
					$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
					$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
					$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
					$_POST['r6_mask_width_x'] = $r6_mask_width_x = intval($Nx6-2.5*$r6_mask_apod_x);$_POST['r6_mask_width_y'] = $r6_mask_width_y = intval($Ny6-2.5*$r6_mask_apod_y);
					$_POST['r7_mask_width_x'] = $r7_mask_width_x = intval($Nx7-2.5*$r7_mask_apod_x);$_POST['r7_mask_width_y'] = $r7_mask_width_y = intval($Ny7-2.5*$r7_mask_apod_y);
					$_POST['r8_mask_width_x'] = $r8_mask_width_x = intval($Nx8-2.5*$r8_mask_apod_x);$_POST['r8_mask_width_y'] = $r8_mask_width_y = intval($Ny8-2.5*$r8_mask_apod_y);
					$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = $r6_hp_diam_x = $r7_hp_diam_x = $r8_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
					$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = $r6_hp_diam_y = $r7_hp_diam_y = $r8_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
					$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $_POST['r6_highpass_apod_x'] = $_POST['r7_highpass_apod_x'] = $_POST['r8_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = $r6_hp_apod_x = $r7_hp_apod_x = $r8_hp_apod_x = round($r1_hp_diam_x/2);
					$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $_POST['r6_highpass_apod_y'] = $_POST['r7_highpass_apod_y'] = $_POST['r8_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = $r6_hp_apod_y = $r7_hp_apod_y = $r8_hp_apod_y = round($r1_hp_diam_y/2);
				}
				
				if ($_POST['preset_search'] == 2)  //Tiny 10%
				{
					$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $_POST['r6_region_x'] = $_POST['r7_region_x'] = $_POST['r8_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = $r6_region_x = $r7_region_x = $r8_region_x = intval($imageinfo['dimx']*0.1);
					$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $_POST['r6_region_y'] = $_POST['r7_region_y'] = $_POST['r8_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = $r6_region_y = $r7_region_y = $r8_region_y = intval($imageinfo['dimy']*0.1);
					$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
					$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
					$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
					$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
					$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
					$Nx6=$r6_region_x/$r6_sampling;$Ny6=$r6_region_y/$r6_sampling;
					$Nx7=$r7_region_x/$r7_sampling;$Ny7=$r7_region_y/$r7_sampling;
					$Nx8=$r8_region_x/$r8_sampling;$Ny8=$r8_region_y/$r8_sampling;
					$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
					$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
					$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
					$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
					$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
					$_POST['r6_mask_width_x'] = $r6_mask_width_x = intval($Nx6-2.5*$r6_mask_apod_x);$_POST['r6_mask_width_y'] = $r6_mask_width_y = intval($Ny6-2.5*$r6_mask_apod_y);
					$_POST['r7_mask_width_x'] = $r7_mask_width_x = intval($Nx7-2.5*$r7_mask_apod_x);$_POST['r7_mask_width_y'] = $r7_mask_width_y = intval($Ny7-2.5*$r7_mask_apod_y);
					$_POST['r8_mask_width_x'] = $r8_mask_width_x = intval($Nx8-2.5*$r8_mask_apod_x);$_POST['r8_mask_width_y'] = $r8_mask_width_y = intval($Ny8-2.5*$r8_mask_apod_y);
					$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = $r6_hp_diam_x = $r7_hp_diam_x = $r8_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
					$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = $r6_hp_diam_y = $r7_hp_diam_y = $r8_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
					$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $_POST['r6_highpass_apod_x'] = $_POST['r7_highpass_apod_x'] = $_POST['r8_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = $r6_hp_apod_x = $r7_hp_apod_x = $r8_hp_apod_x = round($r1_hp_diam_x/2);
					$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $_POST['r6_highpass_apod_y'] = $_POST['r7_highpass_apod_y'] = $_POST['r8_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = $r6_hp_apod_y = $r7_hp_apod_y = $r8_hp_apod_y = round($r1_hp_diam_y/2);
				}
				
				if ($_POST['preset_search'] == 3)  //Small 25%
				{
					$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $_POST['r6_region_x'] = $_POST['r7_region_x'] = $_POST['r8_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = $r6_region_x = $r7_region_x = $r8_region_x = intval($imageinfo['dimx']*0.25);
					$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $_POST['r6_region_y'] = $_POST['r7_region_y'] = $_POST['r8_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = $r6_region_y = $r7_region_y = $r8_region_y = intval($imageinfo['dimy']*0.25);
					$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
					$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
					$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
					$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
					$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
					$Nx6=$r6_region_x/$r6_sampling;$Ny6=$r6_region_y/$r6_sampling;
					$Nx7=$r7_region_x/$r7_sampling;$Ny7=$r7_region_y/$r7_sampling;
					$Nx8=$r8_region_x/$r8_sampling;$Ny8=$r8_region_y/$r8_sampling;
					$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
					$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
					$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
					$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
					$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
					$_POST['r6_mask_width_x'] = $r6_mask_width_x = intval($Nx6-2.5*$r6_mask_apod_x);$_POST['r6_mask_width_y'] = $r6_mask_width_y = intval($Ny6-2.5*$r6_mask_apod_y);
					$_POST['r7_mask_width_x'] = $r7_mask_width_x = intval($Nx7-2.5*$r7_mask_apod_x);$_POST['r7_mask_width_y'] = $r7_mask_width_y = intval($Ny7-2.5*$r7_mask_apod_y);
					$_POST['r8_mask_width_x'] = $r8_mask_width_x = intval($Nx8-2.5*$r8_mask_apod_x);$_POST['r8_mask_width_y'] = $r8_mask_width_y = intval($Ny8-2.5*$r8_mask_apod_y);
					$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = $r6_hp_diam_x = $r7_hp_diam_x = $r8_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
					$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = $r6_hp_diam_y = $r7_hp_diam_y = $r8_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
					$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $_POST['r6_highpass_apod_x'] = $_POST['r7_highpass_apod_x'] = $_POST['r8_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = $r6_hp_apod_x = $r7_hp_apod_x = $r8_hp_apod_x = round($r1_hp_diam_x/2);
					$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $_POST['r6_highpass_apod_y'] = $_POST['r7_highpass_apod_y'] = $_POST['r8_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = $r6_hp_apod_y = $r7_hp_apod_y = $r8_hp_apod_y = round($r1_hp_diam_y/2);
				}
				
				if ($_POST['preset_search'] == 4)  //Medium 50%
				{
					$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $_POST['r6_region_x'] = $_POST['r7_region_x'] = $_POST['r8_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = $r6_region_x = $r7_region_x = $r8_region_x = intval($imageinfo['dimx']*0.5);
					$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $_POST['r6_region_y'] = $_POST['r7_region_y'] = $_POST['r8_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = $r6_region_y = $r7_region_y = $r8_region_y = intval($imageinfo['dimy']*0.5);
					$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
					$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
					$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
					$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
					$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
					$Nx6=$r6_region_x/$r6_sampling;$Ny6=$r6_region_y/$r6_sampling;
					$Nx7=$r7_region_x/$r7_sampling;$Ny7=$r7_region_y/$r7_sampling;
					$Nx8=$r8_region_x/$r8_sampling;$Ny8=$r8_region_y/$r8_sampling;
					$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
					$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
					$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
					$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
					$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
					$_POST['r6_mask_width_x'] = $r6_mask_width_x = intval($Nx6-2.5*$r6_mask_apod_x);$_POST['r6_mask_width_y'] = $r6_mask_width_y = intval($Ny6-2.5*$r6_mask_apod_y);
					$_POST['r7_mask_width_x'] = $r7_mask_width_x = intval($Nx7-2.5*$r7_mask_apod_x);$_POST['r7_mask_width_y'] = $r7_mask_width_y = intval($Ny7-2.5*$r7_mask_apod_y);
					$_POST['r8_mask_width_x'] = $r8_mask_width_x = intval($Nx8-2.5*$r8_mask_apod_x);$_POST['r8_mask_width_y'] = $r8_mask_width_y = intval($Ny8-2.5*$r8_mask_apod_y);
					$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = $r6_hp_diam_x = $r7_hp_diam_x = $r8_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
					$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = $r6_hp_diam_y = $r7_hp_diam_y = $r8_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
					$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $_POST['r6_highpass_apod_x'] = $_POST['r7_highpass_apod_x'] = $_POST['r8_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = $r6_hp_apod_x = $r7_hp_apod_x = $r8_hp_apod_x = round($r1_hp_diam_x/2);
					$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $_POST['r6_highpass_apod_y'] = $_POST['r7_highpass_apod_y'] = $_POST['r8_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = $r6_hp_apod_y = $r7_hp_apod_y = $r8_hp_apod_y = round($r1_hp_diam_y/2);
				}
				
				if ($_POST['preset_search'] == 5)  //Large 75%
				{
					$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $_POST['r6_region_x'] = $_POST['r7_region_x'] = $_POST['r8_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = $r6_region_x = $r7_region_x = $r8_region_x = intval($imageinfo['dimx']*0.75);
					$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $_POST['r6_region_y'] = $_POST['r7_region_y'] = $_POST['r8_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = $r6_region_y = $r7_region_y = $r8_region_y = intval($imageinfo['dimy']*0.75);
					$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
					$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
					$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
					$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
					$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
					$Nx6=$r6_region_x/$r6_sampling;$Ny6=$r6_region_y/$r6_sampling;
					$Nx7=$r7_region_x/$r7_sampling;$Ny7=$r7_region_y/$r7_sampling;
					$Nx8=$r8_region_x/$r8_sampling;$Ny8=$r8_region_y/$r8_sampling;
					$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
					$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
					$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
					$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
					$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
					$_POST['r6_mask_width_x'] = $r6_mask_width_x = intval($Nx6-2.5*$r6_mask_apod_x);$_POST['r6_mask_width_y'] = $r6_mask_width_y = intval($Ny6-2.5*$r6_mask_apod_y);
					$_POST['r7_mask_width_x'] = $r7_mask_width_x = intval($Nx7-2.5*$r7_mask_apod_x);$_POST['r7_mask_width_y'] = $r7_mask_width_y = intval($Ny7-2.5*$r7_mask_apod_y);
					$_POST['r8_mask_width_x'] = $r8_mask_width_x = intval($Nx8-2.5*$r8_mask_apod_x);$_POST['r8_mask_width_y'] = $r8_mask_width_y = intval($Ny8-2.5*$r8_mask_apod_y);
					$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = $r6_hp_diam_x = $r7_hp_diam_x = $r8_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
					$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = $r6_hp_diam_y = $r7_hp_diam_y = $r8_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
					$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $_POST['r6_highpass_apod_x'] = $_POST['r7_highpass_apod_x'] = $_POST['r8_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = $r6_hp_apod_x = $r7_hp_apod_x = $r8_hp_apod_x = round($r1_hp_diam_x/2);
					$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $_POST['r6_highpass_apod_y'] = $_POST['r7_highpass_apod_y'] = $_POST['r8_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = $r6_hp_apod_y = $r7_hp_apod_y = $r8_hp_apod_y = round($r1_hp_diam_y/2);
				}
				
				if ($_POST['preset_search'] == 6)  //Full 90%
				{
					$_POST['r1_region_x'] = $_POST['r2_region_x'] = $_POST['r3_region_x'] = $_POST['r4_region_x'] = $_POST['r5_region_x'] = $_POST['r6_region_x'] = $_POST['r7_region_x'] = $_POST['r8_region_x'] = $r1_region_x = $r2_region_x = $r3_region_x = $r4_region_x = $r5_region_x = $r6_region_x = $r7_region_x = $r8_region_x = intval($imageinfo['dimx']*0.9);
					$_POST['r1_region_y'] = $_POST['r2_region_y'] = $_POST['r3_region_y'] = $_POST['r4_region_y'] = $_POST['r5_region_y'] = $_POST['r6_region_y'] = $_POST['r7_region_y'] = $_POST['r8_region_y'] = $r1_region_y = $r2_region_y = $r3_region_y = $r4_region_y = $r5_region_y = $r6_region_y = $r7_region_y = $r8_region_y = intval($imageinfo['dimy']*0.9);
					$Nx1=$r1_region_x/$r1_sampling;$Ny1=$r1_region_y/$r1_sampling;
					$Nx2=$r2_region_x/$r2_sampling;$Ny2=$r2_region_y/$r2_sampling;
					$Nx3=$r3_region_x/$r3_sampling;$Ny3=$r3_region_y/$r3_sampling;
					$Nx4=$r4_region_x/$r4_sampling;$Ny4=$r4_region_y/$r4_sampling;
					$Nx5=$r5_region_x/$r5_sampling;$Ny5=$r5_region_y/$r5_sampling;
					$Nx6=$r6_region_x/$r6_sampling;$Ny6=$r6_region_y/$r6_sampling;
					$Nx7=$r7_region_x/$r7_sampling;$Ny7=$r7_region_y/$r7_sampling;
					$Nx8=$r8_region_x/$r8_sampling;$Ny8=$r8_region_y/$r8_sampling;
					$_POST['r1_mask_width_x'] = $r1_mask_width_x = intval($Nx1-2.5*$r1_mask_apod_x);$_POST['r1_mask_width_y'] = $r1_mask_width_y = intval($Ny1-2.5*$r1_mask_apod_y);
					$_POST['r2_mask_width_x'] = $r2_mask_width_x = intval($Nx2-2.5*$r2_mask_apod_x);$_POST['r2_mask_width_y'] = $r2_mask_width_y = intval($Ny2-2.5*$r2_mask_apod_y);
					$_POST['r3_mask_width_x'] = $r3_mask_width_x = intval($Nx3-2.5*$r3_mask_apod_x);$_POST['r3_mask_width_y'] = $r3_mask_width_y = intval($Ny3-2.5*$r3_mask_apod_y);
					$_POST['r4_mask_width_x'] = $r4_mask_width_x = intval($Nx4-2.5*$r4_mask_apod_x);$_POST['r4_mask_width_y'] = $r4_mask_width_y = intval($Ny4-2.5*$r4_mask_apod_y);
					$_POST['r5_mask_width_x'] = $r5_mask_width_x = intval($Nx5-2.5*$r5_mask_apod_x);$_POST['r5_mask_width_y'] = $r5_mask_width_y = intval($Ny5-2.5*$r5_mask_apod_y);
					$_POST['r6_mask_width_x'] = $r6_mask_width_x = intval($Nx6-2.5*$r6_mask_apod_x);$_POST['r6_mask_width_y'] = $r6_mask_width_y = intval($Ny6-2.5*$r6_mask_apod_y);
					$_POST['r7_mask_width_x'] = $r7_mask_width_x = intval($Nx7-2.5*$r7_mask_apod_x);$_POST['r7_mask_width_y'] = $r7_mask_width_y = intval($Ny7-2.5*$r7_mask_apod_y);
					$_POST['r8_mask_width_x'] = $r8_mask_width_x = intval($Nx8-2.5*$r8_mask_apod_x);$_POST['r8_mask_width_y'] = $r8_mask_width_y = intval($Ny8-2.5*$r8_mask_apod_y);
					$_POST['r1_highpass_diameter_x'] = $_POST['r2_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $_POST['r3_highpass_diameter_x'] = $_POST['r4_highpass_diameter_x'] = $_POST['r5_highpass_diameter_x'] = $r1_hp_diam_x = $r2_hp_diam_x = $r3_hp_diam_x = $r4_hp_diam_x = $r5_hp_diam_x = $r6_hp_diam_x = $r7_hp_diam_x = $r8_hp_diam_x = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
					$_POST['r1_highpass_diameter_y'] = $_POST['r2_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $_POST['r3_highpass_diameter_y'] = $_POST['r4_highpass_diameter_y'] = $_POST['r5_highpass_diameter_y'] = $r1_hp_diam_y = $r2_hp_diam_y = $r3_hp_diam_y = $r4_hp_diam_y = $r5_hp_diam_y = $r6_hp_diam_y = $r7_hp_diam_y = $r8_hp_diam_y = round($imageinfo['pixelsize']*pow(10,10)*min($r1_region_x, $r1_region_y));
					$_POST['r1_highpass_apod_x'] = $_POST['r2_highpass_apod_x'] = $_POST['r3_highpass_apod_x'] = $_POST['r4_highpass_apod_x'] = $_POST['r5_highpass_apod_x'] = $_POST['r6_highpass_apod_x'] = $_POST['r7_highpass_apod_x'] = $_POST['r8_highpass_apod_x'] = $r1_hp_apod_x = $r2_hp_apod_x = $r3_hp_apod_x = $r4_hp_apod_x = $r5_hp_apod_x = $r6_hp_apod_x = $r7_hp_apod_x = $r8_hp_apod_x = round($r1_hp_diam_x/2);
					$_POST['r1_highpass_apod_y'] = $_POST['r2_highpass_apod_y'] = $_POST['r3_highpass_apod_y'] = $_POST['r4_highpass_apod_y'] = $_POST['r5_highpass_apod_y'] = $_POST['r6_highpass_apod_y'] = $_POST['r7_highpass_apod_y'] = $_POST['r8_highpass_apod_y'] = $r1_hp_apod_y = $r2_hp_apod_y = $r3_hp_apod_y = $r4_hp_apod_y = $r5_hp_apod_y = $r6_hp_apod_y = $r7_hp_apod_y = $r8_hp_apod_y = round($r1_hp_diam_y/2);
				}
				
				
				//Size Presets
				if ($_POST['preset_size'] == 1)  //Generic
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(175, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(150, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(125, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(100, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(75, round(0.75*$r1_hp_diam_x));
					$_POST['r6_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_y'] = $r6_lp_diam_x = $r6_lp_diam_y = min(125, round(0.75*$r1_hp_diam_x));
					$_POST['r7_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_y'] = $r7_lp_diam_x = $r7_lp_diam_y = min(100, round(0.75*$r1_hp_diam_x));
					$_POST['r8_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_y'] = $r8_lp_diam_x = $r8_lp_diam_y = min(75, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r6_lowpass_apod_x'] = $r6_lp_apod_x = round(2.5*$r6_lp_diam_x);
					$_POST['r7_lowpass_apod_x'] = $r7_lp_apod_x = round(2.5*$r7_lp_diam_x);
					$_POST['r8_lowpass_apod_x'] = $r8_lp_apod_x = round(2.5*$r8_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
					$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
					$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
					$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
					$_POST['r6_lowpass_apod_y'] = $r6_lp_apod_y = round(2.5*$r6_lp_diam_y);
					$_POST['r7_lowpass_apod_y'] = $r7_lp_apod_y = round(2.5*$r7_lp_diam_y);
					$_POST['r8_lowpass_apod_y'] = $r8_lp_apod_y = round(2.5*$r8_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 1000;
				}
				
				if ($_POST['preset_size'] == 2)  //Size 10 nm - Steep lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(50, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(25, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(12.5, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(6.25, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(3.125, round(0.75*$r1_hp_diam_x));
					$_POST['r6_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_y'] = $r6_lp_diam_x = $r6_lp_diam_y = min(12.5, round(0.75*$r1_hp_diam_x));
					$_POST['r7_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_y'] = $r7_lp_diam_x = $r7_lp_diam_y = min(6.25, round(0.75*$r1_hp_diam_x));
					$_POST['r8_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_y'] = $r8_lp_diam_x = $r8_lp_diam_y = min(3.125, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r6_lowpass_apod_x'] = $r6_lp_apod_x = round(2.5*$r6_lp_diam_x);
					$_POST['r7_lowpass_apod_x'] = $r7_lp_apod_x = round(2.5*$r7_lp_diam_x);
					$_POST['r8_lowpass_apod_x'] = $r8_lp_apod_x = round(2.5*$r8_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
					$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
					$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
					$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
					$_POST['r6_lowpass_apod_y'] = $r6_lp_apod_y = round(2.5*$r6_lp_diam_y);
					$_POST['r7_lowpass_apod_y'] = $r7_lp_apod_y = round(2.5*$r7_lp_diam_y);
					$_POST['r8_lowpass_apod_y'] = $r8_lp_apod_y = round(2.5*$r8_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 500;
				}
				
				if ($_POST['preset_size'] == 3)  //Size 25 nm - Steep lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(125, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(62.5, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(31.25, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(15.625, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(7.8125, round(0.75*$r1_hp_diam_x));
					$_POST['r6_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_y'] = $r6_lp_diam_x = $r6_lp_diam_y = min(31.25, round(0.75*$r1_hp_diam_x));
					$_POST['r7_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_y'] = $r7_lp_diam_x = $r7_lp_diam_y = min(15.625, round(0.75*$r1_hp_diam_x));
					$_POST['r8_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_y'] = $r8_lp_diam_x = $r8_lp_diam_y = min(7.8125, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
					$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
					$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
					$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
					$_POST['r6_lowpass_apod_y'] = $r6_lp_apod_y = round(2.5*$r6_lp_diam_y);
					$_POST['r7_lowpass_apod_y'] = $r7_lp_apod_y = round(2.5*$r7_lp_diam_y);
					$_POST['r8_lowpass_apod_y'] = $r8_lp_apod_y = round(2.5*$r8_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 1250;
				}
				
				if ($_POST['preset_size'] == 4)  //Size 50 nm - Steep lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(250, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(125, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(62.5, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(31.25, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(15.625, round(0.75*$r1_hp_diam_x));
					$_POST['r6_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_y'] = $r6_lp_diam_x = $r6_lp_diam_y = min(62.5, round(0.75*$r1_hp_diam_x));
					$_POST['r7_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_y'] = $r7_lp_diam_x = $r7_lp_diam_y = min(31.25, round(0.75*$r1_hp_diam_x));
					$_POST['r8_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_y'] = $r8_lp_diam_x = $r8_lp_diam_y = min(15.625, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r6_lowpass_apod_x'] = $r6_lp_apod_x = round(2.5*$r6_lp_diam_x);
					$_POST['r7_lowpass_apod_x'] = $r7_lp_apod_x = round(2.5*$r7_lp_diam_x);
					$_POST['r8_lowpass_apod_x'] = $r8_lp_apod_x = round(2.5*$r8_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
					$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
					$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
					$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
					$_POST['r6_lowpass_apod_y'] = $r6_lp_apod_y = round(2.5*$r6_lp_diam_y);
					$_POST['r7_lowpass_apod_y'] = $r7_lp_apod_y = round(2.5*$r7_lp_diam_y);
					$_POST['r8_lowpass_apod_y'] = $r8_lp_apod_y = round(2.5*$r8_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 2500;
				}
				
				if ($_POST['preset_size'] == 5)  //Size 100 nm - Steep lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(500, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(250, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(125, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(62.5, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(31.25, round(0.75*$r1_hp_diam_x));
					$_POST['r6_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_y'] = $r6_lp_diam_x = $r6_lp_diam_y = min(125, round(0.75*$r1_hp_diam_x));
					$_POST['r7_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_y'] = $r7_lp_diam_x = $r7_lp_diam_y = min(62.5, round(0.75*$r1_hp_diam_x));
					$_POST['r8_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_y'] = $r8_lp_diam_x = $r8_lp_diam_y = min(31.25, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r6_lowpass_apod_x'] = $r6_lp_apod_x = round(2.5*$r6_lp_diam_x);
					$_POST['r7_lowpass_apod_x'] = $r7_lp_apod_x = round(2.5*$r7_lp_diam_x);
					$_POST['r8_lowpass_apod_x'] = $r8_lp_apod_x = round(2.5*$r8_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
					$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
					$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
					$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
					$_POST['r6_lowpass_apod_y'] = $r6_lp_apod_y = round(2.5*$r6_lp_diam_y);
					$_POST['r7_lowpass_apod_y'] = $r7_lp_apod_y = round(2.5*$r7_lp_diam_y);
					$_POST['r8_lowpass_apod_y'] = $r8_lp_apod_y = round(2.5*$r8_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 5000;
				}
				
				if ($_POST['preset_size'] == 6)  //Size 250 nm - Steep lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(1250, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(625, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(312.5, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(156.25, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(78.125, round(0.75*$r1_hp_diam_x));
					$_POST['r6_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_y'] = $r6_lp_diam_x = $r6_lp_diam_y = min(312.5, round(0.75*$r1_hp_diam_x));
					$_POST['r7_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_y'] = $r7_lp_diam_x = $r7_lp_diam_y = min(156.25, round(0.75*$r1_hp_diam_x));
					$_POST['r8_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_y'] = $r8_lp_diam_x = $r8_lp_diam_y = min(78.125, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r6_lowpass_apod_x'] = $r6_lp_apod_x = round(2.5*$r6_lp_diam_x);
					$_POST['r7_lowpass_apod_x'] = $r7_lp_apod_x = round(2.5*$r7_lp_diam_x);
					$_POST['r8_lowpass_apod_x'] = $r8_lp_apod_x = round(2.5*$r8_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
					$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
					$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
					$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
					$_POST['r3_lowpass_apod_y'] = $r6_lp_apod_y = round(2.5*$r6_lp_diam_y);
					$_POST['r4_lowpass_apod_y'] = $r7_lp_apod_y = round(2.5*$r7_lp_diam_y);
					$_POST['r5_lowpass_apod_y'] = $r8_lp_apod_y = round(2.5*$r8_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 12500;
				}
				
				if ($_POST['preset_size'] == 7)  //Size 500 nm - Steep lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(2500, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(1250, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(625, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(312.5, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(156.25, round(0.75*$r1_hp_diam_x));
					$_POST['r6_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_y'] = $r6_lp_diam_x = $r6_lp_diam_y = min(625, round(0.75*$r1_hp_diam_x));
					$_POST['r7_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_y'] = $r7_lp_diam_x = $r7_lp_diam_y = min(312.5, round(0.75*$r1_hp_diam_x));
					$_POST['r8_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_y'] = $r8_lp_diam_x = $r8_lp_diam_y = min(156.25, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
					$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
					$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
					$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
					$_POST['r6_lowpass_apod_y'] = $r6_lp_apod_y = round(2.5*$r6_lp_diam_y);
					$_POST['r7_lowpass_apod_y'] = $r7_lp_apod_y = round(2.5*$r7_lp_diam_y);
					$_POST['r8_lowpass_apod_y'] = $r8_lp_apod_y = round(2.5*$r8_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 25000;
				}
				
				if ($_POST['preset_size'] == 8)  //Size 1000 nm - Steep lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(5000, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(2500, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(1250, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(625, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(310, round(0.75*$r1_hp_diam_x));
					$_POST['r6_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_y'] = $r6_lp_diam_x = $r6_lp_diam_y = min(1250, round(0.75*$r1_hp_diam_x));
					$_POST['r7_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_y'] = $r7_lp_diam_x = $r7_lp_diam_y = min(625, round(0.75*$r1_hp_diam_x));
					$_POST['r8_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_y'] = $r8_lp_diam_x = $r8_lp_diam_y = min(310, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r6_lowpass_apod_x'] = $r6_lp_apod_x = round(2.5*$r6_lp_diam_x);
					$_POST['r7_lowpass_apod_x'] = $r7_lp_apod_x = round(2.5*$r7_lp_diam_x);
					$_POST['r8_lowpass_apod_x'] = $r8_lp_apod_x = round(2.5*$r8_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
					$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
					$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
					$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
					$_POST['r6_lowpass_apod_y'] = $r6_lp_apod_y = round(2.5*$r6_lp_diam_y);
					$_POST['r7_lowpass_apod_y'] = $r7_lp_apod_y = round(2.5*$r7_lp_diam_y);
					$_POST['r8_lowpass_apod_y'] = $r8_lp_apod_y = round(2.5*$r8_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 50000;
				}
				
				
				if ($_POST['preset_size'] == 10)  //Size 10 nm - Decreasing lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(100, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(75, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(50, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(30, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(10, round(0.75*$r1_hp_diam_x));
					$_POST['r6_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_y'] = $r6_lp_diam_x = $r6_lp_diam_y = min(50, round(0.75*$r1_hp_diam_x));
					$_POST['r7_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_y'] = $r7_lp_diam_x = $r7_lp_diam_y = min(30, round(0.75*$r1_hp_diam_x));
					$_POST['r8_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_y'] = $r8_lp_diam_x = $r8_lp_diam_y = min(10, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r6_lowpass_apod_x'] = $r6_lp_apod_x = round(2.5*$r6_lp_diam_x);
					$_POST['r7_lowpass_apod_x'] = $r7_lp_apod_x = round(2.5*$r7_lp_diam_x);
					$_POST['r8_lowpass_apod_x'] = $r8_lp_apod_x = round(2.5*$r8_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
					$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
					$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
					$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
					$_POST['r6_lowpass_apod_y'] = $r6_lp_apod_y = round(2.5*$r6_lp_diam_y);
					$_POST['r7_lowpass_apod_y'] = $r7_lp_apod_y = round(2.5*$r7_lp_diam_y);
					$_POST['r8_lowpass_apod_y'] = $r8_lp_apod_y = round(2.5*$r8_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 500;
				}
				
				if ($_POST['preset_size'] == 11)  //Size 25 nm - Decreasing lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(150, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(125, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(100, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(75, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(50, round(0.75*$r1_hp_diam_x));
					$_POST['r6_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_y'] = $r6_lp_diam_x = $r6_lp_diam_y = min(100, round(0.75*$r1_hp_diam_x));
					$_POST['r7_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_y'] = $r7_lp_diam_x = $r7_lp_diam_y = min(75, round(0.75*$r1_hp_diam_x));
					$_POST['r8_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_y'] = $r8_lp_diam_x = $r8_lp_diam_y = min(50, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
					$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
					$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
					$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
					$_POST['r6_lowpass_apod_y'] = $r6_lp_apod_y = round(2.5*$r6_lp_diam_y);
					$_POST['r7_lowpass_apod_y'] = $r7_lp_apod_y = round(2.5*$r7_lp_diam_y);
					$_POST['r8_lowpass_apod_y'] = $r8_lp_apod_y = round(2.5*$r8_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 1250;
				}
				
				if ($_POST['preset_size'] == 12)  //Size 50 nm - Decreasing lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(400, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(300, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(200, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(150, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(100, round(0.75*$r1_hp_diam_x));
					$_POST['r6_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_y'] = $r6_lp_diam_x = $r6_lp_diam_y = min(200, round(0.75*$r1_hp_diam_x));
					$_POST['r7_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_y'] = $r7_lp_diam_x = $r7_lp_diam_y = min(150, round(0.75*$r1_hp_diam_x));
					$_POST['r8_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_y'] = $r8_lp_diam_x = $r8_lp_diam_y = min(100, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r6_lowpass_apod_x'] = $r6_lp_apod_x = round(2.5*$r6_lp_diam_x);
					$_POST['r7_lowpass_apod_x'] = $r7_lp_apod_x = round(2.5*$r7_lp_diam_x);
					$_POST['r8_lowpass_apod_x'] = $r8_lp_apod_x = round(2.5*$r8_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
					$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
					$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
					$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
					$_POST['r6_lowpass_apod_y'] = $r6_lp_apod_y = round(2.5*$r6_lp_diam_y);
					$_POST['r7_lowpass_apod_y'] = $r7_lp_apod_y = round(2.5*$r7_lp_diam_y);
					$_POST['r8_lowpass_apod_y'] = $r8_lp_apod_y = round(2.5*$r8_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 2500;
				}
				
				if ($_POST['preset_size'] == 13)  //Size 100 nm - Decreasing lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(800, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(600, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(400, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(300, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(200, round(0.75*$r1_hp_diam_x));
					$_POST['r6_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_y'] = $r6_lp_diam_x = $r6_lp_diam_y = min(400, round(0.75*$r1_hp_diam_x));
					$_POST['r7_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_y'] = $r7_lp_diam_x = $r7_lp_diam_y = min(300, round(0.75*$r1_hp_diam_x));
					$_POST['r8_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_y'] = $r8_lp_diam_x = $r8_lp_diam_y = min(200, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r6_lowpass_apod_x'] = $r6_lp_apod_x = round(2.5*$r6_lp_diam_x);
					$_POST['r7_lowpass_apod_x'] = $r7_lp_apod_x = round(2.5*$r7_lp_diam_x);
					$_POST['r8_lowpass_apod_x'] = $r8_lp_apod_x = round(2.5*$r8_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
					$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
					$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
					$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
					$_POST['r6_lowpass_apod_y'] = $r6_lp_apod_y = round(2.5*$r6_lp_diam_y);
					$_POST['r7_lowpass_apod_y'] = $r7_lp_apod_y = round(2.5*$r7_lp_diam_y);
					$_POST['r8_lowpass_apod_y'] = $r8_lp_apod_y = round(2.5*$r8_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 5000;
				}
				
				if ($_POST['preset_size'] == 14)  //Size 250 nm - Decreasing lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(1500, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(1250, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(1000, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(750, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(500, round(0.75*$r1_hp_diam_x));
					$_POST['r6_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_y'] = $r6_lp_diam_x = $r6_lp_diam_y = min(1000, round(0.75*$r1_hp_diam_x));
					$_POST['r7_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_y'] = $r7_lp_diam_x = $r7_lp_diam_y = min(750, round(0.75*$r1_hp_diam_x));
					$_POST['r8_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_y'] = $r8_lp_diam_x = $r8_lp_diam_y = min(500, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r6_lowpass_apod_x'] = $r6_lp_apod_x = round(2.5*$r6_lp_diam_x);
					$_POST['r7_lowpass_apod_x'] = $r7_lp_apod_x = round(2.5*$r7_lp_diam_x);
					$_POST['r8_lowpass_apod_x'] = $r8_lp_apod_x = round(2.5*$r8_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
					$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
					$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
					$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
					$_POST['r6_lowpass_apod_y'] = $r6_lp_apod_y = round(2.5*$r6_lp_diam_y);
					$_POST['r7_lowpass_apod_y'] = $r7_lp_apod_y = round(2.5*$r7_lp_diam_y);
					$_POST['r8_lowpass_apod_y'] = $r8_lp_apod_y = round(2.5*$r8_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 12500;
				}
				
				if ($_POST['preset_size'] == 15)  //Size 500 nm - Decreasing lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(4000, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(3000, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(2000, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(1500, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(1000, round(0.75*$r1_hp_diam_x));
					$_POST['r6_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_y'] = $r6_lp_diam_x = $r6_lp_diam_y = min(2000, round(0.75*$r1_hp_diam_x));
					$_POST['r7_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_y'] = $r7_lp_diam_x = $r7_lp_diam_y = min(1500, round(0.75*$r1_hp_diam_x));
					$_POST['r8_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_y'] = $r8_lp_diam_x = $r8_lp_diam_y = min(1000, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r6_lowpass_apod_x'] = $r6_lp_apod_x = round(2.5*$r6_lp_diam_x);
					$_POST['r7_lowpass_apod_x'] = $r7_lp_apod_x = round(2.5*$r7_lp_diam_x);
					$_POST['r8_lowpass_apod_x'] = $r8_lp_apod_x = round(2.5*$r8_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
					$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
					$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
					$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
					$_POST['r6_lowpass_apod_y'] = $r6_lp_apod_y = round(2.5*$r6_lp_diam_y);
					$_POST['r7_lowpass_apod_y'] = $r7_lp_apod_y = round(2.5*$r7_lp_diam_y);
					$_POST['r8_lowpass_apod_y'] = $r8_lp_apod_y = round(2.5*$r8_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 25000;
				}
				
				if ($_POST['preset_size'] == 16)  //Size 1000 nm - Decreasing lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r1_lowpass_diameter_y'] = $r1_lp_diam_x = $r1_lp_diam_y = min(8000, round(0.75*$r1_hp_diam_x));
					$_POST['r2_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_y'] = $r2_lp_diam_x = $r2_lp_diam_y = min(6000, round(0.75*$r1_hp_diam_x));
					$_POST['r3_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_y'] = $r3_lp_diam_x = $r3_lp_diam_y = min(4000, round(0.75*$r1_hp_diam_x));
					$_POST['r4_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_y'] = $r4_lp_diam_x = $r4_lp_diam_y = min(3000, round(0.75*$r1_hp_diam_x));
					$_POST['r5_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_y'] = $r5_lp_diam_x = $r5_lp_diam_y = min(2000, round(0.75*$r1_hp_diam_x));
					$_POST['r6_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_y'] = $r6_lp_diam_x = $r6_lp_diam_y = min(4000, round(0.75*$r1_hp_diam_x));
					$_POST['r7_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_y'] = $r7_lp_diam_x = $r7_lp_diam_y = min(3000, round(0.75*$r1_hp_diam_x));
					$_POST['r8_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_y'] = $r8_lp_diam_x = $r8_lp_diam_y = min(2000, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_apod_x'] = $r1_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r2_lowpass_apod_x'] = $r2_lp_apod_x = round(2.5*$r2_lp_diam_x);
					$_POST['r3_lowpass_apod_x'] = $r3_lp_apod_x = round(2.5*$r3_lp_diam_x);
					$_POST['r4_lowpass_apod_x'] = $r4_lp_apod_x = round(2.5*$r4_lp_diam_x);
					$_POST['r5_lowpass_apod_x'] = $r5_lp_apod_x = round(2.5*$r5_lp_diam_x);
					$_POST['r6_lowpass_apod_x'] = $r6_lp_apod_x = round(2.5*$r6_lp_diam_x);
					$_POST['r7_lowpass_apod_x'] = $r7_lp_apod_x = round(2.5*$r7_lp_diam_x);
					$_POST['r8_lowpass_apod_x'] = $r8_lp_apod_x = round(2.5*$r8_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $r1_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['r2_lowpass_apod_y'] = $r2_lp_apod_y = round(2.5*$r2_lp_diam_y);
					$_POST['r3_lowpass_apod_y'] = $r3_lp_apod_y = round(2.5*$r3_lp_diam_y);
					$_POST['r4_lowpass_apod_y'] = $r4_lp_apod_y = round(2.5*$r4_lp_diam_y);
					$_POST['r5_lowpass_apod_y'] = $r5_lp_apod_y = round(2.5*$r5_lp_diam_y);
					$_POST['r6_lowpass_apod_y'] = $r6_lp_apod_y = round(2.5*$r6_lp_diam_y);
					$_POST['r7_lowpass_apod_y'] = $r7_lp_apod_y = round(2.5*$r7_lp_diam_y);
					$_POST['r8_lowpass_apod_y'] = $r8_lp_apod_y = round(2.5*$r8_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 50000;
				}
				
				
				if ($_POST['preset_size'] == 18)  //Size 10 nm - Constant lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=$r6_lp_diam_x=$r7_lp_diam_x=$r8_lp_diam_x=min(50, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $_POST['r6_lowpass_diameter_y'] = $_POST['r7_lowpass_diameter_y'] = $_POST['r8_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=$r6_lp_diam_y=$r7_lp_diam_y=$r8_lp_diam_y=min(50, round(0.75*$r1_hp_diam_y));
					$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $_POST['r6_lowpass_apod_x'] = $_POST['r7_lowpass_apod_x'] = $_POST['r8_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = $r6_lp_apod_x = $r7_lp_apod_x = $r8_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $_POST['r6_lowpass_apod_y'] = $_POST['r7_lowpass_apod_y'] = $_POST['r8_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = $r6_lp_apod_y = $r7_lp_apod_y = $r8_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 500;
				}
				
				if ($_POST['preset_size'] == 19)  //Size 25 nm - Constant lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=$r6_lp_diam_x=$r7_lp_diam_x=$r8_lp_diam_x=min(125, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $_POST['r6_lowpass_diameter_y'] = $_POST['r7_lowpass_diameter_y'] = $_POST['r8_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=$r6_lp_diam_y=$r7_lp_diam_y=$r8_lp_diam_y=min(125, round(0.75*$r1_hp_diam_y));
					$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $_POST['r6_lowpass_apod_x'] = $_POST['r7_lowpass_apod_x'] = $_POST['r8_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = $r6_lp_apod_x = $r7_lp_apod_x = $r8_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $_POST['r6_lowpass_apod_y'] = $_POST['r7_lowpass_apod_y'] = $_POST['r8_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = $r6_lp_apod_y = $r7_lp_apod_y = $r8_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 1250;
				}
				
				if ($_POST['preset_size'] == 20)  //Size 50 nm - Constant lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=$r6_lp_diam_x=$r7_lp_diam_x=$r8_lp_diam_x=min(250, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $_POST['r6_lowpass_diameter_y'] = $_POST['r7_lowpass_diameter_y'] = $_POST['r8_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=$r6_lp_diam_y=$r7_lp_diam_y=$r8_lp_diam_y=min(250, round(0.75*$r1_hp_diam_y));
					$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $_POST['r6_lowpass_apod_x'] = $_POST['r7_lowpass_apod_x'] = $_POST['r8_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = $r6_lp_apod_x = $r7_lp_apod_x = $r8_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $_POST['r6_lowpass_apod_y'] = $_POST['r7_lowpass_apod_y'] = $_POST['r8_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = $r6_lp_apod_y = $r7_lp_apod_y = $r8_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 2500;
				}
				
				if ($_POST['preset_size'] == 21)  //Size 100 nm - Constant lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=$r6_lp_diam_x=$r7_lp_diam_x=$r8_lp_diam_x=min(500, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $_POST['r6_lowpass_diameter_y'] = $_POST['r7_lowpass_diameter_y'] = $_POST['r8_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=$r6_lp_diam_y=$r7_lp_diam_y=$r8_lp_diam_y=min(500, round(0.75*$r1_hp_diam_y));
					$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $_POST['r6_lowpass_apod_x'] = $_POST['r7_lowpass_apod_x'] = $_POST['r8_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = $r6_lp_apod_x = $r7_lp_apod_x = $r8_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $_POST['r6_lowpass_apod_y'] = $_POST['r7_lowpass_apod_y'] = $_POST['r8_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = $r6_lp_apod_y = $r7_lp_apod_y = $r8_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 5000;
				}
				
				if ($_POST['preset_size'] == 22)  //Size 250 nm - Constant lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=$r6_lp_diam_x=$r7_lp_diam_x=$r8_lp_diam_x=min(1250, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $_POST['r6_lowpass_diameter_y'] = $_POST['r7_lowpass_diameter_y'] = $_POST['r8_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=$r6_lp_diam_y=$r7_lp_diam_y=$r8_lp_diam_y=min(1250, round(0.75*$r1_hp_diam_y));
					$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $_POST['r6_lowpass_apod_x'] = $_POST['r7_lowpass_apod_x'] = $_POST['r8_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = $r6_lp_apod_x = $r7_lp_apod_x = $r8_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $_POST['r6_lowpass_apod_y'] = $_POST['r7_lowpass_apod_y'] = $_POST['r8_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = $r6_lp_apod_y = $r7_lp_apod_y = $r8_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 12500;
				}
				
				if ($_POST['preset_size'] == 23)  //Size 500 nm - Constant lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=$r6_lp_diam_x=$r7_lp_diam_x=$r8_lp_diam_x=min(2500, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $_POST['r6_lowpass_diameter_y'] = $_POST['r7_lowpass_diameter_y'] = $_POST['r8_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=$r6_lp_diam_y=$r7_lp_diam_y=$r8_lp_diam_y=min(2500, round(0.75*$r1_hp_diam_y));
					$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $_POST['r6_lowpass_apod_x'] = $_POST['r7_lowpass_apod_x'] = $_POST['r8_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = $r6_lp_apod_x = $r7_lp_apod_x = $r8_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $_POST['r6_lowpass_apod_y'] = $_POST['r7_lowpass_apod_y'] = $_POST['r8_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = $r6_lp_apod_y = $r7_lp_apod_y = $r8_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 25000;
				}
				
				if ($_POST['preset_size'] == 24)  //Size 1000 nm - Constant lowpass
				{
					$_POST['r1_lowpass_diameter_x'] = $_POST['r2_lowpass_diameter_x'] = $_POST['r3_lowpass_diameter_x'] = $_POST['r4_lowpass_diameter_x'] = $_POST['r5_lowpass_diameter_x'] = $_POST['r6_lowpass_diameter_x'] = $_POST['r7_lowpass_diameter_x'] = $_POST['r8_lowpass_diameter_x'] = $r1_lp_diam_x=$r2_lp_diam_x=$r3_lp_diam_x=$r4_lp_diam_x=$r5_lp_diam_x=$r6_lp_diam_x=$r7_lp_diam_x=$r8_lp_diam_x=min(5000, round(0.75*$r1_hp_diam_x));
					$_POST['r1_lowpass_diameter_y'] = $_POST['r2_lowpass_diameter_y'] = $_POST['r3_lowpass_diameter_y'] = $_POST['r4_lowpass_diameter_y'] = $_POST['r5_lowpass_diameter_y'] = $_POST['r6_lowpass_diameter_y'] = $_POST['r7_lowpass_diameter_y'] = $_POST['r8_lowpass_diameter_y'] = $r1_lp_diam_y=$r2_lp_diam_y=$r3_lp_diam_y=$r4_lp_diam_y=$r5_lp_diam_y=$r6_lp_diam_y=$r7_lp_diam_y=$r8_lp_diam_y=min(5000, round(0.75*$r1_hp_diam_y));
					$_POST['r1_lowpass_apod_x'] = $_POST['r2_lowpass_apod_x'] = $_POST['r3_lowpass_apod_x'] = $_POST['r4_lowpass_apod_x'] = $_POST['r5_lowpass_apod_x'] = $_POST['r6_lowpass_apod_x'] = $_POST['r7_lowpass_apod_x'] = $_POST['r8_lowpass_apod_x'] = $r1_lp_apod_x = $r2_lp_apod_x = $r3_lp_apod_x = $r4_lp_apod_x = $r5_lp_apod_x = $r6_lp_apod_x = $r7_lp_apod_x = $r8_lp_apod_x = round(2.5*$r1_lp_diam_x);
					$_POST['r1_lowpass_apod_y'] = $_POST['r2_lowpass_apod_y'] = $_POST['r3_lowpass_apod_y'] = $_POST['r4_lowpass_apod_y'] = $_POST['r5_lowpass_apod_y'] = $_POST['r6_lowpass_apod_y'] = $_POST['r7_lowpass_apod_y'] = $_POST['r8_lowpass_apod_y'] = $r1_lp_apod_y = $r2_lp_apod_y = $r3_lp_apod_y = $r4_lp_apod_y = $r5_lp_apod_y = $r6_lp_apod_y = $r7_lp_apod_y = $r8_lp_apod_y = round(2.5*$r1_lp_diam_y);
					$_POST['thickness'] = $_POST['recon_thickness'] = $thickness = $recon_thickness = 50000;
				}
			}
			
			$r1_kernel_x = $r2_kernel_x = $r3_kernel_x = $r4_kernel_x = $r5_kernel_x = 5;
			$r1_kernel_y = $r2_kernel_y = $r3_kernel_y = $r4_kernel_y = $r5_kernel_y = 5;
			$r1_mask_apod_x = $r2_mask_apod_x = $r3_mask_apod_x = $r4_mask_apod_x = $r5_mask_apod_x = 10;
			$r1_mask_apod_y = $r2_mask_apod_y = $r3_mask_apod_y = $r4_mask_apod_y = $r5_mask_apod_y = 10;
			$image_file_type = pathinfo($imageinfo['filename'], PATHINFO_EXTENSION);
			$_SESSION['image_file_type'] = $image_file_type;
			
			//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
			
			// Set the publications to be references on the web pages
			$pubList = array('appion-protomo', 'protomo','imodctf', 'tomoctf', 'dose_comp');
			$this->setPublications( $pubList );
			$this->setJobType( 'protomo' );
			$this->setOutputDirectory( 'protomo_alignments' );
			$this->setBaseRunName( 'batchrun' );
			$this->setTitle( 'Protomo Batch Refinement and Reconstruction Launcher' );
			$this->setHeading( 'Protomo Batch Refinement and Reconstruction' );
			$this->setExeFile( 'protomo2batch.py' );
			$this->setGuideURL( "https://github.com/nysbc/appion-protomo#example" );
			$this->setTestable( False ); // True to activate "test single image".
			$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
			$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
			
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
			$params->addParam( "tilt_azimuth", $tilt_azimuth, "Override Tilt Azimuth" );
			$params->addParam( "change_refimg", $change_refimg, "Change Reference Image to Tilt Angle Closest to " );
			$params->addParam( "desired_ref_tilt_angle", $desired_ref_tilt_angle, "degrees" );
			$params->addParam( "imod_coarse_align", $imod_coarse_align, "Coarse Align with Imod" );
			$params->addParam( "r1_region_x", $r1_region_x, "R1" );
			$params->addParam( "r2_region_x", $r2_region_x, "R2" );
			$params->addParam( "r3_region_x", $r3_region_x, "R3" );
			$params->addParam( "r4_region_x", $r4_region_x, "R4" );
			$params->addParam( "r5_region_x", $r5_region_x, "R5 │ Window Size (x) (<strong>Critical Parameter</strong>)" );
			$params->addParam( "r6_region_x", $r6_region_x, "R6" );
			$params->addParam( "r7_region_x", $r7_region_x, "R7" );
			$params->addParam( "r8_region_x", $r8_region_x, "R8 │ Window Size (x) (<strong>Critical Parameter</strong>)" );
			$params->addParam( "r1_region_y", $r1_region_y, "R1" );
			$params->addParam( "r2_region_y", $r2_region_y, "R2" );
			$params->addParam( "r3_region_y", $r3_region_y, "R3" );
			$params->addParam( "r4_region_y", $r4_region_y, "R4" );
			$params->addParam( "r5_region_y", $r5_region_y, "R5 │ Window Size (y) (<strong>Critical Parameter</strong>)" );
			$params->addParam( "r6_region_y", $r3_region_y, "R6" );
			$params->addParam( "r7_region_y", $r4_region_y, "R7" );
			$params->addParam( "r8_region_y", $r5_region_y, "R8 │ Window Size (y) (<strong>Critical Parameter</strong>)" );
			$params->addParam( "r1_sampling", $r1_sampling, "R1" );
			$params->addParam( "r2_sampling", $r2_sampling, "R2" );
			$params->addParam( "r3_sampling", $r3_sampling, "R3" );
			$params->addParam( "r4_sampling", $r4_sampling, "R4" );
			$params->addParam( "r5_sampling", $r5_sampling, "R5 │ Sampling" );
			$params->addParam( "r6_sampling", $r6_sampling, "R6" );
			$params->addParam( "r7_sampling", $r7_sampling, "R7" );
			$params->addParam( "r8_sampling", $r8_sampling, "R8 │ Sampling" );
			$params->addParam( "map_sampling", $map_sampling, "Sampling for Depiction" );
			$params->addParam( "thickness", $thickness, "Thickness, in angstroms (<strong>Critical Parameter</strong>)" );
			$params->addParam( "r1_kernel_x", $r1_kernel_x, "R1" );
			$params->addParam( "r2_kernel_x", $r2_kernel_x, "R2" );
			$params->addParam( "r3_kernel_x", $r3_kernel_x, "R3" );
			$params->addParam( "r4_kernel_x", $r4_kernel_x, "R4" );
			$params->addParam( "r5_kernel_x", $r5_kernel_x, "R5 │ Filter Window Size (x)" );
			$params->addParam( "r6_kernel_x", $r6_kernel_x, "R6" );
			$params->addParam( "r7_kernel_x", $r7_kernel_x, "R7" );
			$params->addParam( "r8_kernel_x", $r8_kernel_x, "R8 │ Filter Window Size (x)" );
			$params->addParam( "r1_kernel_y", $r1_kernel_y, "R1" );
			$params->addParam( "r2_kernel_y", $r2_kernel_y, "R2" );
			$params->addParam( "r3_kernel_y", $r3_kernel_y, "R3" );
			$params->addParam( "r4_kernel_y", $r4_kernel_y, "R4" );
			$params->addParam( "r5_kernel_y", $r5_kernel_y, "R5 │ Filter Window Size (y)" );
			$params->addParam( "r6_kernel_y", $r6_kernel_y, "R6" );
			$params->addParam( "r7_kernel_y", $r7_kernel_y, "R7" );
			$params->addParam( "r8_kernel_y", $r8_kernel_y, "R8 │ Filter Window Size (y)" );
			$params->addParam( "r1_mask_width_x", $r1_mask_width_x, "R1" );
			$params->addParam( "r2_mask_width_x", $r2_mask_width_x, "R2" );
			$params->addParam( "r3_mask_width_x", $r3_mask_width_x, "R3" );
			$params->addParam( "r4_mask_width_x", $r4_mask_width_x, "R4" );
			$params->addParam( "r5_mask_width_x", $r5_mask_width_x, "R5 │ Rectangular Mask Width (x)" );
			$params->addParam( "r6_mask_width_x", $r6_mask_width_x, "R6" );
			$params->addParam( "r7_mask_width_x", $r7_mask_width_x, "R7" );
			$params->addParam( "r8_mask_width_x", $r8_mask_width_x, "R8 │ Rectangular Mask Width (x)" );
			$params->addParam( "r1_mask_width_y", $r1_mask_width_y, "R1" );
			$params->addParam( "r2_mask_width_y", $r2_mask_width_y, "R2" );
			$params->addParam( "r3_mask_width_y", $r3_mask_width_y, "R3" );
			$params->addParam( "r4_mask_width_y", $r4_mask_width_y, "R4" );
			$params->addParam( "r5_mask_width_y", $r5_mask_width_y, "R5 │ Rectangular Mask Width (y)" );
			$params->addParam( "r6_mask_width_y", $r6_mask_width_y, "R6" );
			$params->addParam( "r7_mask_width_y", $r7_mask_width_y, "R7" );
			$params->addParam( "r8_mask_width_y", $r8_mask_width_y, "R8 │ Rectangular Mask Width (y)" );
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
			$params->addParam( "r6_highpass_diameter_x", $r6_hp_diam_x, "R6" );
			$params->addParam( "r7_highpass_diameter_x", $r7_hp_diam_x, "R7" );
			$params->addParam( "r8_highpass_diameter_x", $r8_hp_diam_x, "R8 │ Highpass Filter (x)" );
			$params->addParam( "r1_highpass_diameter_y", $r1_hp_diam_y, "R1" );
			$params->addParam( "r2_highpass_diameter_y", $r2_hp_diam_y, "R2" );
			$params->addParam( "r3_highpass_diameter_y", $r3_hp_diam_y, "R3" );
			$params->addParam( "r4_highpass_diameter_y", $r4_hp_diam_y, "R4" );
			$params->addParam( "r5_highpass_diameter_y", $r5_hp_diam_y, "R5 │ Highpass Filter (y)" );
			$params->addParam( "r6_highpass_diameter_y", $r6_hp_diam_y, "R6" );
			$params->addParam( "r7_highpass_diameter_y", $r7_hp_diam_y, "R7" );
			$params->addParam( "r8_highpass_diameter_y", $r8_hp_diam_y, "R8 │ Highpass Filter (y)" );
			$params->addParam( "r1_mask_apod_x", $r1_mask_apod_x, "R1" );
			$params->addParam( "r2_mask_apod_x", $r2_mask_apod_x, "R2" );
			$params->addParam( "r3_mask_apod_x", $r3_mask_apod_x, "R3" );
			$params->addParam( "r4_mask_apod_x", $r4_mask_apod_x, "R4" );
			$params->addParam( "r5_mask_apod_x", $r5_mask_apod_x, "R5 │ Apodization (x) for Masks" );
			$params->addParam( "r6_mask_apod_x", $r6_mask_apod_x, "R6" );
			$params->addParam( "r7_mask_apod_x", $r7_mask_apod_x, "R7" );
			$params->addParam( "r8_mask_apod_x", $r8_mask_apod_x, "R8 │ Apodization (x) for Masks" );
			$params->addParam( "r1_mask_apod_y", $r1_mask_apod_y, "R1" );
			$params->addParam( "r2_mask_apod_y", $r2_mask_apod_y, "R2" );
			$params->addParam( "r3_mask_apod_y", $r3_mask_apod_y, "R3" );
			$params->addParam( "r4_mask_apod_y", $r4_mask_apod_y, "R4" );
			$params->addParam( "r5_mask_apod_y", $r5_mask_apod_y, "R5 │ Apodization (y) for Masks" );
			$params->addParam( "r6_mask_apod_y", $r6_mask_apod_y, "R6" );
			$params->addParam( "r7_mask_apod_y", $r7_mask_apod_y, "R7" );
			$params->addParam( "r8_mask_apod_y", $r8_mask_apod_y, "R8 │ Apodization (y) for Masks" );
			$params->addParam( "r1_lowpass_apod_x", $r1_lp_apod_x, "R1" );
			$params->addParam( "r2_lowpass_apod_x", $r2_lp_apod_x, "R2" );
			$params->addParam( "r3_lowpass_apod_x", $r3_lp_apod_x, "R3" );
			$params->addParam( "r4_lowpass_apod_x", $r4_lp_apod_x, "R4" );
			$params->addParam( "r5_lowpass_apod_x", $r5_lp_apod_x, "R5 │ Lowpass Apodization Filter (x)" );
			$params->addParam( "r6_lowpass_apod_x", $r6_lp_apod_x, "R6" );
			$params->addParam( "r7_lowpass_apod_x", $r7_lp_apod_x, "R7" );
			$params->addParam( "r8_lowpass_apod_x", $r8_lp_apod_x, "R8 │ Lowpass Apodization Filter (x)" );
			$params->addParam( "r1_lowpass_apod_y", $r1_lp_apod_y, "R1" );
			$params->addParam( "r2_lowpass_apod_y", $r2_lp_apod_y, "R2" );
			$params->addParam( "r3_lowpass_apod_y", $r3_lp_apod_y, "R3" );
			$params->addParam( "r4_lowpass_apod_y", $r4_lp_apod_y, "R4" );
			$params->addParam( "r5_lowpass_apod_y", $r5_lp_apod_y, "R5 │ Lowpass Apodization Filter (y)" );
			$params->addParam( "r6_lowpass_apod_y", $r6_lp_apod_y, "R6" );
			$params->addParam( "r7_lowpass_apod_y", $r7_lp_apod_y, "R7" );
			$params->addParam( "r8_lowpass_apod_y", $r8_lp_apod_y, "R8 │ Lowpass Apodization Filter (y)" );
			$params->addParam( "r1_highpass_apod_x", $r1_hp_apod_x, "R1" );
			$params->addParam( "r2_highpass_apod_x", $r2_hp_apod_x, "R2" );
			$params->addParam( "r3_highpass_apod_x", $r3_hp_apod_x, "R3" );
			$params->addParam( "r4_highpass_apod_x", $r4_hp_apod_x, "R4" );
			$params->addParam( "r5_highpass_apod_x", $r5_hp_apod_x, "R5 │ Highpass Apodization Filter (x)" );
			$params->addParam( "r6_highpass_apod_x", $r6_hp_apod_x, "R6" );
			$params->addParam( "r7_highpass_apod_x", $r7_hp_apod_x, "R7" );
			$params->addParam( "r8_highpass_apod_x", $r8_hp_apod_x, "R8 │ Highpass Apodization Filter (x)" );
			$params->addParam( "r1_highpass_apod_y", $r1_hp_apod_y, "R1" );
			$params->addParam( "r2_highpass_apod_y", $r2_hp_apod_y, "R2" );
			$params->addParam( "r3_highpass_apod_y", $r3_hp_apod_y, "R3" );
			$params->addParam( "r4_highpass_apod_y", $r4_hp_apod_y, "R4" );
			$params->addParam( "r5_highpass_apod_y", $r5_hp_apod_y, "R5 │ Highpass Apodization Filter (y)" );
			$params->addParam( "r6_highpass_apod_y", $r6_hp_apod_y, "R6" );
			$params->addParam( "r7_highpass_apod_y", $r7_hp_apod_y, "R7" );
			$params->addParam( "r8_highpass_apod_y", $r8_hp_apod_y, "R8 │ Highpass Apodization Filter (y)" );
			$params->addParam( "r1_corr_mode", $r1_corr_mode, "R1" );
			$params->addParam( "r2_corr_mode", $r2_corr_mode, "R2" );
			$params->addParam( "r3_corr_mode", $r3_corr_mode, "R3" );
			$params->addParam( "r4_corr_mode", $r4_corr_mode, "R4" );
			$params->addParam( "r5_corr_mode", $r5_corr_mode, "R5 | Correlation Mode (xcf, mcf, pcf, dbl)" );
			$params->addParam( "r6_corr_mode", $r6_corr_mode, "R6" );
			$params->addParam( "r7_corr_mode", $r7_corr_mode, "R7" );
			$params->addParam( "r8_corr_mode", $r8_corr_mode, "R8 | Correlation Mode (xcf, mcf, pcf, dbl)" );
			$params->addParam( "r1_peak_search_radius_x", $r1_peak_search_radius_x, "R1" );
			$params->addParam( "r2_peak_search_radius_x", $r2_peak_search_radius_x, "R2" );
			$params->addParam( "r3_peak_search_radius_x", $r3_peak_search_radius_x, "R3" );
			$params->addParam( "r4_peak_search_radius_x", $r4_peak_search_radius_x, "R4" );
			$params->addParam( "r5_peak_search_radius_x", $r5_peak_search_radius_x, "R5 │ Peak Search Radius (x)" );
			$params->addParam( "r6_peak_search_radius_x", $r6_peak_search_radius_x, "R6" );
			$params->addParam( "r7_peak_search_radius_x", $r7_peak_search_radius_x, "R7" );
			$params->addParam( "r8_peak_search_radius_x", $r8_peak_search_radius_x, "R8 │ Peak Search Radius (x)" );
			$params->addParam( "r1_peak_search_radius_y", $r1_peak_search_radius_y, "R1" );
			$params->addParam( "r2_peak_search_radius_y", $r2_peak_search_radius_y, "R2" );
			$params->addParam( "r3_peak_search_radius_y", $r3_peak_search_radius_y, "R3" );
			$params->addParam( "r4_peak_search_radius_y", $r4_peak_search_radius_y, "R4" );
			$params->addParam( "r5_peak_search_radius_y", $r5_peak_search_radius_y, "R5 │ Peak Search Radius (y)" );
			$params->addParam( "r6_peak_search_radius_y", $r6_peak_search_radius_y, "R6" );
			$params->addParam( "r7_peak_search_radius_y", $r7_peak_search_radius_y, "R7" );
			$params->addParam( "r8_peak_search_radius_y", $r8_peak_search_radius_y, "R8 │ Peak Search Radius (y)" );
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
			$params->addParam( "recon_iter", $recon_iter, "Refinement Iteration used to generate Reconstruction" );
			$params->addParam( "recon_iter_presets", $recon_iter_presets, "Refinement Iteration used to generate Reconstruction" );
			$params->addParam( "recon_map_sampling", $recon_map_sampling, "Reconstruction Sampling" );
			$params->addParam( "recon_map_size_x", $recon_map_size_x, "Reconstructon Size (x)" );
			$params->addParam( "recon_map_size_y", $recon_map_size_y, "Reconstructon Size (y)" );
			$params->addParam( "recon_thickness", $recon_thickness, "Reconstructon Thickness" );
			$params->addParam( "recon_lowpass", $recon_lowpass, "Lowpass Filter" );
			$params->addParam( "recon_lp_diam_x", $recon_lp_diam_x, "(x)" );
			$params->addParam( "recon_lp_diam_y", $recon_lp_diam_y, "(y)" );
			$params->addParam( "negative", $negative, "<strong>–</strong> Angle Limit" );
			$params->addParam( "positive", $positive, "<strong>+</strong> Angle Limit" );
			$params->addParam( "r1_iters", $r1_iters, "R1" );
			$params->addParam( "r2_iters", $r2_iters, "R2" );
			$params->addParam( "r3_iters", $r3_iters, "R3" );
			$params->addParam( "r4_iters", $r4_iters, "R4" );
			$params->addParam( "r5_iters", $r5_iters, "R5 │ Alignment Iterations" );
			$params->addParam( "r6_iters", $r6_iters, "R6" );
			$params->addParam( "r7_iters", $r7_iters, "R7" );
			$params->addParam( "r8_iters", $r8_iters, "R8 │ Alignment Iterations" );
			$params->addParam( "auto_convergence", $auto_convergence, "Convergence Criteria" );
			$params->addParam( "auto_convergence_iters", $auto_convergence_iters, "Further Iterations After Convergence" );
			$params->addParam( "defocus_estimate", $defocus_estimate, "Defocus Estimate" );
			$params->addParam( "defocus_min", $defocus_min, "Minimum Defocus" );
			$params->addParam( "defocus_max", $defocus_max, "Maximum Defocus" );
			$params->addParam( "defocus_difference", $defocus_difference, "Defocus Difference" );
			$params->addParam( "amp_contrast_defocus", $amp_contrast_defocus, "Amplitude Contrast" );
			$params->addParam( "res_min", $res_min, "Lowest Resolution for Fitting" );
			$params->addParam( "res_max", $res_max, "Highest Resolution for Fitting" );
			$params->addParam( "center_all_images", $center_all_images, "Center All Images" );
			$params->addParam( "defocus_tlt", $defocus_tlt, "Iteration for Tilt-Azimuth" );
			$params->addParam( "defocus_tlt_iteration", $defocus_tlt_iteration, "Iteration Number" );
			$params->addParam( "ctf_correct", $ctf_correct, "Correct for CTF" );
			$params->addParam( "auto_ctf_correct", $auto_ctf_correct, "Correct for CTF" );
			$params->addParam( "amp_contrast_ctf", $amp_contrast_ctf, "Amplitude Contrast" );
			$params->addParam( "iWidth", $iWidth, "Interpolation Width" );
			$params->addParam( "DefocusTol", $DefocusTol, "Defocus Tolerance" );
			$params->addParam( "all_tilt_videos", $all_tilt_videos, "Create Tilt-Series Videos" );
			$params->addParam( "all_recon_videos", $all_recon_videos, "Create Reconstruction Videos" );
			$params->addParam( "map_sampling", $map_sampling, "Sampling for Depiction" );
			$params->addParam( "video_type", $video_type, "Video Type" );
			$params->addParam( "screening_start", $screening_start, "First Tilt-Series to Process" );
			$params->addParam( "template_location", $template_location, "Template Location" );
			$params->addParam( "estimated_particles", $estimated_particles, "Estimated Number of Particles in Each Tomogram" );
			$params->addParam( "distance_from_edges", $distance_from_edges, "Minimum Distance from Edges" );
			$params->addParam( "junk_tolerance", $junk_tolerance, "Junk Tolerance" );
		} else {
			$this->setBaseRunName( 'FIRST_GO_TO_ALIGN_TILT-SERIES' );
			$this->setTitle( 'Protomo Batch Refinement and Reconstruction Launcher' );
			$this->setHeading( 'Protomo Batch Refinement and Reconstruction' );
			$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Align_Tilt-Series" );
			$html .= "<br>
				<b><center>Proceed first to <a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2CoarseAlignForm'>Align Tilt-Series</a>, select a tilt-series, then go directly to Batch Align Tilt-Series</center></b>";
		}
	}
		
	// Generate a form for the parameters that are specific to this program (not Appion params)
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		global $sessionname;
		global $imageinfo;
		global $html;
		global $html2;
		global $html3;
		
		$fieldSize = 5;
		$fieldSize2 = 3;
		$fieldSize3 = 30;
		if (intval($imageinfo["dimx"] > 1)) {
			$html .= "
			<br />
			<H4>Batch Parameters ".docpop('batch_info', '(Info)')."</H4>
			<hr />";
			
			$html.= $params->insertTextField( "procs", $fieldSize );
			$html.= $params->insertTextField( "tiltseriesranges", $fieldSize );
			
			$html .= "<br />";
		}
		
		if ($_POST['firststep'] == 1)
		{
			$html .= "
		<H3>Preparation Parameters ".docpop('prep_info', '(Info)')."</H3>
		<hr />";
			$html.= '<br><select name="frame_aligned" style="width:66px">';
			$html.= '<option selected value="True">True</option>';
			$html.= '<option value="False">False</option>';
			$html.= '</select>'; $html.= docpop('protomo_frame_aligned', ' Use Frame Aligned Images').'<br>';
			$html.= $params->insertTextFieldInRow( "shift_limit", $fieldSize ).'│ ';
			$html.= $params->insertTextField( "angle_limit", $fieldSize );
			$html.= $params->insertTextField( "tilt_azimuth", $fieldSize );
			$html.= '<select name="change_refimg" style="width:66px">';
			$html.= '<option selected value="True">True</option>';
			$html.= '<option value="False">False</option>';
			$html.= '</select>'; $html.= docpop('protomo_change_refimg', ' Change Reference Image to Tilt Angle Closest to ');
			$html.= $params->insertTextField( "desired_ref_tilt_angle", $fieldSize );
			$html.= '<select name="center_all_images" style="width:66px">';
			$html.= '<option value="True">True</option>';
			$html.= '<option selected value="False">False</option>';
			$html.= '</select>'; $html.= docpop('protomo_center_all_images', ' Center All Images').'<br>';
			$html .= "
		<br />
		<H3>Dose Compensation Parameters ".docpop('dose_info', '(Info)')."</H3>
		<hr />";
			$html.= '<select name="dose_presets" style="width:87px">';
			$html.= '<option value="False">None</option>';
			$html.= '<option value="Light">Light</option>';
			$html.= '<option selected value="Moderate">Moderate</option>';
			$html.= '<option value="Heavy">Heavy</option>';
			$html.= '<option value="Custom">Custom</option>';
			$html.= '</select>'; $html.= docpop('dose_presets', ' Dose Compensation Type').'<br>';
			$html.= $params->insertTextFieldInRow( "dose_a", $fieldSize ).'│ ';
			$html.= $params->insertTextFieldInRow( "dose_b", $fieldSize ).'│ ';
			$html.= $params->insertTextField( "dose_c", $fieldSize );
			//$html.= '<br><select name="ctf_correct" style="width:66px">';
			//$html.= '<option value="True">True</option>';
			//$html.= '<option selected value="False">False</option>';
			//$html.= '</select>'; $html.= docpop('ctf_correct', ' Correct for CTF').'<br>';
			//$html.= $params->insertTextFieldInRow( "amp_contrast_ctf", $fieldSize ).'| ';
			//$html.= $params->insertTextFieldInRow( "iWidth", $fieldSize ).'| ';
			//$html.= $params->insertTextField( "DefocusTol", $fieldSize );
		}
		if ($_POST['firststep'] <= 2 and $_POST['laststep'] >= 2)
		{
			$html .= "
		<br />
		<H3>Coarse Alignment Parameters ".docpop('coarse_info', '(Info)')."</H3>
		<hr />";
			$html.= $params->insertTextField( "coarse_param_file", $fieldSize3 );
			$html.= '<select name="imod_coarse_align" style="width:66px">';
			$html.= '<option selected value="True">True</option>';
			$html.= '<option value="False">False</option>';
			$html.= '</select>'; $html.= docpop('protomo_imod_coarse_align', ' Coarse Align with Imod').'<br>';
		}
		
		if ($_POST['firststep'] <= 3 and $_POST['laststep'] >= 3)
		{
			$html .= "
		<br />
		<H3>Refinement Parameters ".docpop('refine_info', '(Info)')."</H3>
		<hr />";
			$html.=$html2;  //Preset Parameters
			$html.=$html3;  //Preset Parameters
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
			
		}
		
		if ($_POST['firststep'] <= 4 and $_POST['laststep'] == 4)
		{
			$html .= "
		<br />
		<H3>Reconstruction Parameters ".docpop('recon_info', '(Info)')."</H3>
		<hr />";
			$html.= $params->insertTextField( "recon_param_file", $fieldSize3 );
			$html.= $params->insertTextField( "link_recons", $fieldSize3 );
			$html.= '<select name="recon_iter_presets" style="width:66px">';
			$html.= '<option selected value="BestBin1or2">BestBin1or2</option>';
			$html.= '<option alue="Best">Best</option>';
			$html.= '<option value="Worst">Worst</option>';
			$html.= '<option value="Last">Last</option>';
			$html.= '<option value="Custom">Custom</option>';
			$html.= '</select> | '; $html.= $params->insertTextField( "recon_iter", $fieldSize );
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
			$html.= '<br><select name="dose_presets" style="width:66px">';
			$html.= '<option selected value="False">None</option>';
			$html.= '<option value="Light">Light</option>';
			$html.= '<option value="Moderate">Moderate</option>';
			$html.= '<option value="Heavy">Heavy</option>';
			$html.= '<option value="Custom">Custom</option>';
			$html.= '</select>'; $html.= docpop('dose_presets', ' Dose Compensation Type').'| ';
			$html.= $params->insertTextFieldInRow( "dose_a", $fieldSize ).'| ';
			$html.= $params->insertTextFieldInRow( "dose_b", $fieldSize ).'| ';
			$html.= $params->insertTextField( "dose_c", $fieldSize );
		}
		
		if ($_POST['firststep'] == 6 and $_POST['laststep'] == 6)
		{
			$html .= "
		<br />
		<H3>Screening Mode Parameters ".docpop('screening_info', '(Info)')."</H3>
		<hr />";
			$html.= $params->insertTextField( "screening_start", $fieldSize );
			$html.= $params->insertTextFieldInRow( "shift_limit", $fieldSize ).'│ ';
			$html.= $params->insertTextField( "angle_limit", $fieldSize );
			$html.= $params->insertTextField( "tilt_azimuth", $fieldSize );
			$html.= $params->insertTextField( "coarse_param_file", $fieldSize3 );
			
		}
		
		if ($_POST['firststep'] == 7 and $_POST['laststep'] == 7)
		{
			$html .= "
		<br />
		<H3>Defocus Estimation Parameters ".docpop('defocus_info2', '(Info)')."</H3>
		<hr />";
			$html.= $params->insertTextFieldInRow( "defocus_min", $fieldSize ).'│ ';
			$html.= $params->insertTextField( "defocus_max", $fieldSize );
			$html.= $params->insertTextField( "defocus_difference", $fieldSize );
			$html.= $params->insertTextField( "amp_contrast_defocus", $fieldSize );
			$html.= $params->insertTextFieldInRow( "res_max", $fieldSize ).'│ ';
			$html.= $params->insertTextField( "res_min", $fieldSize );
			$html.= '<select name="defocus_tlt" style="width:140px">';
			$html.= '<option value="best">Best</option>';
			$html.= '<option selected value="best_bin1or2">Best w/ bin=1or2</option>';
			$html.= '<option value="original">Original</option>';
			$html.= '<option value="iteration">Iteration</option>';
			$html.= '</select>'; $html.= docpop('defocus_tlt', ' Iteration to Extract Tilt-Azimuth').'| ';
			$html.= $params->insertTextField( "defocus_tlt_iteration", $fieldSize );
		}
		
		if ($_POST['firststep'] == 8 and $_POST['laststep'] == 8)
		{
			$html .= "
		<br />
		<H3>CTF Correction Parameters ".docpop('ctf_info', '(Info)')."</H3>
		<hr />";
			$html.= '<br><select name="frame_aligned" style="width:66px">';
			$html.= '<option selected value="True">True</option>';
			$html.= '<option value="False">False</option>';
			$html.= '</select>'; $html.= docpop('protomo_frame_aligned', ' Use Frame Aligned Images').'<br>';
			$html.= $params->insertTextField( "amp_contrast_ctf", $fieldSize );
			$html.= $params->insertTextField( "iWidth", $fieldSize );
			$html.= $params->insertTextField( "DefocusTol", $fieldSize );
			
		}
		
		if ($_POST['firststep'] == 9 and $_POST['laststep'] == 9)
		{
			$html .= "
		<br />
		<H3>Dose Compensation Parameters ".docpop('dose_info', '(Info)')."</H3>
		<hr />";
			$html.= '<br><select name="frame_aligned" style="width:66px">';
			$html.= '<option selected value="True">True</option>';
			$html.= '<option value="False">False</option>';
			$html.= '</select>'; $html.= docpop('protomo_frame_aligned', ' Use Frame Aligned Images').'<br>';
			$html.= '<select name="dose_presets" style="width:87px">';
			$html.= '<option value="Light">Light</option>';
			$html.= '<option selected value="Moderate">Moderate</option>';
			$html.= '<option value="Heavy">Heavy</option>';
			$html.= '<option value="Custom">Custom</option>';
			$html.= '</select>'; $html.= docpop('dose_presets', ' Dose Compensation Type').'<br>';
			$html.= $params->insertTextFieldInRow( "dose_a", $fieldSize ).'│ ';
			$html.= $params->insertTextFieldInRow( "dose_b", $fieldSize ).'│ ';
			$html.= $params->insertTextField( "dose_c", $fieldSize );
			
		}
		
		if ($_POST['firststep'] == 10 and $_POST['laststep'] == 10)
		{
			$html .= "
		<br />
		<H3>3D Template Picking Parameters ".docpop('3D_picking_info', '(Info)')."</H3>
		<hr />";
			$html.= '<br><select name="picking_gpu_or_cpu" style="width:66px">';
			$html.= '<option selected value="GPU">GPU</option>';
			$html.= '<option value="CPU">CPU</option>';
			$html.= '</select>'; $html.= docpop('protomo_picking_gpu_or_cpu', ' Use GPU or CPU').'<br>';
			$html.= $params->insertTextField( "template_location", $fieldSize3 );
			$html.= $params->insertTextField( "estimated_particles", $fieldSize );
			$html.= $params->insertTextField( "distance_from_edges", $fieldSize );
			$html.= $params->insertTextField( "junk_tolerance", $fieldSize );
		}
		
		if ($_POST['firststep'] == 12 and $_POST['laststep'] == 12)
		{
			$html .= "
		<br />
		<H3>Fully Automated Parameters ".docpop('auto_info', '(Info)')."</H3>
		<hr />";
			$html.=$html2.'<br><br>';  //Preset Parameters
			$html.= $params->insertTextField( "coarse_param_file", $fieldSize3 );
			$html.= $params->insertTextField( "refine_param_file", $fieldSize3 );
			$html.= $params->insertTextField( "recon_param_file", $fieldSize3 ).'<br>';
			$html.= '<br><select name="frame_aligned" style="width:66px">';
			$html.= '<option selected value="True">True</option>';
			$html.= '<option value="False">False</option>';
			$html.= '</select>'; $html.= docpop('protomo_frame_aligned', ' Use Frame Aligned Images').'<br>';
			$html.= $params->insertTextFieldInRow( "shift_limit", $fieldSize ).'│ ';
			$html.= $params->insertTextField( "angle_limit", $fieldSize );
			$html.= $params->insertTextField( "tilt_azimuth", $fieldSize );
			$html.= '<select name="auto_ctf_correct" style="width:66px">';
			$html.= '<option selected value="True">True</option>';
			$html.= '<option value="False">False</option>';
			$html.= '</select>'; $html.= docpop('auto_ctf_correct', ' Correct for CTF').'<br>';
			$html.= $params->insertTextFieldInRow( "amp_contrast_ctf", $fieldSize ).'| ';
			$html.= $params->insertTextFieldInRow( "iWidth", $fieldSize ).'| ';
			$html.= $params->insertTextField( "DefocusTol", $fieldSize ).'<br>';
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
			$html.= '<div id="hide_options" style="display:none">';
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
			$html.= '<option selected value="mcf">mcf</option>';
			$html.= '<option value="pcf">pcf</option>';
			$html.= '<option value="dbl">dbl</option>';
			$html.= '</select>'; $html.= docpop('protomo_r5_corr_mode', ' R5 | Correlation Mode').'<br>';
			$html.= "</div>";
			$html.= $params->insertTextField( "auto_convergence", $fieldSize2 );
			$html.= $params->insertTextField( "auto_convergence_iters", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_iters", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_iters", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_iters", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_sampling", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_sampling", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_sampling", $fieldSize2 );
			$html.= '<div id="hide_options" style="display:none">';
			$html.= $params->insertTextFieldInRow( "r6_kernel_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_kernel_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_kernel_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_kernel_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_kernel_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_kernel_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_region_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_region_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_region_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_region_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_region_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_region_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_mask_width_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_mask_width_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_mask_width_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_mask_width_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_mask_width_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_mask_width_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_lowpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_lowpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_lowpass_diameter_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_lowpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_lowpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_lowpass_diameter_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_highpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_highpass_diameter_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_highpass_diameter_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_highpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_highpass_diameter_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_highpass_diameter_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_mask_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_mask_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_mask_apod_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_mask_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_mask_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_mask_apod_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_lowpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_lowpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_lowpass_apod_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_lowpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_lowpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_lowpass_apod_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_highpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_highpass_apod_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_highpass_apod_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_highpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_highpass_apod_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_highpass_apod_y", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_peak_search_radius_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_peak_search_radius_x", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_peak_search_radius_x", $fieldSize2 );
			$html.= $params->insertTextFieldInRow( "r6_peak_search_radius_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextFieldInRow( "r7_peak_search_radius_y", $fieldSize2 ).'│ ';
			$html.= $params->insertTextField( "r8_peak_search_radius_y", $fieldSize2 );
			$html.= '<select name="r6_corr_mode" style="width:51px">';
			$html.= '<option value="xcf">xcf</option>';
			$html.= '<option selected value="mcf">mcf</option>';
			$html.= '<option value="pcf">pcf</option>';
			$html.= '<option value="dbl">dbl</option>';
			$html.= '</select>'; $html.= docpop('protomo_r6_corr_mode', ' R6').'│ ';
			$html.= '<select name="r7_corr_mode" style="width:51px">';
			$html.= '<option value="xcf">xcf</option>';
			$html.= '<option selected value="mcf">mcf</option>';
			$html.= '<option value="pcf">pcf</option>';
			$html.= '<option value="dbl">dbl</option>';
			$html.= '</select>'; $html.= docpop('protomo_r7_corr_mode', ' R7').'│ ';
			$html.= '<select name="r8_corr_mode" style="width:51px">';
			$html.= '<option value="xcf">xcf</option>';
			$html.= '<option selected value="mcf">mcf</option>';
			$html.= '<option value="pcf">pcf</option>';
			$html.= '<option value="dbl">dbl</option>';
			$html.= '</select>'; $html.= docpop('protomo_r8_corr_mode', ' R8 | Correlation Mode').'<br>';
			$html.= "</div><br>";
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
			$html.= '<select name="dose_presets" style="width:66px">';
			$html.= '<option value="False">None</option>';
			$html.= '<option value="Light">Light</option>';
			$html.= '<option selected value="Moderate">Moderate</option>';
			$html.= '<option value="Heavy">Heavy</option>';
			$html.= '<option value="Custom">Custom</option>';
			$html.= '</select>'; $html.= docpop('dose_presets', ' Dose Compensation Type').'| ';
			$html.= $params->insertTextFieldInRow( "dose_a", $fieldSize ).'| ';
			$html.= $params->insertTextFieldInRow( "dose_b", $fieldSize ).'| ';
			$html.= $params->insertTextField( "dose_c", $fieldSize );
			$html.= $params->insertTextField( "link_recons", $fieldSize3 );
			
		}
		
		
		if ($_POST['firststep'] == 14 and $_POST['laststep'] == 14)
		{
			$html .= "
		<br />
		<H3>Tilt-Series Exporting Parameters ".docpop('exporting_info', '(Info)')."</H3>
		<hr />";
			$html.= '<br><select name="frame_aligned" style="width:66px">';
			$html.= '<option selected value="True">True</option>';
			$html.= '<option value="False">False</option>';
			$html.= '</select>'; $html.= docpop('protomo_frame_aligned', ' Use Frame Aligned Images').'<br>';
		}		
		
		if ($_POST['firststep'] == 2 or $_POST['firststep'] == 3 or $_POST['firststep'] == 6  or $_POST['firststep'] == 12 or $_POST['laststep'] == 2 or $_POST['laststep'] == 3 or $_POST['laststep'] == 6 or $_POST['laststep'] == 12 or (($_POST['firststep'] == 1 or $_POST['firststep'] == 2 or $_POST['firststep'] == 3) and $_POST['laststep'] == 4))
		{
			$html .= "
		<br />
		<H4>Depiction Parameters ".docpop('depictionparam_info', '(Info)')."</H4>
		<hr />";
			$html.= '<select name="all_tilt_videos" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_create_tiltvids', ' Create Tilt-Series Videos').'<br>';
			$html.= '<select name="all_recon_videos" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_create_reconstruction2', ' Create Reconstruction Videos').'<br>';
			$html.= '<select name="video_type" style="width:66px">';
			$html.= '<option value="gif">Gif</option>';
			$html.= '<option selected value="html5vid">HTML5</option>';
			$html.= '</select>'; $html.= docpop('protomo_video_type', ' Video Type').'<br>';
			$html.= $params->insertTextField( "map_sampling", $fieldSize );
		}
		
		if ($_POST['firststep'] == 1 and $_POST['laststep'] == 1)
		{
			$html .= "
		<br />
		<H4>Depiction Parameters ".docpop('depictionparam_info', '(Info)')."</H4>
		<hr />";
			$html.= '<select name="all_tilt_videos" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_create_tiltvids', ' Create Tilt-Series Videos').'<br>';
			$html.= '<select name="video_type" style="width:66px">';
			$html.= '<option value="gif">Gif</option>';
			$html.= '<option selected value="html5vid">HTML5</option>';
			$html.= '</select>'; $html.= docpop('protomo_video_type', ' Video Type').'<br>';
			$html.= $params->insertTextField( "map_sampling", $fieldSize );
		}
		
		// Only display link to next step in tomo processing if on completed Command page
		if (empty($_POST['procs']) AND empty($_POST['tiltseriesranges']) AND (intval($imageinfo["dimx"] > 1)))
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
		if ($_POST['firststep'] == 1 or $_POST['firststep'] == 2 or $_POST['firststep'] == 3 or $_POST['firststep'] == 4 or $_POST['firststep'] == 6 or $_POST['firststep'] == 7 or $_POST['firststep'] == 8) {$command.="--automation=False ";}
		if ($_POST['firststep'] == 1 and $_POST['laststep'] == 1) {$command.="--prep_files=True --coarse_align=False --refine=False --reconstruct=False ";}
		if ($_POST['firststep'] == 1 and $_POST['laststep'] == 2) {$command.="--prep_files=True --coarse_align=True --refine=False --reconstruct=False ";}
		if ($_POST['firststep'] == 1 and $_POST['laststep'] == 3) {$command.="--prep_files=True --coarse_align=True --refine=True --reconstruct=False ";}
		if ($_POST['firststep'] == 1 and $_POST['laststep'] == 4) {$command.="--prep_files=True --coarse_align=True --refine=True --reconstruct=True ";}
		if ($_POST['firststep'] == 2 and $_POST['laststep'] == 2) {$command.="--prep_files=False --coarse_align=True --refine=False --reconstruct=False ";}
		if ($_POST['firststep'] == 2 and $_POST['laststep'] == 3) {$command.="--prep_files=False --coarse_align=True --refine=True --reconstruct=False ";}
		if ($_POST['firststep'] == 2 and $_POST['laststep'] == 4) {$command.="--prep_files=False --coarse_align=True --refine=True --reconstruct=True ";}
		if ($_POST['firststep'] == 3 and $_POST['laststep'] == 3) {$command.="--prep_files=False --coarse_align=False --refine=True --reconstruct=False ";}
		if ($_POST['firststep'] == 3 and $_POST['laststep'] == 4) {$command.="--prep_files=False --coarse_align=False --refine=True --reconstruct=True ";}
		if ($_POST['firststep'] == 4 and $_POST['laststep'] == 4) {$command.="--prep_files=False --coarse_align=False --refine=False --reconstruct=True ";}
		if ($_POST['firststep'] == 7) {$command.="--prep_files=False --coarse_align=False --refine=False --reconstruct=False --defocus_estimate=True ";}
		if ($_POST['firststep'] == 8) {$command.="--prep_files=False --coarse_align=False --refine=False --reconstruct=False --ctf_correct=True ";}
		if ($_POST['firststep'] == 9) {$command.="--prep_files=False --coarse_align=False --refine=False --reconstruct=False ";}
		if ($_POST['firststep'] == 10) {$command.="--prep_files=False --coarse_align=False --refine=False --reconstruct=False --particle_picking=True ";}
		if ($_POST['firststep'] == 12) {$command.="--automation=True --auto_prep=True --auto_coarse_align=True --auto_refine=True --auto_recon=True --recon_iter_presets=BestBin1or2 --sampling=8 ";}
		if ($_POST['firststep'] == 14) {$command.="--exporting=True ";}
		
		$image_file_type=$_SESSION['image_file_type'];
		$pixelsize=$_POST['pixelsize'];
		$dimx=$_SESSION['dimx'];
		$dimy=$_SESSION['dimy'];
		$command.="--image_file_type=$image_file_type ";
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
		if (isset($_POST['procs']) AND (isset($_POST['refine_param_file']) OR isset($_POST['coarse_param_file'])) AND isset($_POST['tiltseriesranges']))
		{
			//$trimmed_runname=preg_replace("/\d+$/","",$_POST['runname']);
			$folders='tiltseries####';
			$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2BatchSummary'><b><center>[Click here to View Batch Alignment Results after protomo2batch.py has been run] <font size='5'>→</font></center></b></a>";
			$html .= "<br></br>
			<b><center>[Execution of this protomo2batch.py command will create folders '".$folders."'<br> in the outdir directory (runname doesn't actually do anything in batch mode), overwriting folders & files when necessary]</center></b>";
			$html .= "<br>
			<b><center>[It is recommended that you run protomo2batch.py either on a dedicated machine or using screen/tmux/nohup]</center></b>";
			$html .= "
			<b><center>[protomo2batch.py may require long CPU time limits depending on the number of tilt-series and iterations being processed]</center></b>";
		}
		
		return $html;
	}
}
?>
