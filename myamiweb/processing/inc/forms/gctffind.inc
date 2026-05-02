<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */
require_once "basicLoopForm.inc";
require_once "dbDefocusTable.inc";

class GCtfFind extends BasicLoopForm
{
	function __construct( $expId, $extraHTML='', $ampcontrast='0.07', $fieldsize='1024',
								$astig='0.05', $bestdb=true, $nominal='', $parallel=true, $phase_plate=false, $min_phase_shift=10, $max_phase_shift=170) 
	{
		parent::__construct($expId, $extraHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('gctffind');
		$this->setPublications( $pubList );
		$this->setJobType( 'ctfestimate' );
		$this->setOutputDirectory( 'gctffind' );
		$this->setBaseRunName( 'gctffindrun' );
		$this->setTitle( 'GCTFFIND Launcher' );
		$this->setHeading( 'CTF Estimation with GCTFFIND' );
		$this->setExeFile( 'gctffind.py' );
		$this->setGuideURL( "http://leginon.org/" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );
				
		$params->addParam( "ampcontrast", $ampcontrast, "Amplitude Contrast" );
		$params->addParam( "fieldsize", $fieldsize, "Field Size" );
		$params->addParam( "astig", $dast, "Expected Astigmatism (in fraction)" );
		$params->addParam( "parallel", $parallel, "Allow parallel runs" );

		$params->addParam( "phase_plate", $phase_plate, "Use phase plate" );
		$params->addParam( "min_phase_shift", $min_phase_shift, "Minimun Phase Shift in search (degrees)" );
		$params->addParam( "max_phase_shift", $max_phase_shift, "Maximun Phase Shift in search (degrees)" );
		
		// Validations
		//$params->addValidation( "numpart", "req" );
	}
		
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();

		$html.= "<hr>";

		$html.= parent::generateAdditionalFormLeft();
		return $html;
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
		$html.= $params->insertTextField( "astig", $fieldSize );
		$html.= $params->insertCheckboxField( "parallel" );

		$html.= $params->insertCheckboxField( "phase_plate" );
		$html.= $params->insertTextField( "min_phase_shift", $fieldSize );
		$html.= $params->insertTextField( "max_phase_shift", $fieldSize );

		
		return $html;
	}	

	public function validate($postArray )
	{
		$msg = parent::validate( $postArray );

		return $msg;
	}

	public function buildCommand( $postArray )
	{

		$command = parent::buildCommand( $postArray );
		return $command;
	}
}
?>
