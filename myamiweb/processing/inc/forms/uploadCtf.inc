<?php

/**
 *	The Leginon software is Copyright under
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */
// This class displays a form used to create a command similar to the following:
// uploadCtfEstimates.py \
// -f /emg/sw/myami/appion/docker/centos6/ctfdata-session0003.dat \
// -s artemia2 -p 1 --commit

require_once "basicLayoutForm.inc"; //includes the BasicLayoutForm class that this class extends
require_once "inc/particledata.inc"; // needed to look up symmetry values
require_once "inc/summarytables.inc"; // needed to show stack and model tables

class UploadCtf extends BasicLayoutForm
{

	function __construct( $expId, $extraHTML='', $filename='')
	{
		parent::__construct($expId, $extraHTML);

		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//

		// Set the publications to be references on the web pages
		$pubList = array('appion');
		$this->setPublications( $pubList );
		$this->setJobType( 'uploadctf' );
		$this->setOutputDirectory( 'ctf' );
		$this->setBaseRunName( 'uploadctf' );
		$this->setTitle( 'Upload CTF Estimates' );
		$this->setHeading( 'Upload CTF Estimates' );
		$this->setExeFile( 'uploadCtfEstimates.py' );
		//$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Upload_CTF" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		$this->setUseCluster( False );

		//------ Set Parameters specific to the program that requires this new form -----//

		$params = $this->getFormParams();

		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );

		// Add each of the parameters here.
		// addParam( "key", default_value, "Label that appears in GUI")
		$params->addParam( "filename", $ctfDatFile, "" );

		// Validations
		$params->addValidation( "filename", "req" );
	}

	// Generate a form for the parameters that are specific to this program
	// The Left side will just show the stack and model that the user selected
	// on the previous pages. This overrides the generateAdditionalFormLeft()
	// function that is found in the BasicLayoutForm class.
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		$fieldSize = 64;
		$html .= "<H4>Enter CTF dat file with complete path</H4>";
		$html.= $params->insertTextField( "filename", $fieldSize, "" );

		return $html;
	}
}
?>
