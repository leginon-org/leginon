<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "stackPrepForm.inc";
require_once "inc/particledata.inc";

class StackPrepFormRelion extends StackPrepForm
{
	function __construct( $stackid='', $lastParticle='', $lowpass='', $highpass='', $bin='', $reconiterid='', $emaninit='', $ctffindonly='', $ctftilt='', $paramonly='' ) 
	{
		parent::__construct($lastParticle, $lowpass, $highpass, $bin);
		$params = $this->getFormParams();
						
		// Relion does not need the filter params 
		// that are defined in the base class
		$params->hideParam("lowpass");
		$params->hideParam("highpass");
		
		$this->stackid = $stackid;
	}
	
	public function generateForm()
	{
		// The size of the text fields
		$shortSize = 4;
		
		// get the html for the basic prep refine form
		$html = parent::generateForm();

		return $html;
	}
	
	// Override the basic build command function to include the ctffind flag.
	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand($postArray);

		
		return $command;
	}	
	

	
}
?>
