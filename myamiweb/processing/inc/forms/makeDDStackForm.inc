<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicForm.inc";

class MakeDDStackForm extends BasicForm

{
	function __construct( $align='', $defergpu='', $bin=2 ) 
	{
		parent::__construct();
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "makeDDStack" );
				
		$params->addParam( "align", $align, "align" );
		$params->addParam( "defergpu", $defergpu, "defer gpu processing" );
		$params->addParam( "bin", $bin, "binning" );
		
		// Validations
		//$params->addValidation( "numpart", "req" );
	}
		
	public function generateForm()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 2;
		
		$html .= "<b>Make DD stack params:</b><br />\n";
		
		$html.= $params->insertCheckboxField( "align" );
		$html.= $params->insertCheckboxField( "defergpu" );
		$html.= $params->insertTextFieldInRow( "bin", $fieldSize );
		
		return $html;
	}	
	
}
?>
