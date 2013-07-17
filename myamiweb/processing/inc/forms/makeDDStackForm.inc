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
	function __construct( $align='', $defergpu='', $bin=1, $nokeepstack='' ) 
	{
		parent::__construct();
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "makeDDStack" );
				
		$params->addParam( "align", $align, "align" );
		$params->addParam( "defergpu", $defergpu, "defer gpu processing" );
		$params->addParam( "bin", $bin, "binning" );
		$params->addParam( "no_keepstack", $nokeepstack, "remove generated stack after uploading aligned sum image" );
		
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
		$html.= $params->insertCheckboxField( "no_keepstack" );
		$html.= $params->insertTextFieldInRow( "bin", $fieldSize );
		
		return $html;
	}	
	
	// Override the parent build Commnad function to accomodate the "-" in the no-keepstack flag. 
	// Dashes are not parsed correctly in the help.js file, so I have replaced them with an "_" in this file.
	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand($postArray);
						
		$command = $this->addCommandFlag($command, "no-keepstack", "no_keepstack" );

		// remove params not needed in command
		$command = $this->removeCommandFlag($command, "no_keepstack" );
		
		return $command;
	}		
	
}
?>
