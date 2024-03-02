<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */
require_once "basicLoopForm.inc";

class looplearn extends BasicLoopForm
{


	function __construct( $expId, $extraHTML='', $interval=2 )

	{
		parent::__construct($expId, $extraHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('');
		$this->setPublications( $pubList );
		$this->setJobType( 'learn' );
		$this->setOutputDirectory( 'learn' );
		$this->setBaseRunName( 'learnrun' );
		$this->setTitle( 'Ptolemy Active Learning Launcher' );
		$this->setHeading( 'Send image processing results for Ptolemy to learn and auto update leginon target order' );
		$this->setExeFile( 'looplearn.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.

		//Other forms to include	

		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help, $ddstackid=false.
		$params->setHelpSection( "looplearn" );
				
		// Gctf parameters
		$params->addParam( "interval", $interval, "number of squares between each update" );
		$params->addValidation("interval", "num");
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
	    <H4>Required Parameters</H4>
	    <hr />";
			
		$html.= $params->insertTextField( "interval", $fieldSize );
		$html .= "
	    <br />
	    <H4>Appion Parameters</H4>
	    <hr />";

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

		$this->formParams->getPostedValues( $postArray );
		$paramArray = $this->formParams->getParamArray();
		// If the form does purely composite and does not define any params of its own,
		// the param array will be null.

		if ( $paramArray ) {
		}

		return $command;
	}


}
