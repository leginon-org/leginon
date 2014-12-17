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
$tiltseries=$_SESSION['tiltseries'];
$sessionname=$_SESSION['sessionname'];
$imageinfo=$_SESSION['imageinfo'];

class Protomo2BatchForm extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML, $sessionname='', $tiltseries='', $raw_path='', $procs='all', $iters='',$coarse_param_file='', $refine_param_file='', $recon_param_file='', $cachedir='', $protomo_outdir='', $link_recons='', $tiltseriesranges='', $link='' )
	{
		parent::__construct($expId, $extraHTML);
		//print "_POST:" . "<br>";
		//var_dump($_POST);
		//print "_GET:" . "<br>";
		//var_dump($_GET);
		//print "_SESSION:" . "<br>";
		//var_dump($_SESSION);
		
		global $imageinfo;
		$iters=$_SESSION['recon_iter'];
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
		$params->addParam( "iters", $iters, "Alignment Iterations" );
		$params->addParam( "coarse_param_file", $coarse_param_file, "Coarse Alignment Param File" );
		$params->addParam( "refine_param_file", $refine_param_file, "Refinement Param File" );
		$params->addParam( "recon_param_file", $recon_param_file, "Reconstruction Param File" );
		$params->addParam( "link_recons", $link_recons, "Link Final Reconstructions to this Directory" );
		$params->addParam( "tiltseriesranges", $tiltseriesranges, "Tilt Series to Process" );
		$params->addParam( "link", $link, "Link or Copy Raw Images?" );
		
	}
		
	// Generate a form for the parameters that are specific to this program (not Appion params)
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		global $numtiltseries;
		global $sessionname;
		
		$fieldSize = 5;
		$fieldSize2 = 25;
		
		$html .= "<br></br>
			<b><center>Number of tilt series available to process for session $sessionname: <font size='5'>$numtiltseries</font></center></b>";
		
		$html .= "
	    <br />
	    <H4>Batch Parameters</H4>
	    <hr />";
		
		$html.= $params->insertTextField( "procs", $fieldSize );
		$html.= '<select name="link" style="width:66px">';
		$html.= '<option selected value="True">Link</option>';
		$html.= '<option value="False">Copy</option>';
		$html.= '</select>'; $html.= docpop('protomo_link', ' Link or Copy Raw Images?').'<br>';
		$html.= $params->insertTextField( "tiltseriesranges", $fieldSize );
		$html.= $params->insertTextField( "iters", $fieldSize );
		$html.= $params->insertTextField( "coarse_param_file", $fieldSize2 );
		$html.= $params->insertTextField( "refine_param_file", $fieldSize2 );
		$html.= $params->insertTextField( "recon_param_file", $fieldSize2 );
		$html.= $params->insertTextField( "link_recons", $fieldSize2 );
		
		$html .= "<hr />";
		
		// Only display link to next step in tomo processing if on completed Command page
		if (empty($_POST['iters']) AND empty($_POST['procs']) AND empty($_POST['coarse_param_file']) AND empty($_POST['refine_param_file']) AND empty($_POST['tiltseriesranges']))
		{
			$html .= "<br></br>
			<b><center>[Enter all Parameters and click 'Just Show Command' to proceed]</center></b>";
		}
		
		return $html;
	}	

	// Override the default build Command Function because the --session and coarse flags are not normal
	// for other Appion Loop methods and not included in the parent.
	public function buildCommand( $postArray )
	{
		$command   = parent::buildCommand( $postArray );
		
		global $tiltseries;
		global $sessionname;
		global $numtiltseries;
		
		$command.="--tiltseries=$tiltseries ";
		$command.="--sessionname=$sessionname ";
		$command.="--numtiltseries=$numtiltseries ";
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
		global $numtiltseries;

		$_SESSION['tiltseries'] = $tiltseries;
		$_SESSION['runname'] = $_POST['runname'];
		$_SESSION['sessionname'] = $sessionname;
		$_SESSION['outdir'] = $_POST['outdir'];
		$_SESSION['imageinfo'] = $imageinfo;
		$_SESSION['iters'] = $_POST['iters'];
		$_SESSION['tiltseriesranges'] = $_POST['tiltseriesranges'];
		
		// Only display link to next step in tomo processing if on completed Command page
		if (isset($_POST['iters']) AND isset($_POST['procs']) AND isset($_POST['coarse_param_file']) AND isset($_POST['refine_param_file']) AND isset($_POST['recon_param_file']) AND isset($_POST['tiltseriesranges']))
		{
			$trimmed_runname=preg_replace("/\d+$/","",$_POST['runname']);
			$folder_start=$trimmed_runname.sprintf('%04d',1);
			$folder_end=$trimmed_runname.sprintf('%04d',$numtiltseries);
			$html .= "<br></br>
			<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2BatchSummary'><b><center>[Click here to View Batch Alignment and Reconstructon Results after protomo2batch.py has been run] <font size='5'>→</font></center></b></a>";
			$html .= "<br></br>
			<b><center>[Execution of this protomo2batch.py command will create folders: ".$folder_start." thru ".$folder_end."<br>in the protomo_alignments directory, overwriting folders & files when necessary]</center></b>";
			$html .= "<br>
			<b><center>[It is recommended that you run protomo2batch.py either on a dedicated machine or using screen/tmux/nohup]</center></b>";
			$html .= "
			<b><center>[protomo2batch.py may require long CPU time limits depending on the number of tilt series being processed]</center></b>";
		}
		
		return $html;
	}
}
?>
