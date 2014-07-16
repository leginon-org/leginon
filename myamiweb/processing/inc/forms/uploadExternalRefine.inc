<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */
require_once "basicLayoutForm.inc";
require_once "inc/summarytables.inc";
require_once "inc/particledata.inc";

// Used to create a command similar to the following:
// uploadExternalRefine.py --rundir=/ami/data17/appion/11jan11a/recon/external_package_test 
// --runname=external_package_test --description="testing out external upload on 11jan11 data, emanrecon11, first iteration" 
// --projectid=224 --no-commit --expId=8397 --uploadIterations=1,2,3,4,5 --stackid=127 
// --modelid=19 --mass=3800 --apix=2.74 --box=160 --numberOfReferences=1 --numiter=1 --timestamp=11jul18z 
// --symid=25

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
		$this->setOutputDirectory( 'recon' );
		$this->setBaseRunName( '' );
		$this->setTitle( 'Upload Reconstruction' );
		$this->setHeading( 'Upload External Reconstruction' );
		$this->setExeFile( 'uploadExternalRefine.py' );
		$this->setGuideURL( "http://ami.scripps.edu/redmine/projects/appion/wiki/Appion_Processing" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( True ); // Flag to hide the description field of the run parameters.
		$this->setUseCluster( False );
		
		//------ Set Parameters specific to the program that requires this new form -----//
	
		// find any selected models
		// we expect the key to be "model_" for single model, the value to be "model_#"
		// for multi-model, the value and key are both "model_#"
		foreach( $_POST as $key=>$value ) {
			if (strpos($key,"model_" ) !== False) {
				$id = $this->getModelId($value);
				$this->modelArray[] = array( 'name'=>$value, 'id'=>$id );
				$modelid = $id; //assume single model for now
			}
		}
		
		if (!$this->modelArray)
			$error = "ERROR: no initial model selected";
		if (!$_POST['stackval']) {
			$error = "ERROR: no stack selected";
		} else {
			$stackid = $_POST['stackval'];
		}
			
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "em_hole_finder" );
				
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
		//$params->addValidation( "numpart", "req" );
	}
		
	// Generate a form for the parameters that are specific to this program (not Appion params)
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 10;
		
		$html .= "
	    <br />
	    <H4>Recon Upload Parameters</H4>
	    <hr />";
		
		$html .= $this->insertSymmetrySelectionBox( "symid", $params->getParamValue("symid") );
		$html .= "&nbsp;";
		$html .=  docpop( "basicrefine.symmetry", $params->getParamLabel("symid") );
		$html.= "<br/><br/>\n";
		
		$html.= $params->insertTextField( "uploadIterations", $fieldSize );
		$html.= $params->insertTextField( "mass", $fieldSize );
		$html.= $params->insertTextField( "apix", $fieldSize );
		$html.= $params->insertTextField( "box", $fieldSize );
		$html.= $params->insertTextField( "numberOfReferences", $fieldSize );
		$html.= $params->insertTextField( "numiter", $fieldSize );
		$html.= $params->insertTextField( "timestamp", $fieldSize );
		$html.= $params->insertTextField( "stackid", $fieldSize );
		$html.= $params->insertTextField( "modelid", $fieldSize );

		
		// add stack and model summary
		//echo "StackID: $stackid -- ModelID: $modelid<br/>\n";
		$html.= "<br/><br/>\n";
		$html.= "<table class='tablebubble'><tr><td>\n";
		$html.= stacksummarytable($params->getParamValue('stackid'), true);
		$html.= "</td></tr>";
		foreach ( $this->modelArray as $model ) {
			$html.= "<tr><td>\n";
			$html.= modelsummarytable( $model['id'], true );
			$html.= "</td></tr>";
		}
		$html.= "</table>\n";
		
		return $html;
	}	

	// Override the default build Command Function because the --test flag is not normal
	// for other Appion Loop methods and not included in the parent.
	public function buildCommand( $postArray )
	{
		$command   = parent::buildCommand( $postArray );
		
		if ( $postArray['testimage']=="on" ) {
			$command.= " --test";
		}
		
		return $command." ";
	}

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
	
	// returns the html to display a drop down selection box
	// containing all the available symmetry values as defined
	// in the apSymmetry table. 
	// Name is the name of the form parameter
	// Value is the currently selected symmetry id 
	// TODO: this is awfully similar to the box in UploadModel.php...merge? 
	function insertSymmetrySelectionBox( $name, $value ) 
	{
		$this->particle = new particledata();
		
		// if there are quotes around $value, trim them
		$value = str_replace('"','',$value); 
		
		$syms = $this->particle->getSymmetries();
		$html .= "<select name='$name'>\n";
	   	$html .= "<option value=''>select one...</option>\n";
		
	   	foreach ($syms as $sym) {
	   		$id 		= $sym['DEF_id'];
	   		$symmetry 	= $sym['symmetry'];
	   		
			$html .= "<option value='$symmetry'";
			
			if ( strcasecmp($symmetry, $value) == 0 ) {
				$html .= " SELECTED";
			}
			
			$html .= ">$symmetry";
			
			if ($symmetry == 'C1') {
				$html .= " (no symmetry)";
			}
			
			$html .= "</option>\n";
		}
		
		$html .= "</select>\n";
		
		return $html;
	}	
}
?>
