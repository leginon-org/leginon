<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/particledata.inc";
require_once "inc/processing.inc";
require_once "basicParticleForm.inc";
require_once "templateTable.inc";

class GautomatchForm extends basicParticleForm

{

	function __construct(  $expId, $errorHTML='', $infoHTML='', $thresh=0.2,
		$invert=True, $lp=30, $hp=1000, $lsigma_D=200, $lsigma_cutoff=1.3, $lave_D=400, $speed=2,
		$overlapmult=1.0, $ang_step=5 ) 
	{
		parent::__construct($expId, $errorHTML, $infoHTML);
		
		// initialize private variables;
		$this->availableTemplates = array();

		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		$this->setShowPreForm(true);

		// Set the publications to be references on the web pages
		$pubList = array('appion');
		//$this->setLogoImagePath( 'img/appionlogo.jpg' );
		$this->setPublications( $pubList );
		$this->setJobType( 'gautomatch' );
		$this->setOutputDirectory( 'extract' );
		$this->setBaseRunName( 'gauto' );
		$this->setTitle( 'Gautomatch.py Launcher' );
		$this->setHeading( 'GPU-powered Automated Particle Selection with Gautomatch' );
		$this->setExeFile( 'gAutomatchFast.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
		$this->setTestable( True ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "gautomatch" );
				
		//Gautomatch settings

		$params->addParam( "overlapmult", $overlapmult,"Overlap multiplier between particles" );
		$params->addParam( "thresh", $thresh, "threshold" );
		$params->addParam( "ang_step", $ang_step, "Angular steps in template rotation" );
		$params->addParam( "lp",$lp,"Low pass filter after ice/aggregate detection. (Angstrom)" );
		$params->addParam( "hp",$hp,"High pass filter after ice/aggregate detection. (Angstrom)" );
		$params->addParam( "speed",$speed,"Speed level (0,1, 2, 3, 4), larger is faster but less accurate.");

		$params->addParam( "lsigma_D",$lsigma_D,"Diameter for estimation of local sigma (Angstrom)" );
		$params->addParam( "lsigma_cutoff",$lsigma_cutoff,"Local sigma cutoff (relative value)." );
		$params->addParam( "lave_D",$lave_D,"Diameter for estimation of local average. (Angstrom)" );
		
		//template settings
		$this->createTemplateTableForm();
		// different defaults
	}

	protected function createTemplateTableForm() {
		// Search for available templates
		$projectId   = getProjectId();
		if (is_numeric($projectId)) {
			$this->particle = new particledata();
			$this->availableTemplates = $this->particle->getTemplatesFromProject($projectId);
		}
		$this->TemplateTable = new TemplateSelectionTable($this->availableTemplates, $angles=false);
	}

	public function generateForm() {
		// default particle mask diameter depends on the template diameter
		$params = $this->pDiameterTable->getFormParams();
		$template_diam = (int) $this->TemplateTable->getTemplateDiameter();
		if ( !$params->getParamValue('pdiam') && $template_diam )
			$params->setParamValue('pdiam', round(1.3* $template_diam) );
		// get parent form elements
		$html  .= parent::generateForm();

		return $html;
		}


	public function generateFormFooter() {
		// show selected templates with the entry disabled
		$html .="<script type='text/javascript' src = 'https://cdnjs.cloudflare.com/ajax/libs/jquery/3.1.1/jquery.min.js'></script>";
		$html .= $this->TemplateTable->generateForm($enable=false);
		$used_templates = $this->TemplateTable->getUsedTemplateIds();

		return $html;
	}

				       
	public function generatePreForm() {
		// get parent pre-form elements
		$html  .= parent::generatePreForm();
		// Select template in the pre-form
		$html  .= '<center><button type="button" onclick="checkAll(this)">';
		$html  .= '<label id="selectallLabel1" for="selectall">Select all templates</label>';
		$html  .= "</button></center>";
		$html  .= $this->TemplateTable->generateForm($enable=true, $angles=false);
		$html  .= '<center><button type="button" onclick="checkAll(this)">';
		$html  .= '<label id="selectallLabel2" for="selectall">Select all templates</label>';
		$html  .= "</button></center>";
		return $html;
	}


	public function generateAdditionalFormRight() 
	{
	
	$params = $this->getFormParams();
 	$pDiamparams = $this->pDiameterTable->getFormParams();	
	$imagecontrastparams = $this->imageContrastTable->getFormParams();
	
	$html .= "<!--BEGIN Gautomatch Param -->\n";
	$fieldSize = '5';
	$html .= "<b>Gautomatch parameters:</b><br /><br />\n";
	$html .= $pDiamparams->insertTextField( "pdiam", $fieldSize );
	$html .= $params->insertTextField( "thresh", $fieldSize );
	$html .= $params->insertTextField( "overlapmult", $fieldSize );
	$html .= $params->insertTextField( "ang_step", $fieldSize );
	$html .= "<br />";

	$html .= $imagecontrastparams->insertCheckBoxField( "invert" );

	$html .= "<br />";
	$html .= "<b>Filter parameters:</b><br /><br />\n";
	$html .= $params->insertTextField( "lp", $fieldSize );
	$html .= $params->insertTextField( "hp", $fieldSize );

	$html .= "<br />";
	$html .= "<b>Advanced parameters:</b><br /><br />\n";
	$html .= $params->insertTextField( "speed", $fieldSize );
	$html .= $params->insertTextField( "lsigma_D", $fieldSize );
	$html .= $params->insertTextField( "lsigma_cutoff", $fieldSize );
	$html .= $params->insertTextField( "lave_D", $fieldSize );



	return $html;
	
	}
#	public function generateAdvancedTableRight() {}
#	public function generateAdvancedFormRight() {}
#	public function generateAdditionalFormRightHeader() {}


 	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand( $postArray );
		$params = $this->getFormParams();
		$command .= $this->TemplateTable->buildCommand( $postArray);

		return $command;
	}

	 public function validate( $postArray ) {
		$msg = '';
		$msg .= $this->TemplateTable->validate( $postArray );
		return $msg;

}

}
?>

<script type="text/javascript">

$(document).ready(function() {
    $.jQuery("#lappion.invert").prop('checked',true);
});


function checkAll(bx) {
	var selectallText1 = document.getElementById('selectallLabel1');
	var selectallText2 = document.getElementById('selectallLabel2');

	if (selectallText1.innerHTML == 'Select all templates') {
		selectallText1.innerHTML = 'Deselect all templates';
		selectallText2.innerHTML = 'Deselect all templates';
		checkaction = true;
	} else {
		selectallText1.innerHTML = 'Select all templates';
		selectallText2.innerHTML = 'Select all templates';
		checkaction = false;
	}

  var inputs = document.getElementsByTagName('input');

  for(var i=0; i < inputs.length; i++) {
    if(inputs[i].type == 'checkbox') {
      inputs[i].checked = checkaction;
    }
  }


};


</script>
