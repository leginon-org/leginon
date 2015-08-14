<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */
require_once "basicLoopForm.inc";

class CtfFind4 extends BasicLoopForm
{
	function __construct( $expId, $extraHTML='', $ampcontrast='0.07', $fieldsize='1024',
								$resmin='50', $resmax='10', $defstep='0.1', $numstep='25', $dast='0.05', $bestdb=true) 
	{
		parent::__construct($expId, $extraHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('appion');
		$this->setPublications( $pubList );
		$this->setJobType( 'ctfestimate' );
		$this->setOutputDirectory( 'ctf' );
		$this->setBaseRunName( 'ctffind4run' );
		$this->setTitle( 'CTFFIND v4 Launcher' );
		$this->setHeading( 'CTF Estimation with CTFFIND v4' );
		$this->setExeFile( 'ctffind4.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );
				
		$params->addParam( "ampcontrast", $ampcontrast, "Amplitude Contrast" );
		$params->addParam( "fieldsize", $fieldsize, "Field Size" );
		$params->addParam( "resmin", $resmin, "Minimum Resolution (in &Aring;)" );
		$params->addParam( "resmax", $resmax, "Maximum Resolution (in &Aring;)" );
		$params->addParam( "defstep", $defstep, "Defocus Step (in &mu;m)" );
		$params->addParam( "numstep", $numstep, "Number of Steps to Search" );
		$params->addParam( "dast", $dast, "Expected Astigmatism (in &mu;m)" );
		$params->addParam( "bestdb", $bestdb, "Use best values from Database" );
		
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
		
		$html.= $params->insertTextField( "ampcontrast", $fieldSize );
		$html.= $params->insertTextField( "fieldsize", $fieldSize );
		$html.= $params->insertTextField( "resmin", $fieldSize );
		$html.= $params->insertTextField( "resmax", $fieldSize );
		$html.= $params->insertTextField( "defstep", $fieldSize );
		$html.= $params->insertTextField( "numstep", $fieldSize );
		$html.= $params->insertTextField( "dast", $fieldSize );
		$html.= $params->insertCheckboxField( "bestdb" );

		
		return $html;
	}	

}
?>
