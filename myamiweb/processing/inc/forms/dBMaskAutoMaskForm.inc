<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */
require_once "autoMaskForm.inc";

class dBMaskAutoMaskForm extends autoMaskForm
{
	function __construct( $expId, $errorHTML='', $infoHTML='', $epsilon='15',$min_samp='10',$perc_threshold='99',$bin='4') 
	{
		parent::__construct($expId, $errorHTML, $infoHTML );
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('appion');
		$this->setPublications( $pubList );
		$this->setJobType( 'maskmaker' );
		$this->setOutputDirectory( 'mask' );
		$this->setBaseRunName( 'maskrun' );
		$this->setTitle( 'Auto Masking Launcher' );
		$this->setHeading( 'Automated Masking with dBAutoMasker' );
		$this->setExeFile( 'dBAutoMasker.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
		$this->setTestable( True ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "dbmask_automasker" );
		
		$params->addParam( "bin", $bin, "Binning of the image" );		
		$params->addParam( "epsilon", $epsilon, "Epsilon for DBSCAN" );
		$params->addParam( "min_samp", $min_samp, "Minimum samples per cluster" );
		$params->addParam( "perc_threshold", $perc_threshold, "Threshold for initial binary mask (default 99)" );
		
		// Validations
		//$params->addValidation( "numpart", "req" );
	}
		
	// Generate a form for the parameters that are specific to this program (not Appion params)
	public function generateAdditionalFormRight()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 5;
		
		$html .= "
	    <br />
	    <H4>Optional Parameters</H4>
	    <hr />";
		
		$html.= $params->insertTextField( "epsilon", $fieldSize );
		$html.= $params->insertTextField( "min_samp", $fieldSize );
		$html.= $params->insertTextField( "perc_threshold", $fieldSize );
		$html.= $params->insertTextField( "bin", $fieldSize );	
		return $html;
	}	

	// Override the default build Command Function because the --test flag is not normal
	// for other Appion Loop methods and not included in the parent.
	public function buildCommand( $postArray )
	{
		$command   = parent::buildCommand( $postArray );
		
		if ( $postArray['testimage']=="on" ) {
			$command.= " --test";
		}
		
		return $command." ";
	}	
	
	// getTestResults() should return the HTML code needed to display test results any way this method
	// prefers to have them displayed. The results will be placed below a printout of the test command and 
	// above the launch form. Note that an instance of this class is not required to use this function.
	static public function getTestResults( $outdir, $runname, $testfilename )
	{
		$testdir 		= $outdir.$runname."/tests/"; // Path to output mask jpgs images
		$jpgdir 		= $outdir.$runname."/jpgs/"; // Path to original input jpg images
		$origjpgname 	= preg_replace( "%.mrc%",".jpg", $testfilename );			
		$origJpgFull 	= $jpgdir.$origjpgname; // Full path to original test imgage jpg
		$imgrescl 		= 0.075; // Scale factor for displaying the result image 
		
		if (file_exists($testdir)) {
     		// open image directory
     		$pathdir = opendir( $testdir );
			// get all files in directory
			$ext='jpg';
			while ( $filename=readdir($pathdir) ) {
			   	if ($filename == '.' || $filename == '..') continue;
				if (preg_match('`\.'.$ext.'$`i',$filename)) $files[] = $filename;
			}
			closedir( $pathdir );
		}
		
		if ( count($files) > 0 ) {
			sort($files);
			$imgname 		= $files[0];
			$maskimgfull 	= $testdir.$imgname; 	
			$html .= "$imgname<P>";
			$html .= "<img src='loadimg.php?filename=".$origJpgFull."&scale=".$imgrescl."&overlay=".$maskimgfull."'>\n";
		} else {
			// Tell the users what to do if the test results are not found.
			$html .=  "<FONT COLOR='RED'><B>NO RESULT YET</B><br></FONT>";
			$html .=  "<FONT COLOR='RED'>Use <B>Refresh Test Results</B> button to display the test results when processing completes<br></FONT>";
		}
		
		return $html;
	}	
}
?>
