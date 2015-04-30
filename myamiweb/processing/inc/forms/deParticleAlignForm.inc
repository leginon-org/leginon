<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicLayoutForm.inc"; //includes the BasicLayoutForm class that this class extends
require_once "inc/particledata.inc"; // needed to look up symmetry values

class deParticleAlignForm extends BasicLayoutForm
{
	protected $stackIds;
	
	// Set Default values in the constructor
	function __construct( $expId, $extraHTML='', $stackId='', $darkreference_transform='3', $gainreference_transform='3', $defects_columns='', $defects_rows='', 
		$alignment_correct='1', $boxes_transform='2', $radiationdamage_compensate='1', $radiationdamage_exposurerate='2.92', $radiationdamage_apix='1.25813', 
		$output_rotation='90', $alignment_target='boxes' ) 
	{
		parent::__construct($expId, $extraHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('departicle'); // Keys are found in publicationList.inc
		$this->setPublications( $pubList ); // list of references to display
		
		$this->setJobType( 'framealignment' ); //Job type stored in database
		$this->setOutputDirectory( 'framealignment' ); // the general folder this job run will be stored in, along with others of this type
		$this->setBaseRunName( 'DEaligner' ); // a unique number will be added to this to create the run name
		$this->setTitle( 'DE Particle Alignment' ); // Shows up in the browser tab
		$this->setHeading( 'DE Particle Alignment' ); // shows at the top of the processing page
		$this->setExeFile( 'de_aligner.py' ); // added to the command string
		$this->setGuideURL( "http://http://emg.nysbc.org/redmine/projects/appion/wiki/Run_DE_Particle_Frame_Alignment" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		$this->setUseCluster( False ); // Shows the processing host params to set processors and memory
		$this->setShowRemoteOutDir( False ); // Shows the remote out dir field in cluster params (since using apRemoteJob.py which expects it)
		$this->setEnableLocalHost( False ); // ISAC needs to know the local helper host to rsync the results back to the local rundir
		
		//------ Add JavaScript functions needed for this form -------------------------//
		
		
		//------ Set Parameters specific to the program that requires this new form -----//
		
		$particle 				= new particledata();
		$this->stackIds 		= $particle->getStackIds($expId);
	
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "departalign" );
				
		// Add each of the parameters here. 
		// addParam( "key", default_value, "Label that appears in GUI")
		$params->addParam( "stackid", $stackId, "Select a stack of particles to use" );
		$params->addParam( "darkreference_transform", $darkreference_transform, "Dark reference transform" );
		$params->addParam( "gainreference_transform", $gainreference_transform, "Gain reference transform" );
		$params->addParam( "defects_columns", $defects_columns, "Defects columns" );
		$params->addParam( "defects_rows", $defects_rows, "Defects rows" );
		$params->addParam( "alignment_correct", $alignment_correct, "Alignment correct" );
		$params->addParam( "boxes_transform", $boxes_transform, "Boxes transform" );
		$params->addParam( "radiationdamage_compensate", $radiationdamage_compensate, "Radiation damage compensate" );
		$params->addParam( "radiationdamage_exposurerate", $radiationdamage_exposurerate, "Radiation damage eposure rate" );
		$params->addParam( "radiationdamage_apix", $radiationdamage_apix, "Radiation damage apix" );
		$params->addParam( "output_rotation", $output_rotation, "Output rotation" );
		$params->addParam( "alignment_target", $alignment_target, "Alignment target" );

	}
		
	// Generate a form for the parameters that are specific to this program 
	// This overrides the generateAdditionalFormRight() 
	// function that is found in the BasicLayoutForm class.
	public function generateAdditionalFormRight()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 5;

		$html .= "
	    <br />
	    <H4>DE Align Parameters</H4>
	    <hr />";

		$html.= $params->insertTextField( "defects_columns", $fieldSize );
		$html.= $params->insertTextField( "defects_rows", $fieldSize );
		
		$html .= "<br />";
		
		$html.= $params->insertTextField( "darkreference_transform", $fieldSize );
		$html.= $params->insertTextField( "gainreference_transform", $fieldSize );
		$html.= $params->insertTextField( "boxes_transform", $fieldSize );
		
		$html .= "
	    <br />
	    <H4>Advanced DE Align Parameters</H4>
	    <hr />";
		
		$html.= $params->insertTextField( "radiationdamage_compensate", $fieldSize );
		$html.= $params->insertTextField( "radiationdamage_exposurerate", $fieldSize );
		$html.= $params->insertTextField( "radiationdamage_apix", $fieldSize );
		
		$html .= "<br />";
		
		$html.= $params->insertTextField( "output_rotation", $fieldSize );
		$html.= $params->insertTextField( "alignment_target", $fieldSize );
		$html.= $params->insertTextField( "alignment_correct", $fieldSize );
		
		return $html;
	}	
	
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		$particle 	= new particledata();
		
		$html .= "
	    <br />
	    <H4>Stack Selection</H4>
	    <hr />";
		
		if (!$this->stackIds) {
			$html .=  "<font color='red'><B>No Stacks for this Session</B></FONT>\n";
		} else {
			$options 	= $particle->getStackOptions($this->stackIds);
			$html 		.= $params->insertStackedSelectField( "stackid", $options );
		}
		
		return $html;
	}
	
	// Override the buildCommand function to adapt to the old python command
	// that uses "-" in params and parse the stack id.
	public function buildCommand( $postArray )
	{	
		$command = parent::buildCommand( $postArray );
		
		$params = $this->getFormParams();
		
		// Determine if we should use the stack or alignedstack id
		$command = $this->removeCommandFlag( $command, "stackid" );
		$stack = $params->getParamValue( "stackid" );
		list($stackid, $apix, $boxsz, $totpart) = preg_split('%\|--\|%',$stack);
		$command = $this->addCommandFlag( $command, "stackid", "stackid", $stackid );			
				
		return $command;		
	}
}
?>
