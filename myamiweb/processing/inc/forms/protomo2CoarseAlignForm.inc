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

class Protomo2CoarseAlignForm extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML, $region_x='512', $region_y='512', $sampling='8', $map_sampling='8', $thickness='1000', $pixelsize='', $lp_diam_x='20', $lp_diam_y='20', $lp_apod_x='50',
	$lp_apod_y='50', $hp_diam_x='500', $hp_diam_y='500', $hp_apod_x='150', $hp_apod_y='150', $corr_mode='mcf', $raw_path='', $iters='', $param='', $binning='true',
	$preprocessing='true', $select_images='', $exclude_images='', $border='100', $clip_low='3.5', $clip_high='3.5', $thr_low='', $thr_high='', $gradient='true', $iter_gradient='false', $filter='median',
	$kernel_x='', $kernel_y='', $grow='0', $window_area='0.95', $mask_apod_x='', $mask_apod_y='', $mask_width_x='', $mask_width_y='', $dimx='', $dimy='',
	$correlation_size_x='192', $correlation_size_y='192', $peak_search_radius_x='', $peak_search_radius_y='', $logging='true', $loglevel='2', $map_size_x='512', $map_size_y='512', $map_size_z='200', $filename_prefix='', $image_file_type='', $cachedir='cache',
	$protomo_outdir='out', $gui_coarse_align='', $grid_limit='2.0', $grid_step='0.1', $retry='10', $retry_shrink='0.9', $create_reconstruction='true', $keep_recons='false', $region_x='512', $video_type='',
	$link='', $shift_limit='30' , $angle_limit='40' )
	{
		parent::__construct($expId, $extraHTML);
		print "_POST:" . "<br>";
		var_dump($_POST);
		print "_GET:" . "<br>";
		var_dump($_GET);
		print "_SESSION:" . "<br>";
		var_dump($_SESSION);
		
		global $imageinfo;
		
		global $html; //I can only get the selector form to pass variables properly by defining it globally in the constructor.
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
		
		// Select tilt series
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
		$html.=  docpop('protomo_tiltseries', ' Tilt Series');
		if (count($tiltseriesinfos) && $tiltseriesId) {
			$html.=  "
			<br/><br/><b>First Image in the Tilt Series:</b><br/>"
				.$tiltseriesinfos[0]['filename'].".".pathinfo($imageinfo['filename'], PATHINFO_EXTENSION);
		} else {
			if ($tiltseriesId)
				$html.=  "<br/><b>Bad Tilt Series! Do not use.</b><br/>";
		}
		// Hide secondary tilt series until dual tilt is processable
		if (false) {
			$html.=  "</td><td Valign='TOP'>\n";
			$html.=  $seriesselector_array2[0];
			$html.=  docpop('tiltseriestwo', 'Secondary Tilt Series');
		}
		if (count($tiltseriesinfos2) && $tiltseriesId2) {
			if ($tiltseriesId2==$tiltseriesId){
				$html.=  "<br/><b>2nd tilt series must be different.</b><br/>";
			} else {
				$html.=  "
					<br/><b>First Image in the Tilt Series:</b><br/>"
					.$tiltseriesinfos2[0]['filename'].".".pathinfo($imageinfo['filename'], PATHINFO_EXTENSION);
			}
		} else {
			if ($tiltseriesId2)
				$html.=  "<br/><b>Bad Tilt Series! Do not use.</b><br/>";
		}
		$_SESSION['imageinfo'] = $imageinfo;
		$_SESSION['tiltseries'] = $tiltseriesinfos[0]['number'];
		
		$region_x = intval($imageinfo['dimx']*0.6);
		$region_y = intval($imageinfo['dimy']*0.6);
		$map_size_x = intval($imageinfo['dimx']/$map_sampling);
		$map_size_y = intval($imageinfo['dimy']/$map_sampling);
		$kernel_x = intval($region_x/$sampling);
		$kernel_y = intval($region_y/$sampling);
		$mask_width_x = intval($region_x/$sampling);
		$mask_width_y = intval($region_y/$sampling);
		$mask_apod_x = intval($region_x/$sampling);
		$mask_apod_y = intval($region_y/$sampling);
		$image_file_type = pathinfo($imageinfo['filename'], PATHINFO_EXTENSION);
		$_SESSION['image_file_type'] = $image_file_type;
		$_SESSION['dimx'] = $imageinfo['dimx'];
		$_SESSION['dimy'] = $imageinfo['dimy'];
		$_POST['pixelsize'] = $imageinfo['pixelsize']*pow(10,10);
		$_POST['peak_search_radius_x'] = $imageinfo['dimx']/2;
		$_POST['peak_search_radius_y'] = $imageinfo['dimy']/2;
		
		//foreach(array_keys($imageinfo) as $paramName)
		//	echo $paramName . "<br>";
			//echo $imageinfo["$paramName"] . "<br>";
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('protomo');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'protomorun' );
		$this->setTitle( 'Protomo Coarse Alignment Launcher' );
		$this->setHeading( 'Protomo Coarse Alignment' );
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
		$params->addParam( "region_x", $region_x, "Window Size (x) (<strong>Required Parameter</strong>)" );
		$params->addParam( "region_y", $region_y, "Window Size (y) (<strong>Required Parameter</strong>)" );
		$params->addParam( "sampling", $sampling, "Sampling" );
		$params->addParam( "map_sampling", $map_sampling, "Sampling for Depiction" );
		$params->addParam( "thickness", $thickness, "Thickness, in angstroms (<strong>Required Parameter</strong>)" );
		$params->addParam( "lowpass_diameter_x", $lp_diam_x, "Lowpass Filter (x)" );
		$params->addParam( "lowpass_diameter_y", $lp_diam_y, "Lowpass Filter (y)" );
		$params->addParam( "lowpass_apod_x", $lp_apod_x, "Lowpass Apodization Filter (x)" );
		$params->addParam( "lowpass_apod_y", $lp_apod_y, "Lowpass Apodization Filter (y)" );
		$params->addParam( "highpass_diameter_x", $hp_diam_x, "Highpass Filter (x)" );
		$params->addParam( "highpass_diameter_y", $hp_diam_y, "Highpass Filter (y)" );
		$params->addParam( "highpass_apod_x", $hp_apod_x, "Highpass Apodization Filter (x)" );
		$params->addParam( "highpass_apod_y", $hp_apod_y, "Highpass Apodization Filter (y)" );
		$params->addParam( "corr_mode", $corr_mode, "Correlation Mode (xcf, mcf, pcf, dbl)" );
		$params->addParam( "raw_path", $raw_path, "Raw Image Path" );
		$params->addParam( "iters", $iters, "Alignment Iterations" );
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
		//$params->addParam( "do_estimation", $do_estimation, "Estimate Geometric Parameters" );
		//$params->addParam( "norotations", "$norotations", "No In-plane Rotations" );
		//$params->addParam( "max_correction", $max_correction, "Correction Cutoff" );
		$params->addParam( "correlation_size_x", $correlation_size_x, "Size (x) of Cross-Correlation Image" );
		$params->addParam( "correlation_size_y", $correlation_size_y, "Size (y) of Cross-Correlation Image" );
		$params->addParam( "peak_search_radius_x", $peak_search_radius_x, "Peak Search Radius (x)" );
		$params->addParam( "peak_search_radius_y", $peak_search_radius_y, "Peak Search Radius (y)" );
		//$params->addParam( "orientation", $orientation, "Include Orientation Angles in Refinement" );
		//$params->addParam( "azimuth", $azimuth, "Include Tilt Azimuth in Refinement" );
		//$params->addParam( "elevation", $elevation, "Include Tilt Axis Elevation in Refinement" );
		//$params->addParam( "rotation", $rotation, "Include In-plane Rotations in Refinement" );
		//$params->addParam( "scale", $scale, "Include Scale Factors (Magnification) in Refinement" );
		$params->addParam( "logging", $logging, "Logging" );
		$params->addParam( "loglevel", $loglevel, "Logging Level" );
		$params->addParam( "filename_prefix", $filename_prefix, "Filename Prefix" );
		$params->addParam( "image_file_type", $image_file_type, "Image Extension" );
		$params->addParam( "cachedir", $cachedir, "Cache Directory" );
		$params->addParam( "protomo_outdir", $protomo_outdir, "Output Directory" );
		//$params->addParam( "gui_coarse_align", $gui_coarse_align, "Coarse Alignment equivalent to 'Align All' in tomoaign-gui (<strong>Over-rides other options</strong>) (NOT IMPLEMENTED YET!!)" );
		$params->addParam( "gridsearch_limit", $grid_limit, "Gridseach +-Angle Limit (<strong>Required Parameter</strong>)" );
		$params->addParam( "gridsearch_step", $grid_step, "Gridseach Angle Step Size (<strong>Required Parameter</strong>)" );
		$params->addParam( "retry", $retry, "Coarse Alignment Retries" );
		$params->addParam( "retry_shrink", $retry_shrink, "Window Size Fraction to Shrink Each Retry Attempt" );
		$params->addParam( "create_reconstruction", $create_reconstruction, "Create a Reconstruction Video" );
		$params->addParam( "keep_recons", $keep_recons, "Keep Intermediate Reconstruction" );
		$params->addParam( "map_size_x", $map_size_x, "Reconstructon Size (x)" );
		$params->addParam( "map_size_y", $map_size_y, "Reconstructon Size (y)" );
		$params->addParam( "map_size_z", $map_size_z, "Reconstructon Size (z)" );
		$params->addParam( "video_type", $video_type, "Video Type" );
		$params->addParam( "link", $link, "Link or Copy Raw Images?" );
		$params->addParam( "shift_limit", $shift_limit, "Shift Limit" );
		$params->addParam( "angle_limit", $angle_limit, "Angle Limit" );

		
		// Validations
		$params->addValidation( "region_x", "req" );
		$params->addValidation( "region_x", "num" );
		$params->addValidation( "region_y", "req" );
		$params->addValidation( "region_y", "num" );
		$params->addValidation( "thickness", "req" );
		$params->addValidation( "thickness", "num" );
		
	}
		
	// Generate a form for the parameters that are specific to this program (not Appion params)
	public function generateAdditionalFormLeft()
	{
		$filename='/lustre/cryo/lustre/appiondata/15apr12b/protomo_alignments/protomorun2/series000309.corr';
		$lines = file($filename, FILE_IGNORE_NEW_LINES);
		print $filename;
		print $lines;
		
		if ($_SESSION['erase_coarse']==1)
		{
			$html .= "<br></br>
			<b><center>Remove the previous Coarse Alignment by running this command:</center></b>";
			$html .= "<br></br>
			<center><code>rm -r ".$_SESSION['outdir'].$_SESSION['runname']."</code></center>";
			$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2CoarseAlignForm'><b><center>Click here or Refresh this page to continue.</center></b></a>";	
			$_SESSION['erase_coarse'] = 0;
		}
		elseif (empty($_POST['tiltseriesId']) AND $_SESSION['erase_coarse']!=1)
		{
			global $html;
			$html .= "<br></br>
			<b><center>[Choose a Tilt Series to align to proceed]</center></b>";
		}
		else
		{
			$fieldSize = 5;
			//$imageinfo=$_SESSION['imageinfo'];
			
			$this->updateFormParams();
			$params = $this->getFormParams();
			
			global $html;
			$html .= "
		    <br><br />
		    <H4>General Parameters ".docpop('genparam_info', '(Info)')."</H4>
		    <hr />";
			
			$html.= $params->insertTextField( "raw_path", $fieldSize );
			//$html.= $params->insertTextField( "param_file", $fieldSize );
			//$html.= $params->insertTextField( "filename_prefix", $fieldSize );
			//$html.= $params->insertTextField( "image_file_type", $fieldSize );
			//$html.= $params->insertTextField( "cachedir", $fieldSize );
			//$html.= $params->insertTextField( "protomo_outdir", $fieldSize );
			//$html.= $params->insertTextField( "preprocessing", $fieldSize );
			$html.= '<select name="link" style="width:66px">';
			$html.= '<option selected value="True">Link</option>';
			$html.= '<option value="False">Copy</option>';
			$html.= '</select>'; $html.= docpop('protomo_link', ' Link or Copy Raw Images?').'<br>';
			$html.= '<select name="preprocessing" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_preprocessing', ' Raw Image Preprocessing').'<br>';
			//$html.= $params->insertTextField( "binning", $fieldSize );
			$html.= '<select name="binning" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_binning', ' Raw Image Binning').'<br>';
			$html.= $params->insertTextField( "sampling", $fieldSize );
			$html.= $params->insertTextField( "select_images", $fieldSize );
			$html.= $params->insertTextField( "exclude_images", $fieldSize );
			$html.= $params->insertTextFieldInRow( "shift_limit", $fieldSize ).'│ ';
			$html.= $params->insertTextField( "angle_limit", $fieldSize );
			//$html.= $params->insertTextField( "logging", $fieldSize );
			$html.= '<select name="logging" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_logging', ' Logging').'<br>';
			$html.= $params->insertTextField( "loglevel", $fieldSize );
			
			$html .= "
		    <br />
		    <H4>Preprocessing Parameters ".docpop('preprocparam_info', '(Info)')."</H4>
		    <hr />";
		    
			//$html.= $params->insertTextField( "gradient", $fieldSize );
			$html.= '<select name="gradient" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_gradient', ' Linear Gradient Subtraction').'<br>';
			//$html.= $params->insertTextField( "iter_gradient", $fieldSize );
			$html.= '<select name="iter_gradient" style="width:66px">';
			$html.= '<option value="true">true</option>';
			$html.= '<option selected value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_iter_gradient', ' Iterate Gradient Subtraction Once').'<br>';
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
		    
			$html.= $params->insertTextField( "mask_width_x", $fieldSize );
			$html.= $params->insertTextField( "mask_width_y", $fieldSize );
			$html.= $params->insertTextField( "lowpass_diameter_x", $fieldSize );
			$html.= $params->insertTextField( "lowpass_diameter_y", $fieldSize );
			$html.= $params->insertTextField( "highpass_diameter_x", $fieldSize );
			$html.= $params->insertTextField( "highpass_diameter_y", $fieldSize );
			$html.= $params->insertTextField( "mask_apod_x", $fieldSize );
			$html.= $params->insertTextField( "mask_apod_y", $fieldSize );
			$html.= $params->insertTextField( "lowpass_apod_x", $fieldSize );
			$html.= $params->insertTextField( "lowpass_apod_y", $fieldSize );
			$html.= $params->insertTextField( "highpass_apod_x", $fieldSize );
			$html.= $params->insertTextField( "highpass_apod_y", $fieldSize );
			
			$html .= "
		    <br />
		    <H4>Coarse Gridsearch Parameters ".docpop('gridsearchparam_info', '(Info)')."</H4>
		    <hr />";
		    
			//$html.= $params->insertCheckboxField( "gui_coarse_align" );
			$html.= $params->insertTextField( "gridsearch_limit", $fieldSize );
			$html.= $params->insertTextField( "gridsearch_step", $fieldSize );
			$html.= $params->insertTextField( "retry", $fieldSize );
			$html.= $params->insertTextField( "retry_shrink", $fieldSize );
			
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
			$html.= $params->insertTextField( "peak_search_radius_x", $fieldSize );
			$html.= $params->insertTextField( "peak_search_radius_y", $fieldSize );
			
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
			$html.= '</select>'; $html.= docpop('protomo_create_reconstruction', ' Create a Reconstruction Video').'<br>';
			$html.= '<select name="video_type" style="width:66px">';
			$html.= '<option value="gif">Gif</option>';
			$html.= '<option selected value="html5vid">HTML5</option>';
			$html.= '</select>'; $html.= docpop('protomo_video_type', ' Video Type').'<br>';
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
			if ((empty($_POST['region_x']) OR empty($_POST['region_y']) OR empty($_POST['thickness']) OR empty($_POST['grid_limit']) OR empty($_POST['grid_step'])) AND !isset($_POST['process']))
			{
				$html .= "<br></br>
				<b><center>[Enter the Required Parameters and click 'Just Show Command' to proceed]</center><br></b>";
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
		$pixelsize=$_POST['pixelsize'];
		$dimx=$_SESSION['dimx'];
		$dimy=$_SESSION['dimy'];
		$image_file_type=$_SESSION['image_file_type'];
		$command.="--session=$sessionname ";
		$command.="--tiltseries=$tiltseries ";
		$command.="--pixelsize=$pixelsize ";
		$command.="--dimx=$dimx ";
		$command.="--dimy=$dimy ";
		$command.="--image_file_type=$image_file_type ";
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
