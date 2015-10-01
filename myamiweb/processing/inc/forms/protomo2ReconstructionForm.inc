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
require_once "inc/leginon.inc";

session_start();
$refine_thickness=$_SESSION['thickness'];
$tiltseries=$_SESSION['tiltseries'];
$sessionname=$_SESSION['sessionname'];
$outdir=$_SESSION['outdir'];
$runname=$_SESSION['runname'];
$imageinfo=$_SESSION['imageinfo'];
$protomo_outdir = $_SESSION['protomo_outdir'];
$_SESSION['erase_refine'] = 0;

class Protomo2ReconstructionForm extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML, $commit='false', $recon_iter='', $recon_map_sampling='2', $recon_map_size_x='4096', $recon_map_size_y='4096',
	$recon_thickness='2000', $pixelsize='', $recon_lowpass='', $recon_lp_diam_x='15', $recon_lp_diam_y='15')
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
		global $refine_thickness;
		$tiltseries=$_SESSION['tiltseries'];
		$_POST['runname']=$_SESSION['runname'];
		$_POST['outdir']=$_SESSION['outdir'];
		$_POST['protomo_outdir']=$_SESSION['protomo_outdir'];
		$_POST['pixelsize'] = $imageinfo['pixelsize']*pow(10,10);
		$recon_iter=$_SESSION['iters'];
		$recon_map_size_x = $imageinfo['dimx'];
		$recon_map_size_y = $imageinfo['dimy'];
		$recon_thickness = $refine_thickness;
		$recon_lp_diam_x = round(pow(10,10)*$imageinfo['pixelsize']*8);
		$recon_lp_diam_y = round(pow(10,10)*$imageinfo['pixelsize']*8);
		
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
		
		$params->addParam( "recon_iter", $recon_iter, "Refinement Iteration used to generate Reconstruction (<strong>Required Parameter</strong>)" );
		$params->addParam( "recon_map_sampling", $recon_map_sampling, "Reconstruction Sampling" );
		$params->addParam( "recon_map_size_x", $recon_map_size_x, "Reconstructon Size (x)" );
		$params->addParam( "recon_map_size_y", $recon_map_size_y, "Reconstructon Size (y)" );
		$params->addParam( "recon_thickness", $recon_thickness, "Reconstructon Thickness" );
		$params->addParam( "recon_lowpass", $recon_lowpass, "Lowpass Filter" );
		$params->addParam( "recon_lp_diam_x", $recon_lp_diam_x, "(x)" );
		$params->addParam( "recon_lp_diam_y", $recon_lp_diam_y, "(y)" );
		$params->addParam( "link_recon", $link_recon, "Link Final Reconstructions to this Directory" );
		
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
		$fieldSize2 = 30;
		
		$html .= "
	    <br />
	    <H4>Reconstruction Parameters ".docpop('recon_info2', '(Info)')."</H4>
	    <hr />";
		
		$html.= $params->insertTextField( "recon_iter", $fieldSize );
	    $html.= $params->insertTextField( "recon_map_sampling", $fieldSize );
		$html.= $params->insertTextField( "recon_map_size_x", $fieldSize );
		$html.= $params->insertTextField( "recon_map_size_y", $fieldSize );
		$html.= $params->insertTextField( "recon_thickness", $fieldSize );
		$html.= '<select name="recon_lowpass" style="width:66px">';
		$html.= '<option value="True">True</option>';
		$html.= '<option selected value="False">False</option>';
		$html.= '</select>'; $html.= docpop('recon_lowpass', ' Lowpass Filter │ ');
		$html.= $params->insertTextFieldInRow( "recon_lp_diam_x", $fieldSize ).'│ ';
		$html.= $params->insertTextField( "recon_lp_diam_y", $fieldSize );
		$html.= $params->insertTextField( "link_recon", $fieldSize2 );
		
		$html .= "<hr />";
		
		// Only display link to next step in tomo processing if on completed Command page
		if (empty($_POST['recon_iter']))
		{
			$html .= "<br></br>
			<b><center>[Enter all required parameters and click 'Just Show Command' to proceed]</center></b>";
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
		
		$pixelsize=$_POST['pixelsize'];
		$command.="--pixelsize=$pixelsize ";
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
			//$html .= "<br></br>
				//<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2UploadForm'><b><center>[Click here to continue on to <font size='4'>Upload your Reconstruction</font>] <font size='5'>→</font></center></center></b></a>";
			$html .= "<br>
				<a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2BatchForm'><b><center>[Click here to use all previous parameter files for <font size='4'>Batch Refinement and Reconstruction</font> of this session's tilt-series] <font size='5'>→</font></center></center></b></a>";
		}	
		return $html;
	}
}
?>
