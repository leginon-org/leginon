<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicForm.inc";
require_once "inc/particledata.inc";
require_once "inc/processing.inc";

class CtfRunTable extends BasicForm
{
	protected $runList; //array of (id=>runname)

	function __construct ($runList='', $run='' )
	{
		parent::__construct();
		$this->runList = $runList;
		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );
		
		$params->addParam( "ctfrunID", $run, "Ctf Run" );
	}

	public function generateForm( $displayAdvanced=False )
	{
		$this->updateFormParams();
		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();
		
		// Presets
		$html.= "<!-- Start Preset Selector -->\n";
		$html.= "<B>Select Run:</B>&nbsp;&nbsp;".$id."\n\n";
		if ($this->runList && count($this->runList) > 1) {
			$html.= $params->insertSelectField( "ctfrunID", $this->runList );
		} elseif ( !empty($this->runList) ) {			
			//only one run
			$id = key( $this->runList );
			$html.= $params->insertTextField( "ctfrunID", $this->runList[$id],$id,$enable=false );
		} else {
			//no results
			$html.= $params->insertHiddenField( "ctfrunID", null );
			$html.= "<I>No ctfruns for this session<br/>\n";
		}
		$html.= "<!-- END Preset Selector -->\n";
			
		return $html;
	}
}

?>
