<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicParticleForm.inc";

class ManualPickerForm extends BasicParticleForm

{
	function __construct(  $expId, $extraHTML='' ) 
	{
		parent::__construct($expId, $extraHTML);

		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('appion');
		$this->setPublications( $pubList );
		$this->setJobType( 'manualpicker' );
		$this->setOutputDirectory( 'extract' );
		$this->setBaseRunName( 'manrun' );
		$this->setTitle( 'ManualPicker.py Launcher' );
		$this->setHeading( 'Manual Particle Selection' );
		$this->setExeFile( 'manualpicker.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "particle" );
				
		//Advanced parameters

	}		
		
	public function generateParticleTable() {
		//$this->updateFormParams();

		//Basic manual picking parameters
		$manualTable = new ManualTable();
		$html .= $manualTable->generateForm();

		//Helix segment picking
		$helicalTable = new HelicalTable();
		$html .= $helicalTable->generateForm();

		$html .= "<hr/>\n";
		$html .= parent::generateParticleTable();
	
		return $html;
	}

	public function validate( $postArray )
	{
		$msg .= parent::validate( $postArray );
		$manualTable = new ManualTable();
		$msg .= $manualTable->validate($postArray);
		
		$helicalTable = new HelicalTable();
		$msg .= $helicalTable->validate($postArray);

		
		return $msg;
	}
	
	// Override buildCommand so that we can call it from ParticleForm
	public function buildCommand( $postArray )
	{	
		$command = parent::buildCommand( $postArray );
		
		// add params from tables
		$manualTable = new ManualTable();
		$helicalTable = new HelicalTable();
		$command .= $manualTable->buildCommand( $postArray );
		$command .= $helicalTable->buildCommand( $postArray );
		
		return $command;		
	}
}
?>
