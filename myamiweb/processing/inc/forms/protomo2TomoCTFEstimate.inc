<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
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

if (isset($_GET['outdir'])) {$_POST['outdir'] = $_GET['outdir'];$_SESSION['outdir'] = $_GET['outdir'];}
if (isset($_GET['runname'])) {$_POST['runname'] = $_GET['runname'];$_SESSION['runname'] = $_GET['runname'];}

class Protomo2TomoCTFEstimate extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML, $pixelsize='', $ctf_correct='',	$frame_aligned='', $defocus_min='',
	$defocus_max='', $defocus_difference='0.2', $defocus_ang_negative='', $defocus_ang_positive='',
	$amp_contrast_defocus='0.07', $res_min='10000', $res_max='10', $defocus_tlt='', $defocus_tlt_iteration='')
	{
		parent::__construct($expId, $extraHTML);
		//print "_POST:" . "<br>";
		//var_dump($_POST);
		//print "_GET:" . "<br>";
		//var_dump($_GET);
		//print "_SESSION:" . "<br>";
		//var_dump($_SESSION);
		
		global $imageinfo;
		global $html;
		$html .= "
			<center>(TomoCTF Defocus Estimation only operates on tilt-series directories that have already been prepared)</center><br>";
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
		
		$defocus_min = -round($imageinfo['defocus']*pow(10,6)*0.8,2);
		$defocus_max = -round($imageinfo['defocus']*pow(10,6)*1.2,2);
		$res_max = round($imageinfo['pixelsize']*4*pow(10,10),1);
		$_SESSION['pixelsize'] = $imageinfo['pixelsize']*pow(10,10);
		$_SESSION['tiltseries'] = $tiltseriesinfos[0]['number'];

		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('appion-protomo', 'tomoctf');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		if ($_POST['process'] != "Just Show Command"){
			if (isset($tiltseriesinfos[0]['number']) and (($_POST['runname'] == 'FIRST_SELECT_A_TILT-SERIES_BELOW') or ($tiltseriesinfos[0]['number'] != $_SESSION['internal_num']))){
				$num = sprintf('%04d', $tiltseriesinfos[0]['number']);
				$_SESSION['internal_num'] = $tiltseriesinfos[0]['number'];
				if ((isset($_SESSION['runname'])) and ($_POST['runname'] != 'FIRST_SELECT_A_TILT-SERIES_BELOW')){
					$_POST['runname'] = $_SESSION['runname'];
				}else{
					$_POST['runname'] = 'tiltseries'.$num;
				}
			}elseif (isset($tiltseriesinfos[0]['number']) and ($_POST['runname'] != 'FIRST_SELECT_A_TILT-SERIES_BELOW')){
				//nothing
			}else{
				$_POST['runname'] = 'FIRST_SELECT_A_TILT-SERIES_BELOW';
				if (isset($_GET['runname'])) {$_POST['runname'] = $_GET['runname'];}
			}
		}
		#$this->setBaseRunName( $protomorunname );
		$this->setTitle( 'TomoCTF Defocus Estimation Launcher' );
		$this->setHeading( 'TomoCTF Defocus Estimation' );
		$this->setExeFile( 'protomo2tomoctfestimate.py' );
		$this->setGuideURL( "https://github.com/nysbc/appion-protomo#example" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( True ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "protomo" );
		
		$params->addParam( "tiltseries", $tiltseries, "Tilt-Series #" );
		$params->addParam( "frame_aligned", $frame_aligned, "Use Frame Aligned Images" );
		$params->addParam( "parallel", $parallel, "Parallelize Non-Protomo Processes" );
		$params->addParam( "defocus_min", $defocus_min, "Minimum Defocus" );
		$params->addParam( "defocus_max", $defocus_max, "Maximum Defocus" );
		$params->addParam( "defocus_difference", $defocus_difference, "Defocus Difference" );
		$params->addParam( "defocus_ang_negative", $defocus_ang_negative, "<strong>–</strong> Angle Limit for Estimation" );
		$params->addParam( "defocus_ang_positive", $defocus_ang_positive, "<strong>+</strong> Angle Limit for Estimation" );
		$params->addParam( "amp_contrast_defocus", $amp_contrast_defocus, "Amplitude Contrast" );
		$params->addParam( "res_min", $res_min, "Lowest Resolution for Fitting" );
		$params->addParam( "res_max", $res_max, "Highest Resolution for Fitting" );
		$params->addParam( "defocus_tlt", $defocus_tlt, "Iteration for Tilt-Azimuth" );
		$params->addParam( "defocus_tlt_iteration", $defocus_tlt_iteration, "Iteration Number" );

		// Validations
		$params->addValidation( "defocus_min", "req" );
		$params->addValidation( "defocus_max", "req" );
	}
		
	// Generate a form for the parameters that are specific to this program (not Appion params)
	public function generateAdditionalFormLeft()
	{
		if (empty($_POST['tiltseriesId']) AND $_SESSION['erase_coarse'] != 1 AND $_SESSION['manual'] != 1)
		{
			global $html;
			$html .= "<br></br>
			<b><center>[Choose a Tilt-Series to proceed]</center></b><br>";
		}else{
			$this->updateFormParams();
			$params = $this->getFormParams();
			
			global $html;
			$fieldSize = 5;
			
			if (!empty($_POST['tiltseriesId'])) {
				$html .= "
				<br /><br>
				<H4>Defocus Estimation Parameters ".docpop('defocus_info', '(Info)')."</H4>
				<hr />";
				$html.= '<select name="frame_aligned" style="width:66px">';
				$html.= '<option selected value="True">True</option>';
				$html.= '<option value="False">False</option>';
				$html.= '</select>'; $html.= docpop('protomo_frame_aligned', ' Use Frame Aligned Images').'<br>';
				$html.= $params->insertTextFieldInRow( "defocus_min", $fieldSize ).'│ ';
				$html.= $params->insertTextField( "defocus_max", $fieldSize );
				$html.= $params->insertTextField( "defocus_difference", $fieldSize );
				$html.= $params->insertTextField( "amp_contrast_defocus", $fieldSize );
				$html.= $params->insertTextFieldInRow( "res_max", $fieldSize ).'│ ';
				$html.= $params->insertTextField( "res_min", $fieldSize );
				$html.= $params->insertTextFieldInRow( "defocus_ang_negative", $fieldSize ).'│ ';
				$html.= $params->insertTextField( "defocus_ang_positive", $fieldSize );
				$html.= '<select name="defocus_tlt" style="width:140px">';
				$html.= '<option value="best">Best</option>';
				$html.= '<option selected value="best_bin1or2">Best w/ bin=1or2</option>';
				$html.= '<option value="original">Original</option>';
				$html.= '<option value="iteration">Iteration</option>';
				$html.= '</select>'; $html.= docpop('defocus_tlt', ' Iteration to Extract Tilt-Azimuth').'| ';
				$html.= $params->insertTextField( "defocus_tlt_iteration", $fieldSize ).'<br>';
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
		$command.="--sessionname=$sessionname ";
		$command.="--tiltseries=$tiltseries ";
		$command.="--pixelsize=$pixelsize ";
		
		return $command." ";
	}	
	
	// Use form footer to re-direct user
	// to the next step of the Protomo workflow.
	public function generateFormFooter()
	{
		global $imageinfo;
		
		$tiltseries = $_SESSION['tiltseries'] = $_SESSION['tiltseries'];
		$runname = $_SESSION['runname'] = $_POST['runname'];
		$_SESSION['sessionname'] = $_POST['sessionname'];
		$outdir = $_SESSION['outdir'] = $_POST['outdir'];
		$_SESSION['imageinfo'] = $imageinfo;
		
		return $html;
	}
}
?>
