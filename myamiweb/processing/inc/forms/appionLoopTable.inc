<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicForm.inc";
require_once "inc/particledata.inc";
require_once "inc/processing.inc";


class AppionLoopTable extends BasicForm
{
	protected $presetList;
	protected $maxtiltangle;
	
	function __construct( $checkimage='', $nowait='', $imgorder='', $limit='',$tiltangle='',$maxtiltangle='', $apcontinue='',
		$commit='', $presetList='', $preset='', $testimage='', $testfilename='' ) 
	{
		parent::__construct();
		$this->presetList = $presetList;
		$this->maxtiltangle = $maxtiltangle;
		
		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );
				
		$params->addParam( "checkimage", $checkimage, "Images to process" );
		$params->addParam( "nowait", $nowait, "Wait for more images after finishing" );
		$params->addParam( "limit", $limit, "Max number of images to process" );
		$params->addParam( "imgorder", $imgorder, "Image order" );
		$params->addParam( "tiltangle", $tiltangle, "Tilt Angle" );
		$params->addParam( "apcontinue", $apcontinue, "apcontinue" );
		$params->addParam( "commit", $commit, "Commit results to database" );
		$params->addParam( "preset", $preset, "Preset" );
		$params->addParam( "testimage", $testimage, "testimage" );
		$params->addParam( "testfilename", $testfilename, "testfilename" );		
	}
			
	public function generateForm( $displayAdvanced=True )
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 5;
		
		$html.=  "<!-- BEGIN Appion Loop Param -->\n";

		// Presets
		if ($this->presetList && count($this->presetList) > 1) {
			$html.= $params->insertSelectField( "preset", $this->presetList );
		} elseif ( !empty($this->presetList) ) {			
			//only one preset
			$preset = key( $this->presetList );
			$html.= "<B>Preset:</B>&nbsp;&nbsp;".$preset."\n\n";
			$html.= "<input type='hidden' name='preset' VALUE=".$preset."><br/>\n";
		} else {
			//no presets
			$html.= "<input type='hidden' name='alldbimages' VALUE=1>\n";
			$html.= "<I>No presets for this session<br/>\n"
				."processing ALL images</I><br/>\n";
		}
		$html.= $params->insertCheckboxField( "nowait" );
		$html.= "<hr/>\n";

		//
		// STARTING ADVANCED SECTION
		//
		if ( !$displayAdvanced ) {
			$html.= "<a id='Advanced_Loop_Options_toggle' href='javascript:toggle(\"Advanced_Loop_Options\");' style='color:blue'>";
			$html.= "Show Advanced Options</a><br/>\n";
			$html.= "<div id='Advanced_Loop_Options' style='display: none'>\n";
		}
	
		// 5 degrees is the cutoff for the accuracy of the goniometer when it is set to zero.
		if ($this->maxtiltangle > 5) {
			$tiltOptions = array( 'all'=>'all tilt angles', 'notilt'=>'zero tilt angles only','hightilt'=>'large tilt angles only', 
								'lowtilt'=>'small tilt angles only', 'minustilt'=>'negative tilt angles only', 'plustilt'=>'positive tilt angles only');
			
			$html.= $params->insertSelectField( "tiltangle", $tiltOptions );
		} else {
			$html.= "<input type='hidden' name='tiltangle' value='all'>\n";
		}
	
		$html.= $params->insertTextField( "limit", $fieldSize );	
		
		$html.= "<I>Images to process:</I><br />\n";
		$html.= $params->insertRadioField("checkimage", "unrejected", "Do not process hidden or rejected images");	
		$html.= $params->insertRadioField("checkimage", "all", "All images independent of status");	
		$html.= $params->insertRadioField("checkimage", "best", "Exemplar and keep images only");	
	
		$html.= "<I>Image order:</I><br />\n";
		$html.= $params->insertRadioField("imgorder", "normal", "Forward");	
		$html.= $params->insertRadioField("imgorder", "reverse", "Reverse");	
		$html.= $params->insertRadioField("imgorder", "shuffle", "Shuffle");	
		
		$html.= "<I>Continuation:</I><br />\n";		
		$html.= $params->insertRadioField("apcontinue", "1", "Continue unfinished run", "(default)");	
		$html.= $params->insertRadioField("apcontinue", "0", "Reprocess all images");	
		
		$html.= "<hr/>\n";
		$html.= $params->insertCheckboxField( "commit" );
		
		//
		// ENDING ADVANCED SECTION 1
		//
		// if this is not an advanced user, end the advanced section
		if ( !$displayAdvanced ) {
			$html.= "</div>\n";
		}
		$html.= "<hr/>\n";
		$html.= "<!-- END Appion Loop Param -->\n";
			
		return $html;
	}	
	
	// Override the validate function to add more complex validations than are available in the formValidator class.
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		
		$params = $this->getFormParams();
		
		if ( $params->getParamValue('testimage') == "on" &&  $params->getParamValue('testfilename') == '' ) {
			$msg .= "<B>Error:</B> Specify an mrc file to test these parameters.";
		} elseif ($postArray['sessionname'] && !$postArray['preset'] && !$postArray['alldbimages'] ) {
			$msg .= "<B>Error:</B> Select an image preset.";
		}
		
		return $msg;
	}	
	
	// Override the buildCommand function because we need to set multiple flags per param
	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand( $postArray );
		$params = $this->getFormParams();

		$commit  		= ($params->getParamValue('commit') == 'on' ) ? true : false;
		$nowait  		= ($params->getParamValue('nowait') == "on" ) ? false : true;
		$shuffle 		= ($params->getParamValue('imgorder') == "shuffle" ) ? true : false;
		$reverse 		= ($params->getParamValue('imgorder') == "reverse" ) ? true : false;
		$apcontinue 	= $params->getParamValue('apcontinue');	
		$tiltangle  	= $params->getParamValue('tiltangle');
		$checkimage 	= $params->getParamValue('checkimage');
		$testimage 		= $params->getParamValue('testimage');
		$testfilename 	= $params->getParamValue('testfilename');
		
		$command = $this->removeCommandFlag( $command, 'nowait' );
		$command = $this->removeCommandFlag( $command, 'imgorder' );
		$command = $this->removeCommandFlag( $command, 'checkimage' );
		$command = $this->removeCommandFlag( $command, 'testimage' );
		$command = $this->removeCommandFlag( $command, 'testfilename' );
		$command = $this->removeCommandFlag( $command, 'apcontinue' );
		
		if ( $checkimage == "unrejected" ) {
			$norejects = 1;
			$bestimages = 0;
		} elseif ( $checkimage == "best" ) {
			$norejects = 0;
			$bestimages = 1;
		} else {
			$norejects = 0;
			$bestimages = 0;
		}		
	
		if ( $testimage == "on" ) {
			if ( $testfilename ) $testimage = trim( $testfilename );
			$testimage = preg_replace("% %",",", $testimage);
			$testimage = preg_replace("%,,%",",", $testimage);
			$apcontinue = false;
		}
	
		// CREATE COMMAND
		$command .= " ";
		$command .= " --projectid=".getProjectId()." ";
		$command .= " --session=".$_POST['sessionname'];
		
		if ($norejects) $command.= " --no-rejects";
		if ($bestimages)$command.= " --best-images";
		if ($nowait) 	$command.= " --no-wait";
		if (!$commit)   $command.= " --no-commit";
		if ($reverse)   $command.= " --reverse";
		if ($shuffle)   $command.= " --shuffle";
	
		if ($tiltangle == '' || $tiltangle == 'all') { 
			$command = $this->removeCommandFlag( $command, 'tiltangle' );
		} 
		
		if (!$apcontinue) {
			$command.=" --no-continue";
		} else { 
			$command.=" --continue";
		}
		
		if ($testimage) {
			$command.= " --mrclist=$testimage ";
			$command = $this->removeCommandFlag( $command, 'preset' );
		}
		
		return $command." ";
	}	
	
}
?>
