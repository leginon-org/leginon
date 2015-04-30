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

require_once "basicLayoutForm.inc"; //includes the BasicLayoutForm class that this class extends
require_once "inc/particledata.inc"; // needed to look up symmetry values
require_once "inc/summarytables.inc"; // needed to show stack and model tables

class UploadExternalRefine extends BasicLayoutForm
{
	
	function __construct( $expId, $extraHTML='', $stackid='', $modelid='', $uploadIterations='', $mass='', $apix='', $box='',
	$numberOfReferences='', $numiter='', $timestamp='', $symid='') 
	{
		parent::__construct($expId, $extraHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('appion');
		$this->setPublications( $pubList );
		$this->setJobType( 'uploadrecon' );
		$this->setOutputDirectory( 'recon/external_package_test' );
		$this->setBaseRunName( 'external_refinement_results' );
		$this->setTitle( 'Upload Reconstruction' );
		$this->setHeading( 'Upload External Reconstruction' );
		$this->setExeFile( 'uploadExternalRefine.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Upload_Refinement" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( True ); // Flag to hide the description field of the run parameters.
		$this->setUseCluster( False );
		
		//------ Set Parameters specific to the program that requires this new form -----//
	
		// Find any selected models and stack. 
		// These were selected on a previous page and stored in the $_POST array.
		// We expect the key to be "model_" for single model, the value to be "model_#"
		// for multi-model, the value and key are both "model_#"
		foreach( $_POST as $key=>$value ) {
			if (strpos($key,"model_" ) !== False) {
				$id = $this->getModelId($value);
				$this->modelArray[] = array( 'name'=>$value, 'id'=>$id );
				$modelid = $id; //assume single model for now
			}
		}
		
		if ($_POST['stackval']) {
			$stackid = $_POST['stackval'];
		}
			
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "upload_external_recon" );
				
		// Add each of the parameters here. 
		// addParam( "key", default_value, "Label that appears in GUI")
		$params->addParam( "uploadIterations", $uploadIterations, "Upload iterations" );
		$params->addParam( "mass", $mass, "Mass" );
		$params->addParam( "apix", $apix, "Apix" );
		$params->addParam( "box", $box, "Box size" );
		$params->addParam( "numberOfReferences", $numberOfReferences, "Number of references" );
		$params->addParam( "numiter", $numiter, "Number of iterations" );
		$params->addParam( "timestamp", $timestamp, "Timestamp" );
		$params->addParam( "symid", $symid, "Symmetry group" );
		$params->addParam( "stackid", $stackid, "Stack id" );
		$params->addParam( "modelid", $modelid, "Model id" );
		
		// Validations
		$params->addValidation( "uploadIterations", "req" );
		$params->addValidation( "apix", "req" );
		$params->addValidation( "box", "req" );
		$params->addValidation( "numiter", "req" );
		$params->addValidation( "numberOfReferences", "req" );
		$params->addValidation( "timestamp", "req" );
		$params->addValidation( "symid", "req" );
		$params->addValidation( "stackid", "req" );
		$params->addValidation( "modelid", "req" );
	}
		
	// Generate a form for the parameters that are specific to this program 
	// The Left side will just show the stack and model that the user selected
	// on the previous pages. This overrides the generateAdditionalFormLeft() 
	// function that is found in the BasicLayoutForm class.
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
				$fieldSize = 15;
		
		$html .= "
	    <br />
	    <H4>Recon Upload Parameters</H4>
	    <hr />";
		
		$symDict = $this->createSymmetryDict();
		$html .= $params->insertSelectField( "symid", $symDict );
		
		$html.= $params->insertTextField( "timestamp", $fieldSize, "(ex. 11jul18z)" );
		$html.= $params->insertTextField( "numberOfReferences", $fieldSize );
		$html.= $params->insertTextField( "numiter", $fieldSize );
		$html.= $params->insertTextField( "uploadIterations", $fieldSize, "(ex. 1,2,3)" );
		$html.= $params->insertTextField( "mass", $fieldSize, "(kDa)" );
		$html.= $params->insertTextField( "apix", $fieldSize, "(&Aring;ngstroms)" );
		$html.= $params->insertTextField( "box", $fieldSize, "(Pixels)" );
		$html.= $params->insertTextField( "stackid", $fieldSize );
		$html.= $params->insertTextField( "modelid", $fieldSize );
		
		// add stack summary
		//echo "StackID: $stackid -- ModelID: $modelid<br/>\n";
		$html.= "<table class='tablebubble'><tr><td>\n";
		$html.= stacksummarytable($params->getParamValue('stackid'), true);
		$html.= "</td></tr>";
		// Add the model summary table
		$html.= "<tr><td>\n";
		$html.= modelsummarytable( $params->getParamValue('modelid'), true );
		$html.= "</td></tr>";
		$html.= "</table>\n";
		
		return $html;
	}	
	
	//------ Helper Functions specific to this form only -----//

	// Parse "model_#" to return #
	function getModelId($value)
	{
		$id = 0; //default
		
		if (strpos($value,"model_" ) !== False) {
			preg_match('/(\D+)_(\d+)/', $value, $matches);
			$id = $matches[2];
		}
		
		return $id;
	}
	
	function createSymmetryDict( ) 
	{
		$this->particle = new particledata();
		$syms = $this->particle->getSymmetries();
		
	   	foreach ($syms as $sym) {
	   		$id 		= $sym['DEF_id'];
	   		$symmetry 	= $sym['symmetry'];
	   		
			if ($symmetry == 'C1') {
				$symmetry = " (no symmetry)";
			}
			
			$symDict[$id] = $symmetry;
	   	}
		
		return $symDict;
	}	
}
?>
