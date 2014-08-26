<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicLayoutForm.inc";
require_once "inc/leginon.inc";

class Protomo2PrepForm extends BasicLayoutForm
{
	function __construct( $expId, $extraHTML, $session='',$tiltseries='', $commit='false' )
	{
		parent::__construct($expId);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('protomo');
		$this->setPublications( $pubList );
		$this->setJobType( 'protomo' );
		$this->setOutputDirectory( 'protomo_alignments' );
		$this->setBaseRunName( 'protomorun' );
		$this->setTitle( 'Protomo Alignment Preparation Launcher' );
		$this->setHeading( 'Protomo Alignment Preparation' );
		$this->setExeFile( 'protomo2prep.py' );
		$this->setGuideURL( "http://ami.scripps.edu/redmine/projects/appion/wiki/" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "protomo" );
		
		$params->addParam( "expId", $expId, "Experiment ID—should be pulled from project" );
		$params->addParam( "session", $session, "Session—in YYmthDDX format" );
		$params->addParam( "tiltseries", $tiltseries, "It'd be nice to have a big, wide pull-down menu" );
		$params->addParam( "commit", $commit, "Commits to database if 'true'" );
		
		
		// Validations
		//$params->addValidation( "projectid", "req" );
		//$params->addValidation( "projectid", "num" );
		$params->addValidation( "session", "req" );
		$params->addValidation( "tiltseries", "req" );
		$params->addValidation( "tiltseries", "num" );
		$params->addValidation( "commit", "req" );
		
	}
	
	// Generate a form for the parameters that are specific to this program (not Appion params)
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 8;
		
		$html .= "
	    <br />
	    <H4>Required Parameters</H4>
	    <hr />";
		
		$html.= $params->insertTextField( "session", $fieldSize );
		$html.= $params->insertTextField( "tiltseries", $fieldSize );
		$html.= $params->insertTextField( "commit", $fieldSize );
		
	    $html .= "<br></br>
	    <a href='runAppionLoop.php?expId=".$this->expId."&form=Protomo2CoarseAlignForm'><b><center>[Click here to continue onto Coarse Alignment if protomo2prep.py has already been run]</center></b></a>";

		return $html;
	}	
	
	
}
?>
