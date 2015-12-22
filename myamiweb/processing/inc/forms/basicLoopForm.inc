<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

//--------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------
require_once "inc/processing.inc";
require_once "basicForm.inc";
require_once "inc/particledata.inc";
require_once "inc/forms/basicLayoutForm.inc";
require_once "inc/forms/appionLoopTable.inc";
require_once "inc/forms/runParametersForm.inc";


class BasicLoopForm extends BasicLayoutForm
{

	function __construct( $expId, $errorHTML='', $infoHTML='' ) 
	{
		parent::__construct($expId, $errorHTML, $infoHTML);	
	}
	
	// Override this to output the html required to display program specific parameters
	// This html will be displayed directly below the appion loop params on the left hand side of the form
	public function generateAdditionalFormLeft() {
		
		// check if coming directly from a session
		if ( $this->expId ) {
			$sessionId = $this->expId;
		} else {
			$sessionId = $_POST['sessionId'];
		}
		
		// Get the session data
		$projectId   = getProjectId();
		$sessiondata = getSessionList( $projectId, $sessionId );
		
		// Presets
		// Create a dictionary of preset value=>desc. Desc appears in the gui, value is returned in the code in a selection box.
		if ( !empty( $sessiondata['presets']) ) {
			$presetList = array_combine( $sessiondata['presets'], $sessiondata['presets'] );			
		}

		// Get the max tilt angle which determines if the tilt angle select control is displayed
		$particle = new particledata();
		$maxang = $particle->getMaxTiltAngle( $this->expId );	

		// Set nowait according to the timestamp of the most recent non-processed image
		$nowait_default =  $particle->isSessionRunning( $this->expId );

		// Add the Appion Loop Form
		$appionLoopTable = new AppionLoopTable( $checkimage='unrejected', $nowait=$nowait_default, $imgorder='normal', $limit='',$tiltangle='', $maxtiltangle=$maxang, $apcontinue='1',
		$commit='on', $presetList=$presetList, $preset="en", $testimage='', $testfilename='' );
		
		// Only hide advanced parameters if there is not an advanced user logged in.
		// Modify user profile to set to an advanced user. 
		// NOTE: this assumes the Appion user name and the username that is used to log in to the processing page are the same.
		// We may want to change that someday.
		$displayAdvanced = $_SESSION['advanced_user'];
		$html .= $appionLoopTable->generateForm( $displayAdvanced=$displayAdvanced );

		return $html;
	}
	
	// Override the validate function so that we can verify the appionLoopTable parameters
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		
		$appionLoopTable = new AppionLoopTable();
		$msg .= $appionLoopTable->validate( $postArray );
		
		return $msg;
	}
	
	// Override buildCommand so that we can call it from AppionLoopTable
	public function buildCommand( $postArray )
	{	
		$command = parent::buildCommand( $postArray );
		
		// add params from Appion Loop form
		$appionLoopTable = new AppionLoopTable();
		$command .= $appionLoopTable->buildCommand( $postArray );
		
		return $command;		
	}
}

?>
