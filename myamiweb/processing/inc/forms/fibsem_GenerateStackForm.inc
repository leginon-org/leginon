<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicLayoutForm.inc";

class fibsem_GenerateStackForm extends BasicLayoutForm

{
//	function __construct(  $expId, $errorHTML='', $infoHTML='', )
	function __construct(  $expId, $errorHTML='', $infoHTML='' )
	{
		parent::__construct($expId, $errorHTML, $infoHTML);

		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//

		// Set the publications to be references on the web pages
		$pubList = array('imod');
		$this->setPublications( $pubList );
		$this->setJobType( 'generatestack' );
		$this->setOutputDirectory( 'alstack' );
		$this->setBaseRunName( 'fibsem_stack_generation' );
		$this->setTitle( 'generatefibsemstack.py Launcher' );
		$this->setHeading( 'Generate an aligned stack' );
		$this->setExeFile( 'generatefibsemstack.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( True ); // Flag to hide the description field of the run parameters.

		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();

		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "generate_fibsem_stack" );
				
//		$params->addParam( "nparams", $nparams, "Number of parameters, 3=shiftx,shifty,rotate" );
//		$params->addParam( "reduce", $refimgid, "reduction factor" );
		//$params->addParam( "matt", $matt, "Clip outer percentage" );
		//$params->addParam( "bilinear", $bilinear, "Bilinear interpolation" );
		//$params->addParam( "sobel", $sobel, "Sobel filter or not" );
		//$params->addParam( "median", $median, "Median filter before alignment" );
		//$params->addParam( "timestamp", $timestamp, "Timestamp" );
		//$params->addParam( "dewarp", $dewarp, "Dewarping box size, 0 for none" );

		// Validations
		//$params->addValidation( "nparams", "req" );
		//$params->addValidation( "reduce", "req" );
		//$params->addValidation( "matt", "req" );
		//$params->addValidation( "bilinear", "req" );
		//$params->addValidation( "sobel", "req" );
		//$params->addValidation( "median", "req" );
		//$params->addValidation( "dewarp", "req" );
	}

	public function generateAdditionalFormRight()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();

		$fieldSize = 4;

		$html .= "<b>Generate FIBSEM stack params:</b><br />\n";

		$html.= "<br/>\n";
		$html.= "<br/>\n";
#		$html.= $params->insertTextField( "timestamp", $fieldSize, "(ex. 11jul18z)" );
	//	$html.= $params->insertTextField( "nparams", $fieldSize, "(2 for shiftX,shiftY)" );
		//$html.= $params->insertTextField( "reduce", $fieldSize );
		//$html.= $params->insertTextField( "matt", $fieldSize, "%" );
		//$html.= $params->insertTextField( "bilinear", $fieldSize, "(1 for yes)" );
		//$html.= $params->insertTextField( "sobel", $fieldSize, "(1 for yes)" );
		//$html.= $params->insertTextField( "median", $fieldSize, "(1 for yes)" );
		//$html.= $params->insertTextField( "dewarp", $fieldSize, "(box size, 0 for no dewarp)" );

		return $html;
	}

	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		// Get recent image to check nframes against alignoffset and nrw.
		$preset = $postArray['preset'];
		$testfilename = $postArray['testfilename'];
		$leginondata = new leginondata();
		if ( $testfilename ) {
			// testing
			$images = $leginondata->getFilename($testfilename, $this->expId);
			if ( !is_array($images ) || empty($images) ) {
				$msg .= "<B>Error:</B> image ".$testfilename." not found in the session <br/>";
			} else {
				$imageId = $images[0]['id'];
			}
		} else {
			// preset
			$images = $leginondata->getFilenames($this->expId, $preset);
			if ( !is_array($images ) || empty($images) ) {
				$msg .= "<B>Error:</B> no image found in preset";
			} else {
				$imageId = $images[0]['id'];
			}
		}

		if ( $imageId ) {
			$nframes = $leginondata->getNFramesSavedFromImage($imageId);
			if ( $nframes == false ) {
				if ( $testfilename ) {
					$msg .= "<B>Error</B> Image does not have frames saved. Can not make DDstack";
				}	else {
					$msg .= "<B>Error</B> Last image of the specified preset does not have frames saved. Can not validate. Try again later.";
				}
			}
		}
		return $msg;
	}

	// Override the parent build Commnad function to accomodate the "-" in the no-keepstack flag.
	// Dashes are not parsed correctly in the help.js file, so I have replaced them with an "_" in this file.
	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand($postArray);

		$paramArray = $this->formParams->getParamArray();
		$value = $this->formParams->getParamValue( "refimgid" );
		// if we are not testing an image, add the parellel flag
		if ( !($postArray['testimage']=="on") ) {
			$command = $this->addCommandFlag($command, "parallel", "parallel", "on" );
		}

		return $command;
	}

}
?>
