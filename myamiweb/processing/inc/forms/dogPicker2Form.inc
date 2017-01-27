<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "mathParticleForm.inc";

class DogPicker2Form extends MathParticleForm
{
	function __construct(  $expId, $errorHTML='', $infoHTML='', $kfactorv=1.2, $numslicesv='',$sizerangev='',$invertv="on" ) 
	{
		parent::__construct($expId, $errorHTML, $infoHTML);
		$this->showfilters=false; //override to not display lowpass and highpass fields
		$this->imageContrastTable = new DogPickerImageContrastTable($invertv);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('dog');
		$this->setLogoImagePath( 'img/dogpicker2.jpg' );
		$this->setPublications( $pubList );
		$this->setJobType( 'dogpicker' );
		$this->setOutputDirectory( 'extract' );
		$this->setBaseRunName( 'ddogrun' );
		$this->setTitle( 'dogPicker2.py Launcher' );
		$this->setHeading( 'Automated Particle Selection with DoG Picker' );
		$this->setExeFile( 'dogPicker2.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
		$this->setTestable( True ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );
				
		//Advanced parameters

		//Single slice
		$params->addParam( "kfactor", $kfactorv, "K-factor" );
		//Multiple slices
		$params->addParam( "numslices", $numslicesv, "Number of Slices" );
		$params->addParam( "sizerange", $sizerangev, "Size Range" );

		// Validations
		//$params->addValidation( "numpart", "req" );
	}
		
	public function generateAdvancedTableRight() {
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 3;

		$html = parent::generateAdvancedTableRight();

		$html .= $params->insertTextField( "kfactor", $fieldSize, "(slopiness)" );
		$html .= "<b>Multi-scale dogpicker:</b><br />\n";
		$html .= $params->insertTextField( "numslices", $fieldSize,"(number of sizes)" );
		$html .= $params->insertTextField( "sizerange", $fieldSize,"(in &Aring;ngstroms)" );
		$html .="<br />\n";
		return $html;
	}

	// Override the validate function so that we can verify the DogPicker parameters
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		
		$params = $this->getFormParams();
		
		
		$numslices = $params->getParamValue('numslices');
		if ( $numslices != "" && $numslices < 2 )
		{
			$msg .= "<B>Error:</B> numslices must be more than 1 for multisize picking";
		}
		return $msg;
	}


	// getTestResults() return the HTML code needed to display test results from this method
	static public function getTestResults( $outdir, $runname, $testfilename )
	{
		$testjpg = preg_replace("%.mrc%","",$testfilename);
		$testResultFile = $testjpg.".prtl.jpg";
		$jpgimg = Path::join($outdir, $runname, "jpgs", $testResultFile);
		
		$pathToMaps = Path::join($outdir, $runname, "maps");

		// Fix me, Not the best way to get binning
		$bin = $_POST['bin'];		
		if ($_POST['process'] != "Just Show Command") {
			$filePattern = $testjpg."*.jpg";
			$pathPattern = Path::join($pathToMaps, $filePattern);
			$dogmaplist = glob($pathPattern);
			$html .= writeTestResults($jpgimg, $dogmaplist, $bin);
		} else {
			$mapFile = $testjpg.".dogmap1.jpg";
			$ccclist = array();
			$cccimg = Path::join($pathToMaps, $mapFile);
			$ccclist[]=$cccimg;
			$html.= writeTestResults($jpgimg,$ccclist,$bin=$bin);			
		}	
		return $html;
	}
}
?>
