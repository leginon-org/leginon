<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */
// This class displays a form used to create a command similar to the following:
// uploadExternalRefine.py --rundir=/ami/data17/appion/11jan11a/recon/external_package_test 
// --runname=external_package_test --description="testing out external upload on 11jan11 data, emanrecon11, first iteration" 
// --projectid=224 --no-commit --expId=8397 --uploadIterations=1,2,3,4,5 --stackid=127 
// --modelid=19 --mass=3800 --apix=2.74 --box=160 --numberOfReferences=1 --numiter=1 --timestamp=11jul18z 
// --symid=25

require_once "basicForm.inc";

class DEAlignTable extends BasicForm
{
	
	// This is the constructor function. It is called as soon as this class is 
	// instantiated with a line like: $form = new CoolFeatureForm($expId, $extraHTML).
	// The first 2 parameters are needed for the BasicLayoutForm class that this class extends from.  
	// The rest of the parameters are specific to this form.
	
	function __construct( $expId, $extraHTML='', $alignment_correct='1', $alignment_quanta='3', $radiationdamage_compensate='1', $border='70',
	$hackcopy='', $usequeue='on', $queue_style='', $queue_scratch='', $njobs='4', $queue_ppn='2', $queue_name='', $queue_memory='4', $handlefiles='copy',
	$bad_cols='', $bad_rows='', $darkreference_transform='', $gainreference_transform='', $output_transform='', $wrapper='', $alignlabel='a' ) 
	{
		// You must first call the parent class(BasicLayoutForm) constructor. 
		// Pass it the $expId and $extraHTML variables. Errors and test results are passed through $extraHTML.
		
		parent::__construct($expId, $extraHTML);

		// Selections		
		$this->switchList = array(0,1);
		$this->handlefilesList = array('copy'=>'copy','link'=>'link','direct'=>'direct');
		$this->queue_styleList = array('PBS'=>'PBS','MOAB'=>'MOAB','SLURM'=>'SLURM');
		//------ Set Parameters for the parent class, BasicLoopForm or BasicLayoutForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('appion'); // The publication reference key that you added to publicationList.inc
		$this->setPublications( $pubList );


		// Wrapper is currently defaulted from config.php without knowing what cluster
		// the job is going to be submitted to.  This is not the best to do.		
		// getAppionWrapper function comes from processing/inc/processing.inc
		$wrapper = ($wrapper) ? $wrapper: getAppionWrapper();

		$params = $this->getFormParams();
		// Add each of the parameters here. 
		// addParam( "key", default_value, "Label that appears in GUI")
		$params->addParam( "alignment_correct", $alignment_correct, "Align Correct Switch" );
		$params->addParam( "radiationdamage_compensate", $radiationdamage_compensate, "Radiation Damage Compensation Switch" );
		$params->addParam( "alignment_quanta", $alignment_quanta, "N frames to average for rolling average (odd)" );
		$params->addParam( "border", $border, "Border" );
		$params->addParam( "hackcopy", $hackcopy, "Hackcopy" );
		$params->addParam( "usequeue", $usequeue, "Use Queue" );
		$params->addParam( "queue_style", $queue_style, "Queue Style" );
		$params->addParam( "queue_scratch", $queue_scratch, "Queue Scratch" );
		$params->addParam( "njobs", $njobs, "Number of Jobs" );
		$params->addParam( "queue_ppn", $queue_ppn, "Queue ppn" );
		$params->addParam( "queue_memory", $queue_memory, "Queue memory" );
		$params->addParam( "queue_name", $queue_name, "Queue name" );
		$params->addParam( "handlefiles", $handlefiles, "File handling" );
		$params->addParam( "bad_cols", $bad_cols, "Bad column numbers" );
		$params->addParam( "bad_rows", $bad_rows, "Bad row numbers" );
		$params->addParam( "darkreference_transform", $darkreference_transform, "Transformation of dark reference to frames" );
		$params->addParam( "gainreference_transform", $gainreference_transform, "Transformation of bright reference to frames" );
		$params->addParam( "output_transform", $output_transform, "Transformation of final summed image" );
		$params->addParam( "wrapper", $wrapper, "Environment wrapper to pass into queue jobs" );
		$params->addParam( "alignlabel", $alignlabel, "label for uploaded aligned sum image" );
	}
	
	// Generate a form for the parameters that are specific to this program 
	// The Left side will just show the stack and model that the user selected
	// on the previous pages. This overrides the generateAdditionalFormLeft() 
	// function that is found in the BasicLayoutForm class.
	public function generateForm( $displayAdvanced=False )
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 15;
		
		$html .= "
	    <br />
	    <H4>DE Aligner Params</H4>
	    <hr />";
		
		$html.= $params->insertTextField( "alignlabel", 2 );
		$html.= $params->insertSelectField( "alignment_correct", $this->switchList );
		$html.= $params->insertSelectField( "radiationdamage_compensate", $this->switchList );
		$html.= $params->insertTextField( "alignment_quanta", $fieldSize );
		$html.= $params->insertTextField( "border", $fieldSize );
		
		$html.= $params->insertSelectField( "handlefiles", $this->handlefilesList );
		
		$html.= $params->insertCheckboxField( "usequeue");
		$html.= $params->insertTextField( "queue_scratch", 35 );
		$html.= $params->insertTextField( "njobs", $fieldSize );
		$html.= $params->insertTextField( "queue_ppn", $fieldSize );
		$html.= $params->insertTextField( "queue_memory", $fieldSize );
		$html.= $params->insertTextField( "queue_name", $fieldSize );
		$html.= $params->insertSelectField( "queue_style", $this->queue_styleList );
		
		//
		// STARTING ADVANCED SECTION
		//
		if ( !$displayAdvanced ) {
			// The javascript toggle makes what is within <div > show up
			$html.= "<a id='Advanced_DEAlign_Options_toggle' href='javascript:toggle(\"Advanced_DEAlign_Options\");' style='color:blue'>";
			$html.= "Show Advanced Options</a><br/>\n";
			$html.= "<div id='Advanced_DEAlign_Options' style='display: none'>\n";
		}
			$html.= $params->insertTextField( "bad_cols", $fieldSize );
			$html.= $params->insertTextField( "bad_rows", $fieldSize );
			$html.= $params->insertCheckboxField( "hackcopy" );
			$html.= $params->insertTextField( "darkreference_transform", $fieldSize );
			$html.= $params->insertTextField( "gainreference_transform", $fieldSize );
			$html.= $params->insertTextField( "output_transform", $fieldSize );
			$html.= $params->insertTextField( "wrapper", 25 );

		//
		// ENDING ADVANCED SECTION
		//
		return $html;
	}	

	// Override the validate function so that we can verify parameters from this subform
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		
		$params = $this->getFormParams();
		
		
		$usequeue = $params->getParamValue('usequeue');
		$njobs = $params->getParamValue('njobs');
		$handlefiles = $params->getParamValue('handlefiles');
		$queue_scratch = $params->getParamValue('queue_scratch');
		if ( $usequeue == "")
		{
			$msg .= "<B>Error:</B> Running without job queuing is not implemented";
		}

		if ( $usequeue != "" && empty($njobs) )
		{
			$msg .= "<B>Error:</B> Number of jobs must be specified when using queue";
		}

		if ( $handlefiles != "direct" && empty($queue_scratch) )
		{
			$msg .= "<B>Error:</B> Scratch directory must be specified when files are not used directly";
		}
		return $msg;
	}

	// not need to redefine buildCommand
}

?>
