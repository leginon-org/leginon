<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicLayoutForm.inc";
require_once "inc/leginon.inc";

session_start();
$tiltseries=$_SESSION['tiltseries'];
$sessionname=$_SESSION['sessionname'];
$outdir=$_SESSION['outdir'];
$runname=$_SESSION['runname'];
$imageinfo=$_SESSION['imageinfo'];
$protomo_outdir = $_SESSION['protomo_outdir'];
$_SESSION['erase_refine'] = 0;

class Protomo2ReconstructionForm extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML, $commit='false', $recon_iter='', $map_sampling='1', $map_size_x='512', $map_size_y='512', $map_size_z='1600', $protomo_outdir='' )
	{
		parent::__construct($expId, $extraHTML);
		//print "_POST:" . "<br>";
		//var_dump($_POST);
		//print "_GET:" . "<br>";
		//var_dump($_GET);
		//print "_SESSION:" . "<br>";
		//var_dump($_SESSION);
		
		global $imageinfo;
		global $protomo_outdir;
		$tiltseries=$_SESSION['tiltseries'];
		$_POST['runname']=$_SESSION['runname'];
		$_POST['outdir']=$_SESSION['outdir'];
		$_POST['protomo_outdir']=$_SESSION['protomo_outdir'];
		$recon_iter=$_SESSION['iters'];
		$map_size_x = $imageinfo['dimx']/$map_sampling;
		$map_size_y = $imageinfo['dimy']/$map_sampling;
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('protomo');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'protomorun' );
		$this->setTitle( 'Protomo Reconstruction Launcher' );
		$this->setHeading( 'Protomo Reconstruction' );
		$this->setExeFile( 'protomo2reconstruction.py' );
		$this->setGuideURL( "http://www.electrontomography.org/?page_id=317" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "protomo" );
		
		$params->addParam( "recon_iter", $recon_iter, "Refinement Iteration used to Generate Reconstruction (<strong>Required Parameter</strong>)" );
		$params->addParam( "map_sampling", $map_sampling, "Reconstruction Sampling" );
		$params->addParam( "map_size_x", $map_size_x, "Reconstructon Size (x)" );
		$params->addParam( "map_size_y", $map_size_y, "Reconstructon Size (y)" );
		$params->addParam( "map_size_z", $map_size_z, "Reconstructon Size (z)" );
		$params->addParam( "protomo_outdir", $protomo_outdir, "Protomo outdir (for internal use)" );
		
		
		// Validations
		$params->addValidation( "recon_iter", "req" );
		$params->addValidation( "recon_iter", "num" );
		
	}
	
	// Generate a form for the parameters that are specific to this program (not Appion params)
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 5;
		
		$html .= "
	    <br />
	    <H4>Reconstruction Parameters</H4>
	    <hr />";
		
		$html.= $params->insertTextField( "recon_iter", $fieldSize );
	    	$html.= $params->insertTextField( "map_sampling", $fieldSize );
		$html.= $params->insertTextField( "map_size_x", $fieldSize );
		$html.= $params->insertTextField( "map_size_y", $fieldSize );
		$html.= $params->insertTextField( "map_size_z", $fieldSize );
		
		$html .= "<hr />";
		
		// Only display link to next step in tomo processing if on completed Command page
		if (empty($_POST['recon_iter']))
		{
			$html .= "<br></br>
			<b><center>[Enter the Required Parameters and click 'Just Show Command' to proceed]</center></b>";
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
		
		$command.="--tiltseries=$tiltseries ";
		$command.="--sessionname=$sessionname ";
		
		return $command." ";
	}	
	
	// Override the default ShowReference function because the user needs to be re-directed
	// to the next step of the Protomo workflow.
	public function showReference( $postArray )
	{
		$html = parent::showReference( $postArray );
		
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
		$_SESSION['recon_iter']=$_POST['recon_iter'];
		
		if (isset($_POST['recon_iter']))
		{
			$html .= "<br></br>
				<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2UploadForm'><b><center>[Click here to continue on to <font size='4'>Upload your Reconstruction</font>] <font size='5'>→</font></center></center></b></a>";
			$html .= "<br>
				<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2BatchForm'><b><center>[Click here to use ALL previous settings for <font size='4'>Batch Refinement and Reconstruction</font> of this session's tilt series] <font size='5'>→</font></center></center></b></a>";
		}	
		return $html;
	}
}
?>
