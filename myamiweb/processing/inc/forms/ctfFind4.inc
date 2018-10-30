<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */
require_once "basicLoopForm.inc";
require_once "ddstackSelectTable.inc";
require_once "dbDefocusTable.inc";

class CtfFind4 extends BasicLoopForm
{
	function __construct( $expId, $extraHTML='', $ampcontrast='0.07', $fieldsize='1024',
								$resmin='50', $resmax='4', $defstep='0.1', $numstep='25', $dast='0.05', $bestdb=true, $nominal='', $parallel=true, $useDDStack=false, $ddstackid=false, $phase_plate=false, $min_phase_shift=10, $max_phase_shift=170, $phase_search_step=10, $num_frame_avg=7) 
	{
		parent::__construct($expId, $extraHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('ctffind4');
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
		
		$this->ddStackSelectTable = new DDStackSelectTable($expId, $useDDStack, $ddstackid);
		$this->ddStackSelectTable->setOnlyAligned(false);
		$this->dbDefocusTable = new dbDefocusTable($expId, $bestdb, $nominal);
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
		$params->addParam( "parallel", $parallel, "Allow parallel runs" );

		$params->addParam( "phase_plate", $phase_plate, "Use phase plate" );
		$params->addParam( "min_phase_shift", $min_phase_shift, "Minimun Phase Shift in search (degrees)" );
		$params->addParam( "max_phase_shift", $max_phase_shift, "Maximun Phase Shift in search (degrees)" );
		$params->addParam( "phase_search_step", $phase_search_step, "Initial Phase Shift Search Step (degrees)" );
		$params->addParam( "num_frame_avg", $num_frame_avg, "Number of Frames to average" );
		
		// Validations
		//$params->addValidation( "numpart", "req" );
	}
		
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();

		$html .=$this->ddStackSelectTable->generateForm();
		$html.= $params->insertTextField( "num_frame_avg", 4 );
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
		$html.= $params->insertTextField( "resmin", $fieldSize );
		$html.= $params->insertTextField( "resmax", $fieldSize );
		$html.= $params->insertTextField( "defstep", $fieldSize );
		$html.= $params->insertTextField( "numstep", $fieldSize );
		$html.= $params->insertTextField( "dast", $fieldSize );
		$html .=$this->dbDefocusTable->generateForm();
		$html.= $params->insertCheckboxField( "parallel" );

		$html.= $params->insertCheckboxField( "phase_plate" );
		$html.= $params->insertTextField( "min_phase_shift", $fieldSize );
		$html.= $params->insertTextField( "max_phase_shift", $fieldSize );
		$html.= $params->insertTextField( "phase_search_step", $fieldSize );

		
		return $html;
	}	

	public function validate($postArray )
	{
		$msg = parent::validate( $postArray );
		$msg .= $this->ddStackSelectTable->validate( $postArray);
		$msg .= $this->dbDefocusTable->validate( $postArray);

		return $msg;
	}

	public function buildCommand( $postArray )
	{

		$command = parent::buildCommand( $postArray );
		$command .= $this->dbDefocusTable->buildCommand( $postArray);
		$command .= $this->ddStackSelectTable->buildCommand( $postArray);
		return $command;
	}
}
?>
