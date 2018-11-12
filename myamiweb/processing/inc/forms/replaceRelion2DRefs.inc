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
require_once "inc/particledata.inc"; // needed to look up symmetry values
require_once "inc/summarytables.inc"; // needed to show stack and model tables

class replaceRelion2DRefs extends BasicLayoutForm
{

	function __construct( $expId, $extraHTML='', $alignStackId='')
	{
		parent::__construct($expId, $extraHTML);

		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//

		// Set the publications to be references on the web pages
		$pubList = array('appion');
		$this->setPublications( $pubList );
		$this->setJobType( 'repair' ); //Job type stored in database
		$this->setOutputDirectory( 'align' ); // the general folder this job run will be stored in, along with others of this type
		$this->setBaseRunName( 'rmaxlike' ); // a unique number will be added to this to create the run name
		$this->setTitle( 'Replace Relion2DAlign Aligned References' );
		$this->setHeading( 'Replace Relion 2D Aligned References' );
		$this->setExeFile( 'replaceRelion2DAlignedRefs.py' );
		//$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Upload_CTF" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		$this->setUseCluster( False );

		//------ Set Parameters specific to the program that requires this new form -----//

		$this->particle	= new particledata();
		$this->alignStackIds 	= $this->particle->getAlignStackIds($expId, False);
		$params = $this->getFormParams();

		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );

		// Add each of the parameters here.
		// addParam( "key", default_value, "Label that appears in GUI")
		$params->addParam( "alignstack", $alignStackId, "Select an aligned stack of particles to use" );
	}

	//Overwrite generateRunForm since this script does not need it
	public function generateRunForm(	$defrunname='', $outdir='', $description='', $showDesc=false)
	{
		return '';
	}
	// Generate a form for the parameters that are specific to this program
	// The Left side will just show the stack and model that the user selected
	// on the previous pages. This overrides the generateAdditionalFormLeft()
	// function that is found in the BasicLayoutForm class.
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		$fieldSize = 64;
		$html .= "
	    <br />
	    <H4>Stack Selection</H4>
	    <hr />";
		$alignStackId = $_GET['astack'];
		if (!$alignStackId)
			$alignoptions = $this->particle->getAlignedStackOptions($this->alignStackIds);
		else 
			$alignoptions = $this->particle->getAlignedStackOptions(array(array('alignstackid'=>$alignStackId)));
		$html .= $params->insertStackedSelectField( "alignstack", $alignoptions,'', 'relion.alignstack', $onchange );
		return $html;
	}
	
	// Override the validate function so that we can verify the appionLoopTable parameters
	public function validate( $postArray )
	{
		//$msg = parent::validate( $postArray );
		
		/*
		if ($this->getUseCluster()) {
			$remoteParamsForm = new RemoteJobParamsForm($this->outDir);
			$msg .= $remoteParamsForm->validate( $postArray );
		} else {
			$runParametersForm = new RunParametersForm();
			$msg .= $runParametersForm->validate( $postArray );
		}
		*/
		$this->updateFormParams();
		$params = $this->getFormParams();
		$alignstack = $params->getParamValue( "alignstack" );
		list($alignstackid, $alignapix, $alignboxsz, $aligntotpart) = preg_split('%\|--\|%',$alignstack);
		$astackparams = $this->particle->getAlignStackParams($alignstackid);
		return $msg;
	}

	// Override the buildCommand function to adapt to the old python command
	// that uses "-" in params and parse the stack id.
	public function buildCommand( $postArray )
	{	
		$this->updateFormParams();
		list($alignstackid, $alignapix, $alignboxsz, $aligntotpart, $path) = preg_split('%\|--\|%',$postArray['alignstack']);
		$astackparams = $this->particle->getAlignStackParams($alignstackid);
		$bits = explode($astackparams['runname'],$path);
		$postArray['outdir'] = $bits[0];
		$postArray['runname'] = $astackparams['runname'];
		$command = parent::buildCommand( $postArray );
		
		$params = $this->getFormParams();
		
		// Determine if we should use the stack or alignedstack id
		$command = $this->removeCommandFlag( $command, "alignstack" );

		$alignstack = $params->getParamValue( "alignstack" );
		$command = $this->addCommandFlag( $command, "alignstack", "alignstack", $alignstackid );
		
		return $command;		
	}
}
?>
