<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicLoopForm.inc";

class MakeDDStackForm extends BasicLoopForm

{
	function __construct(  $expId, $errorHTML='', $infoHTML='',$align='', $defergpu='', $bin=1, $nokeepstack='', $ddstartframe=0, $ddnframe='',$alignoffset=7,$alignbfactor=1000,$alignccbox=96,$alignlabel='a' ) 
	{
		parent::__construct($expId, $errorHTML, $infoHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('appion');
		$this->setPublications( $pubList );
		$this->setJobType( 'makeddrawframestack' );
		$this->setOutputDirectory( 'ddstack' );
		$this->setBaseRunName( 'ddstack' );
		$this->setTitle( 'makeDDRawFrameStack.py Launcher' );
		$this->setHeading( 'Create a Direct Detector Frame Stack' );
		$this->setExeFile( 'makeDDRawFrameStack.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
		$this->setTestable( True ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( True ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "makeDDStack" );
				
		$params->addParam( "align", $align, "align" );
		$params->addParam( "defergpu", $defergpu, "defer gpu processing" );
		$params->addParam( "bin", $bin, "binning" );
		$params->addParam( "no_keepstack", $nokeepstack, "remove generated stack after uploading aligned sum image" );
		$params->addParam( "ddstartframe", $ddstartframe, "start frame" );
		$params->addParam( "ddnframe", $ddnframe, "total frames" );
		$params->addParam( "alignoffset", $alignoffset, "frame offset" );
		$params->addParam( "alignbfactor", $alignbfactor, "b factor in motioncorr" );
		$params->addParam( "alignccbox", $alignccbox, "CC search boxsize in motioncorr" );
		$params->addParam( "alignlabel", $alignlabel, "append label to aligned image" );
		// Validations
		$params->addValidation( "bin", "num" );
	}
		
	public function generateAdditionalFormRight()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 4;
		
		$html .= "<b>Make DD stack params:</b><br />\n";
		
		$html.= $params->insertCheckboxField( "align" );
		$html.= $params->insertCheckboxField( "defergpu" );
		$html.= $params->insertCheckboxField( "no_keepstack" );
		$html.= "<br/><br/>\n";
		$html.= $params->insertTextFieldInRow( "bin", $fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "alignlabel", $fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "alignoffset",$fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "alignbfactor", $fieldSize );
		$html.= "<br/>\n";
		$html.= $params->insertTextFieldInRow( "alignccbox",$fieldSize );
		$html.= "<br/><br/>Frames used for sum image after alignment: <br/>\n";
		$html.= $params->insertTextFieldInRow( "ddstartframe", $fieldSize );
		$html.= $params->insertTextFieldInRow( "ddnframe", $fieldSize );
		
		return $html;
	}	
	
	// Override the parent build Commnad function to accomodate the "-" in the no-keepstack flag. 
	// Dashes are not parsed correctly in the help.js file, so I have replaced them with an "_" in this file.
	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand($postArray);
						
		$command = $this->addCommandFlag($command, "no-keepstack", "no_keepstack" );

		// if we are not testing an image, add the parellel flag
		if ( !($postArray['testimage']=="on") ) {
			$command.= " --parallel";
		}
		
		// remove params not needed in command
		$command = $this->removeCommandFlag($command, "no_keepstack" );
		
		return $command;
	}		
	
}
?>
