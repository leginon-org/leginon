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

class ImgRejector2Form extends BasicLayoutForm
{

	function __construct( $expId, $extraHTML='', $commit=True, $preset='en-a', $bestdb='', $checkdrift=True, $driftmax=5.0, $checkctf=True, $sort='rePkg', $ctfrunid='0', $resmin='7.0', $hideall=True, $checkice=False, $icemax='3.0')
	{
		parent::__construct($expId, $extraHTML);

		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//

		// Set the publications to be references on the web pages
		$pubList = array('appion');
		$this->setPublications( $pubList );
		$this->setJobType( 'reject' );
		$this->setOutputDirectory( 'reject' );
		$this->setBaseRunName( 'reject' );
		$this->setTitle( 'Hide rejected images' );
		$this->setHeading( 'Filter images to hidden' );
		$this->setExeFile( 'imgRejector2.py' );
		//$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Upload_CTF" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		$this->setUseCluster( False );

		//------ Set Parameters specific to the program that requires this new form -----//

		$params = $this->getFormParams();
		$params->addParam( "commit", $commit, "Commit results to database" );

		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "imgreject" );

		// Add each of the parameters here.
		// addParam( "key", default_value, "Label that appears in GUI")
		$params->addParam( "preset", $preset, "Preset to check values" );
		$params->addParam( "hideall", $hideall, "Hide all sibling presets" );
		$params->addParam( "checkdrift", $checkdrift, "Reject according to direct detector frame drift" );
		$params->addParam( "driftmax", $driftmax, "Maximal frame drift","angstrom" );
		$params->addParam( "checkctf", $checkctf, "Reject according to CTF fit quality");
		$params->addParam( "ctfrunid", $ctfrunid, "Specific CTF run" );
		$params->addParam( "bestdb", $bestdb, "Use best database value" );
		$params->addParam( "resmin", $resmin, "Minimal CTF resolution from software package" );
		$params->addParam( "checkice", $checkice, "Reject according to presence of ice crystal diffraction");
		$params->addParam( "icemax", $icemax, "Ice crystal ring rejection threshold" );

		$this->updateFormParams();
		$params = $this->getFormParams();
		$fieldSize = 20;

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
			$preset_default = $params->getParamDefault( 'preset' );
			if (!in_array($preset_default, $this->presetList)) {
				$session_preset_default = $this->getAlignedPreset();
				$params->setParamDefault('preset',$session_preset_default);
				if ($params->getParamValue('preset') == $preset_default) {
					$params->setParamvalue('preset',$session_preset_default);
				}
				$this->updateFormParams();
				$params = $this->getFormParams();
			} 
		}

		$ctfruns = $this->particle->getCtfRunIds($sessionId,$showHidden=False,$ctffind=False);
		if (is_array($ctfruns)) {
			$this->ctfruns = array(0=>'use all runs');
			foreach ($ctfruns as $r) {
				$this->ctfruns[$r['DEF_id']] = $r['name'];
			}
			$session_ctfrunid_default = $r['DEF_id'];
			$params->setParamDefault('ctfrunid',$session_ctfrunid_default);
			if ( $params->getParamValue('bestdb')!='on' & $params->getParamValue('ctfrunid') == "0" ) {
				$params->setParamvalue('ctfrunid',$session_ctfrunid_default);
			}
			$this->updateFormParams();
		}
	}

	// Generate a form for the parameters that are specific to this program
	// The Left side will just show the stack and model that the user selected
	// on the previous pages. This overrides the generateAdditionalFormLeft()
	// function that is found in the BasicLayoutForm class.
	public function generateAdditionalFormLeft()
	{
		$fieldSize = 10;
		$params = $this->getFormParams();
		$html.= $params->insertSelectField( "preset", $this->presetList );
		$html.= $params->insertCheckboxField( "hideall" );
		$html.= '<hr>';
		$html.= '<h4>'.$params->insertCheckboxField( "checkdrift" ).'</h4>';
		$html.= $params->insertTextFieldInRow( "driftmax", $fieldSize,'(angstroms/frame)' );
		$html.= '<hr>';
		$html.= '<h4>'.$params->insertCheckboxField( "checkctf" ).'</h4>';
		$html.= $params->insertTextFieldInRow( "resmin", $fieldSize, '(angstroms)' );
		$html.= '<p> ';
		$html.= $params->insertSelectField( "ctfrunid", $this->ctfruns );
		$html.= '<p>OR ';
		$html.= $params->insertCheckboxField( "bestdb" );
		$html.= '<hr>';
		$html.= '<h4>'.$params->insertCheckboxField( "checkice" ).'</h4>';
		$html.= $params->insertTextFieldInRow( "icemax", $fieldSize,'ice-background rms deviation ratio' );
		$html.= '<hr>';
		$html.= $params->insertCheckboxField( "commit" );


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
		return $msg;
	}

	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand( $postArray );
		$command = $this->removeCommandFlag( $command, 'sort' );

		$bestdb = $this->formParams->getParamValue( 'bestdb' );
		if ($bestdb == 'on' )	{			
				$command = $this->removeCommandFlag( $command, 'ctfrunid' );
		} 
		$flag = $this->formParams->getParamValue( 'checkdrift' );
		if ($flag !== 'on' )	{			
				$command = $this->removeCommandFlag( $command, 'driftmax' );
		} else {
				$command = $this->removeCommandFlag( $command, 'checkdrift' );
		}
		$flag = $this->formParams->getParamValue( 'checkctf' );
		if ($flag !== 'on' )	{			
				$command = $this->removeCommandFlag( $command, 'resmin' );
		} else {
				$command = $this->removeCommandFlag( $command, 'checkctf' );
		}
		$flag = $this->formParams->getParamValue( 'checkice' );
		if ($flag !== 'on' )	{			
				$command = $this->removeCommandFlag( $command, 'icemax' );
		} else {
				$command = $this->removeCommandFlag( $command, 'checkice' );
		}
		$commit  		= ($this->formParams->getParamValue('commit') == 'on' ) ? true : false;
		if (!$commit)   $command.= " --no-commit";
		return $command;
	}

	private function getAlignedPreset( )
	{
		$presets = $this->presetList;
		foreach ($presets as $p) {
			if (substr_count($p, '-') == 1) break;
		}
		return $p;
	}

}
?>
