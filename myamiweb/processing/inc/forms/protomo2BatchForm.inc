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
require_once "inc/leginon.inc";

session_start();
$sessionname=$_SESSION['sessionname'];

class Protomo2BatchForm extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML, $sessionname='', $raw_path='', $procs='all',$coarse_param_file='', $refine_param_file='', $recon_param_file='',
	$cachedir='', $protomo_outdir='', $link_recons='', $tiltseriesranges='', $link='', $firststep='1', $laststep='3', $shift_limit='30' , $angle_limit='40',
	$coarse_retry_align='10', $coarse_retry_shrink='0.9', $refine_retry_align='12', $refine_retry_shrink='0.9', $all_tilt_videos="True", $all_recon_videos="True",
	$map_sampling='8', $map_size_x='512', $map_size_y='512', $map_size_z='200', $video_type='')
	{
		parent::__construct($expId, $extraHTML);
		
		$tiltseriesId = ($_POST['tiltseriesId']) ? $_POST['tiltseriesId'] : NULL;
		$particle = new particledata();
		$leginondata = new leginondata();
		$alltiltseries = $particle->getTiltSeries($_GET['expId']);
		$seriesselector_array = $particle->getTiltSeriesSelector($alltiltseries,$tiltseriesId);
		
		
		$iters=$_SESSION['recon_iter'];
		$map_size_x = $imageinfo['dimx']/$map_sampling;
		$map_size_y = $imageinfo['dimy']/$map_sampling;
		$coarse_param_file=$_SESSION['outdir'].$_SESSION['runname'].'/ready_for_batch/coarse_series'.sprintf('%04d',$_SESSION['tiltseries']).'.param';
		$refine_param_file=$_SESSION['outdir'].$_SESSION['runname'].'/ready_for_batch/refine_series'.sprintf('%04d',$_SESSION['tiltseries']).'.param';
		$recon_param_file=$_SESSION['outdir'].$_SESSION['runname'].'/ready_for_batch/recon_series'.sprintf('%04d',$_SESSION['tiltseries']).'.param';
		$link_recons=$_SESSION['outdir'].'batch_tiltseries_out/';
		$_POST['outdir']=$_SESSION['outdir'];
		$this->updateFormParams();
		$params = $this->getFormParams();
		$particle = new particledata();
		$alltiltseries = $particle->getTiltSeries($_GET['expId']);
		$num = count($alltiltseries);
		global $numtiltseries;
		$numtiltseries = $num;
		$tiltseriesranges="1-$numtiltseries";
		$sessionname=$_SESSION['sessionname'];
		
		global $html;
		
		//foreach(array_keys($imageinfo) as $paramName)
		//	echo $paramName . "<br>";
			//echo $imageinfo["$paramName"] . "<br>";
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('protomo');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'tiltseries' );
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
		
		$params->addParam( "tiltseries", $tiltseries, "Tilt Series #" );
		$params->addParam( "raw_path", $raw_path, "Raw Image Path" );
		$params->addParam( "procs", $procs, "Number of Processors" );
		$params->addParam( "coarse_param_file", $coarse_param_file, "Coarse Alignment Param File" );
		$params->addParam( "refine_param_file", $refine_param_file, "Refinement Param File" );
		$params->addParam( "recon_param_file", $recon_param_file, "Reconstruction Param File" );
		$params->addParam( "link_recons", $link_recons, "Link Final Reconstructions to this Directory" );
		$params->addParam( "tiltseriesranges", $tiltseriesranges, "Tilt Series to Process" );
		$params->addParam( "link", $link, "Link or Copy Raw Images?" );
		$params->addParam( "firststep", $firststep, "First Step" );
		$params->addParam( "laststep", $laststep, "Last Step" );
		$params->addParam( "shift_limit", $shift_limit, "Shift Limit" );
		$params->addParam( "angle_limit", $angle_limit, "Angle Limit" );
		$params->addParam( "coarse_retry_align", $coarse_retry_align, "Coarse Alignment Retries" );
		$params->addParam( "coarse_retry_shrink", $coarse_retry_shrink, "Window Size Fraction to Shrink Each Retry Attempt" );
		$params->addParam( "refine_retry_align", $refine_retry_align, "Refinement Retries" );
		$params->addParam( "refine_retry_shrink", $refine_retry_shrink, "Window Size Fraction to Shrink Each Retry Attempt" );
		$params->addParam( "all_tilt_videos", $all_tilt_videos, "Create Tilt Series Videos" );
		$params->addParam( "all_recon_videos", $all_recon_videos, "Create Reconstruction Videos" );
		$params->addParam( "map_sampling", $map_sampling, "Sampling for Depiction" );
		$params->addParam( "map_size_x", $map_size_x, "Reconstructon Size (x)" );
		$params->addParam( "map_size_y", $map_size_y, "Reconstructon Size (y)" );
		$params->addParam( "map_size_z", $map_size_z, "Reconstructon Size (z)" );
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
		$fieldSize2 = 30;
		
		#Initialize steps
		if (!isset($_POST['firststep'])) {$_POST['firststep']=1;}
		if (!isset($_POST['laststep'])) {$_POST['laststep']=3;}
		#Check for impossible setting
		if ($_POST['firststep'] > $_POST['laststep']) {$_POST['laststep']=$_POST['firststep'];}
		
		$steps=array("Preparation", "Coarse Alignment", "Refinement", "Reconstruction", "----------------", "Screening", "CTF Correction");
		$html .= "<br>
			<b><center>Number of tilt series available to process for session $sessionname: <font size='5'>$numtiltseries</font></center></b>";
		
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
			$html.= '<select name="link" style="width:66px">';
			$html.= '<option selected value="True">Link</option>';
			$html.= '<option value="False">Copy</option>';
			$html.= '</select>'; $html.= docpop('protomo_link', ' Link or Copy Raw Images?').'<br>';
			$html.= $params->insertTextFieldInRow( "shift_limit", $fieldSize ).'│ ';
			$html.= $params->insertTextField( "angle_limit", $fieldSize );
		}
		
		if ($_POST['firststep'] <= 2 and $_POST['laststep'] >= 2)
		{
			$html .= "
		<br />
		<H3>Coarse Alignment Parameters ".docpop('coarse_info', '(Info)')."</H3>
		<hr />";
			$html.= $params->insertTextField( "coarse_param_file", $fieldSize2 );
			$html.= $params->insertTextField( "coarse_retry_align", $fieldSize );
			$html.= $params->insertTextField( "coarse_retry_shrink", $fieldSize );
		}
		
		if ($_POST['firststep'] <= 3 and $_POST['laststep'] >= 3)
		{
			$html .= "
		<br />
		<H3>Refinement Parameters ".docpop('refine_info', '(Info)')."</H3>
		<hr />";
			$html.= $params->insertTextField( "refine_param_file", $fieldSize2 );
			$html.= $params->insertTextField( "refine_retry_align", $fieldSize );
			$html.= $params->insertTextField( "refine_retry_shrink", $fieldSize );
		}
		
		if ($_POST['firststep'] <= 4 and $_POST['laststep'] >= 4)
		{
			$html .= "
		<br />
		<H3>Reconstruction Parameters ".docpop('recon_info', '(Info)')."</H3>
		<hr />";
			$html.= $params->insertTextField( "recon_param_file", $fieldSize2 );
			$html.= $params->insertTextField( "link_recons", $fieldSize2 );
		}
		
		
			$html .= "
		<br />
		<H4>Depiction Parameters ".docpop('depictionparam_info', '(Info)')."</H4>
		<hr />";
			$html.= '<select name="create_tiltseriesvids" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_create_reconstruction', ' Create Tilt Series Videos').'<br>';
			$html.= '<select name="create_reconstruction" style="width:66px">';
			$html.= '<option selected value="true">true</option>';
			$html.= '<option value="false">false</option>';
			$html.= '</select>'; $html.= docpop('protomo_create_reconstruction2', ' Create Reconstruction Videos').'<br>';
			$html.= '<select name="video_type" style="width:66px">';
			$html.= '<option value="gif">Gif</option>';
			$html.= '<option selected value="html5vid">HTML5</option>';
			$html.= '</select>'; $html.= docpop('protomo_video_type', ' Video Type').'<br>';
			$html.= $params->insertTextField( "map_sampling", $fieldSize );
			$html.= $params->insertTextField( "map_size_x", $fieldSize );
			$html.= $params->insertTextField( "map_size_y", $fieldSize );
			$html.= $params->insertTextField( "map_size_z", $fieldSize );
			
		
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
		
		$command.="--sessionname=$sessionname ";
		$command.="--numtiltseries=$numtiltseries ";
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
		if (isset($_POST['procs']) AND isset($_POST['coarse_param_file']) AND isset($_POST['refine_param_file']) AND isset($_POST['recon_param_file']) AND isset($_POST['tiltseriesranges']))
		{
			$trimmed_runname=preg_replace("/\d+$/","",$_POST['runname']);
			$folders=$trimmed_runname.'XXXX';
			$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2BatchSummary'><b><center>[Click here to View Batch Alignment and Reconstructon Results after protomo2batch.py has been run] <font size='5'>→</font></center></b></a>";
			$html .= "<br></br>
			<b><center>[Execution of this protomo2batch.py command will create folders '".$folders."'<br> in the protomo_alignments directory, overwriting folders & files when necessary]</center></b>";
			$html .= "<br>
			<b><center>[It is recommended that you run protomo2batch.py either on a dedicated machine or using screen/tmux/nohup]</center></b>";
			$html .= "
			<b><center>[protomo2batch.py may require long CPU time limits depending on the number of tilt series being processed]</center></b>";
		}
		
		return $html;
	}
}
?>
