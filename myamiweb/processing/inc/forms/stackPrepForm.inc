<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicForm.inc";


class StackPrepForm extends BasicForm
{
	function __construct( $lastParticle='', $lowpass='', $highpass='', $bin='' ) 
	{
		parent::__construct();
		$params = $this->getFormParams();
				
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "stackprep" );
		
		$params->addParam( "lastParticle", $lastParticle, "last particle to use" );
		$params->addParam( "lowpass", $lowpass, "low-pass filter" );
		$params->addParam( "highpass", $highpass, "high-pass filter" );
		$params->addParam( "bin", $bin, "binning" );
	}
	
	public function generateForm()
	{
		// if the form is being reloaded, make sure we keep anything the user already set.
		$this->updateFormParams();
		$params = $this->getFormParams();

		$html = "
	    <br />
	    <H4>Stack Preparation Parameters</H4>
	    <hr />";
	
		$html.= $params->insertTextField( "lastParticle", 4, "(leave blank for all particles)");
		$html.= $params->insertTextField( "lowpass", 4, "(angstroms)" );
		$html.= $params->insertTextField( "highpass", 4, "(angstroms)" );
		$html.= $params->insertTextField( "bin", 4 );
			
		$html.= "<br/>\n";

		return $html;
	}
}
?>
