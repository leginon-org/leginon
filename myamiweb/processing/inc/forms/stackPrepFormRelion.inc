<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "stackPrepForm.inc";
require_once "inc/particledata.inc";

class StackPrepFormRelion extends StackPrepForm
{
	function __construct( $stackid='', $lastParticle='', $lowpass='', $highpass='', $bin='', $reconiterid='', $emaninit='', $ctffindonly='', $ctftilt='', $paramonly='',$relion_version='1.4' ) 
	{
		parent::__construct($lastParticle, $lowpass, $highpass, $bin);
		$params = $this->getFormParams();

		$this->relion_versions = array('1.4','2.0');						
		$params->addParam( "relion_version", $relion_version, "relion_version" );

		$params->addParam( "paramonly", $paramonly, "Only create Relion star file, not the stack");
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
		$params = $this->getFormParams();

		$html .= $params->insertCheckboxField( "paramonly");
		$html.= "<!-- START Selector -->\n";
		$onchange = "switchDefaults(this.value)";
		for($i=0;$i<count($this->relion_versions);$i++)
			{
				$ddoptions[$this->relion_versions[$i]] = $this->relion_versions[$i];
			}

		$html .= $params->insertStackedSelectField("relion_version",$ddoptions,'','',$onchange);

		$html .= "<br />";
		$html.= "<!-- END Selector -->\n";
			
		
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
