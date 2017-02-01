<?php

/**
 *	The Leginon software is Copyright under
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */
// This class displays a form used to create a command similar to the following:
// uploadCtfEstimates.py \
// -f /emg/sw/myami/appion/docker/centos6/ctfdata-session0003.dat \
// -s artemia2 -p 1 --commit

require_once "basicLayoutForm.inc"; //includes the BasicLayoutForm class that this class extends
require_once "appionLoopTable.inc"; //includes the BasicLayoutForm class that this class extends
require_once "inc/particledata.inc"; // needed to look up symmetry values
require_once "inc/summarytables.inc"; // needed to show stack and model tables

class TransferCtf extends BasicLayoutForm
{

	function __construct( $expId, $extraHTML='', $frompreset='en', $preset='en', $bestdb='on', $sort='res50', $ctfrunid='0')
	{
		parent::__construct($expId, $extraHTML);

		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//

		// Set the publications to be references on the web pages
		$pubList = array('appion');
		$this->setPublications( $pubList );
		$this->setJobType( 'transfer' );
		$this->setOutputDirectory( 'ctf' );
		$this->setBaseRunName( 'tctf' );
		$this->setTitle( 'Transfer CTF Estimates' );
		$this->setHeading( 'Transfer CTF Estimates' );
		$this->setExeFile( 'transferCtfResults.py' );
		//$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Upload_CTF" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		$this->setUseCluster( False );

		//------ Set Parameters specific to the program that requires this new form -----//

		$params = $this->getFormParams();

		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );

		// Add each of the parameters here.
		// addParam( "key", default_value, "Label that appears in GUI")
		$params->addParam( "frompreset", $frompreset, "Preset to copy CTF and viewer status from" );
		$params->addParam( "preset", $preset, "Preset to recieve the values" );
		$params->addParam( "ctfrunid", $ctfrunid, "Specific CTF run" );
		$params->addParam( "bestdb", $bestdb, "Use best database value" );
		$params->addParam( "sort", $sort, "sort method" );

		$this->updateFormParams();
		$params = $this->getFormParams();
		$fieldSize = 64;

		// check if coming directly from a session
		if ( $this->expId ) {
			$sessionId = $this->expId;
		} else {
			$sessionId = $_POST['sessionId'];
		}
		
		// Get the session data
		$projectId   = getProjectId();
		$sessiondata = getSessionList( $projectId, $sessionId );
		// Appion query
		$this->particle = new particledata();		
		// Presets
		// Create a dictionary of preset value=>desc. Desc appears in the gui, value is returned in the code in a selection box.
		if ( !empty( $sessiondata['presets']) ) {
			$this->presetList = array_combine( $sessiondata['presets'], $sessiondata['presets'] );			
		}
		$this->sortList = array('res80'=>'Resolution 0.8 critera','res50'=>'Resolution 0.5 criteria','resPkg'=>'Software Resolution estimate','maxconf'=>'Maximum confidence value');
		$ctfruns = $this->particle->getCtfRunIds($sessionId,$showHidden=False,$ctffind=False);
		$this->ctfruns = array(0=>'use all runs');
		if (is_array($ctfruns)) {
			foreach ($ctfruns as $r) {
				$this->ctfruns[$r['DEF_id']] = $r['name'];
			}
		}
	}

	// Generate a form for the parameters that are specific to this program
	// The Left side will just show the stack and model that the user selected
	// on the previous pages. This overrides the generateAdditionalFormLeft()
	// function that is found in the BasicLayoutForm class.
	public function generateAdditionalFormLeft()
	{
		$params = $this->getFormParams();
		$html.= $params->insertSelectField( "frompreset", $this->presetList );
		$html.= $params->insertSelectField( "preset", $this->presetList );
		$html.= '<hr>';
		$html.= '<h4> CTF Estimation Selection</h4>';
		$html.= $params->insertCheckboxField( "bestdb" );

		$html.= $params->insertSelectField( "sort", $this->sortList );
		$html.= '<p>OR ';
		$html.= $params->insertSelectField( "ctfrunid", $this->ctfruns );
		return $html;
	}

	public function validate( $postArray )
	{
		$this->formParams->getPostedValues( $postArray );
		$msg = $this->formParams->validate();
		if ($postArray['bestdb']!='on' & $postArray['ctfrunid']==0 )
			$msg .= '<B>ERROR:</B>Use either best run or specify a run. You have chosen neither.<br/>';	
		if ($postArray['bestdb']=='on' & $postArray['ctfrunid']!=0 )
			$msg .= '<B>ERROR:</B>Use either best run or specify a run, not both.<br/>';	
		if ($postArray['preset']==$postArray['frompreset'] & $postArray['ctfrunid']!=0 )
			$msg .= '<B>ERROR:</B>Transferring CTF result of a single run to the same preset accomplish nothing<br/>';	
		return $msg;
	}

	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand( $postArray );

		$bestdb = $this->formParams->getParamValue( 'bestdb' );
		if ($bestdb == 'on' )	{			
				$command = $this->removeCommandFlag( $command, 'ctfrunid' );
		} else {
				$command = $this->removeCommandFlag( $command, 'sort' );
		}
		return $command;
	}
}
?>
