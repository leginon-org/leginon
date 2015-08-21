<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */
// This class displays a form used to create a command similar to the following:
// uploadExternalRefine.py --rundir=/ami/data17/appion/11jan11a/recon/external_package_test 
// --runname=external_package_test --description="testing out external upload on 11jan11 data, emanrecon11, first iteration" 
// --projectid=224 --no-commit --expId=8397 --uploadIterations=1,2,3,4,5 --stackid=127 
// --modelid=19 --mass=3800 --apix=2.74 --box=160 --numberOfReferences=1 --numiter=1 --timestamp=11jul18z 
// --symid=25

require_once "basicLoopForm.inc";

class makeDEAlignedSum extends BasicLoopForm
{
	
	// This is the constructor function. It is called as soon as this class is 
	// instantiated with a line like: $form = new CoolFeatureForm($expId, $extraHTML).
	// The first 2 parameters are needed for the BasicLayoutForm class that this class extends from.  
	// The rest of the parameters are specific to this form.
	
	function __construct( $expId, $extraHTML='', $alignment_correct='1', $alignment_quanta='3', $radiationdamage_compensate='1', $border='',
	$hackcopy='', $usequeue='', $queue_style='', $queue_scratch='', $njobs='', $queue_ppn='2', $queue_name='', $queue_memory='4', $handlefiles='copy',
	$defects_columns='', $defects_rows='', $darkreference_transform='', $gainreference_transform='', $output_transform='', $wrapper='' ) 
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
		// Job Type should be unique to Appion. Used in the database to determine the type of job being run.
		$this->setJobType( 'dealignedframes' ); 
		// The name of the folder that all runs of this job type will be stored in.
		$this->setOutputDirectory( 'framealignment' );  
		// A portion of the run name that will be common (by default) to all runs of this job type. A unique number is appended to individual run names.
		$this->setBaseRunName( 'fullframe' ); 
		// The title on the web page for this feature.
		$this->setTitle( 'Launcher for full frame DE aligner' ); 
		// The Heading on the web page for this feature.		
		$this->setHeading( 'Create Aligned and Dose Compensated Frame Sums' ); 
		// The name of the python executable file that this GUI corresponds to. It should be based on the AppionLoop class and located in the myami/appion/bin folder.
		$this->setExeFile( 'makeDEAlignedSum.py' );
		// A URL corresponding to a wiki page in the Appion User Guide with information on running this feature.  
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
		// True to activate "test single image" field of Appion Loop parameters.
		$this->setTestable( True ); 
		// The output directory will be created in the Appion run directory rather than Leginon.
		$this->setUseLegOutDir( False );
		// Flag to hide the description field of the run parameters. True enables the description field.
		$this->setShowDesc( True ); 
		// Flag to use the cluster parameter form rather than the run parameter form.
		// Reconstructions and remote jobs use the cluster parameters, generic single processor jobs use run parameters.
		// Set to True to use Cluster Parameters
		$this->setUseCluster( False );
		
		$params = $this->getFormParams();

		// Wrapper is currently defaulted from config.php without knowing what cluster
		// the job is going to be submitted to.  This is not the best to do.		
		// getAppionWrapper function comes from processing/inc/processing.inc
		$wrapper = ($wrapper) ? $wrapper: getAppionWrapper();

		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "makeDEAlignedSum" );
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
		$params->addParam( "defects_columns", $defects_columns, "Defective column numbers" );
		$params->addParam( "defects_rows", $defects_rows, "Defective row numbers" );
		$params->addParam( "darkreference_transform", $darkreference_transform, "Transformation of dark reference to frames" );
		$params->addParam( "gainreference_transform", $gainreference_transform, "Transformation of bright reference to frames" );
		$params->addParam( "output_transform", $output_transform, "Transformation of final summed image" );
		$params->addParam( "wrapper", $wrapper, "Environment wrapper to pass into queue jobs" );
	}
	
	// Generate a form for the parameters that are specific to this program 
	// The Left side will just show the stack and model that the user selected
	// on the previous pages. This overrides the generateAdditionalFormLeft() 
	// function that is found in the BasicLayoutForm class.
	public function generateAdditionalFormRight($displayAdvanced=False)
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 15;
		
		$html .= "
	    <br />
	    <H4>DE Aligner Params</H4>
	    <hr />";
		
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
			$html.= $params->insertTextField( "defects_columns", $fieldSize );
			$html.= $params->insertTextField( "defects_rows", $fieldSize );
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

	public function buildCommand( $postArray )
	{
		$command   = parent::buildCommand( $postArray );
		return $command." ";
		
	}	

}

?>
