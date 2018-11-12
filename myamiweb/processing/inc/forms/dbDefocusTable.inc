<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicForm.inc";

class dbDefocusTable extends BasicForm
{

	function __construct ($expId, $bestdb=true, $nominal='' )
	{
		parent::__construct();
		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );
		
		$params->addParam( "bestdb", $bestdb, "Use best values from Database" );
		$params->addParam( "nominal", $nominal, "Override Nominal Value (in &mu;m)" );
	}

	public function generateForm( $displayAdvanced=False )
	{
		$fieldSize = 5;	
		$this->updateFormParams();
		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();
		$html.= "<!-- Start db Defocus options -->\n";
		$html.= $params->insertCheckboxField( "bestdb" );
		$html.= $params->insertTextField( "nominal", $fieldSize );
		$html.= "<!-- END db Defocus options -->\n";
			
		return $html;
	}

	public function validate($postArray )
	{
		$msg = parent::validate( $postArray );
		$params = $this->getFormParams();
		$nominalv = $params->getParamValue('nominal');
		$bestdbv = $params->getParamValue('bestdb');
		if ( $nominalv && $bestdbv == 'on' )
			$msg .= "<B>Error:</B> Either use best results from database or give nomial focus";
		return $msg;
	}
}

?>
