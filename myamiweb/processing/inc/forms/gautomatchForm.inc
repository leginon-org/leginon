<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "mathParticleForm.inc";
require_once "inc/particledata.inc";
require_once "inc/processing.inc";
require_once "gautomatchTemplateTable.inc";

class GautomatchForm extends basicParticleForm

{

	function __construct(  $expId, $errorHTML='', $infoHTML='',$ac=0.1,$minthresh=0.4,$invert=True,$lp=30,$hp=1000,$do_pre_filter=False,$pre_lp=8.0,$pre_hp=1000,$lsigma_D=200,$lsigma_cutoff=1.3,$lave_D=400,$speed=2,$overlapmult=1.0 ) 
	{
		parent::__construct($expId, $errorHTML, $infoHTML);
		
		// initialize private variables;
		$this->availableTemplates = array();

		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		$this->setShowPreForm(true);


		// Set the publications to be references on the web pages
		$pubList = array('appion');
		$this->setLogoImagePath( 'img/appionlogo.jpg' );
		$this->setPublications( $pubList );
		$this->setJobType( 'gautomatch' );
		$this->setOutputDirectory( 'extract' );
		$this->setBaseRunName( 'gauto' );
		$this->setTitle( 'gautomatch.py Launcher' );
		$this->setHeading( 'GPU-powered Automated Particle Selection with Gautomatch' );
		$this->setExeFile( 'gautomatch.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
		$this->setTestable( True ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "gautomatch" );
				
		//findem settings

		//Gautomatch settings

		$params->addParam( "overlapmult", $overlapmult,"Overlap multiplier between particles" );
		$params->addParam( "invert", $invert,"Invert contrast" );
		$params->addParam( "pdiam",$pdiam,"Particle diameter. Only relevant for DoG picking.");
		$params->addParam( "ac",$ac,"Amplitude contrast");
	        $params->addParam( "minthresh", $minthresh, "Minimum threshold" );
		$params->addParam( "lp",$lp,"Low pass filter after ice/aggregate detection. (Angstrom)" );
		$params->addParam( "hp",$hp,"High pass filter after ice/aggregate detection. (Angstrom)" );
		$params->addParam( "do_pre_filter",$do_pre_filter,"Do pre filtering (not recommended)" );
		$params->addParam( "pre_lp",$pre_lp,"Low pass filter before ice/aggregate detection. (Angstrom)" );
		$params->addParam( "pre_hp",$pre_hp,"High pass filter before ice/aggregate detection. (Angstrom)" ); 
		$params->addParam( "speed",$speed,"Speed level (0,1, 2, 3, 4), larger is faster but less accurate.");
		$params->addParam( "boxsize",$boxsize,"Template box size in pixels. Will be calculated based on diameter and micrograph pixel size if left blank.");
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

                $this->TemplateTable = new TemplateSelectionTable($this->availableTemplates);
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
                $html .= $this->TemplateTable->generateForm($enable=false);

                $used_templates = $this->TemplateTable->getUsedTemplateIds();
                // set multi thread according to number of templates;
                return $html;
        }

                                       
        public function generatePreForm() {
                // get parent pre-form elements
		$html  .= '<div id="notice">(Leave all templates unchecked to run Gautomatch as a DoG picker.)</div><br>';
                $html  .= parent::generatePreForm();
                // Select template in the pre-form
                $html .= $this->TemplateTable->generateForm($enable=true);
                return $html;

        }


	public function generateAdditionalFormRight() 
	{
	
	$params = $this->getFormParams();
	$newparams = $this->getFormParams();				
	

	
	$html .= "<!--BEGIN Gautomatch Param -->\n";
	$fieldSize = '5';
        $html .= "<b>Gautomatch parameters:</b><br /><br />\n";
	$html .= $params->insertTextField( "pdiam", $fieldSize );
        $html .= $params->insertTextField( "minthresh", $fieldSize );
	$html .= $params->insertTextField( "overlapmult", $fieldSize );
	$html .= "<br />";
	$html .= $params->insertCheckBoxField( "invert");

	$html .= "<br />";
        $html .= "<b>Filter parameters:</b><br /><br />\n";
	$html .= $params->insertTextField( "lp", $fieldSize );
        $html .= $params->insertTextField( "hp", $fieldSize );
	$html .= "<br />";
	$html .= $params->insertCheckboxField( "do_pre_filter" );
	$html .= "<br />";
        $html .= $params->insertTextField( "pre_lp", $fieldSize );
        $html .= $params->insertTextField( "pre_hp", $fieldSize );

        $html .= "<br />";
        $html .= "<b>Advanced parameters:</b><br /><br />\n";
        $html .= $params->insertTextField( "speed", $fieldSize );
        $html .= $params->insertTextField( "boxsize", $fieldSize );
        $html .= $params->insertTextField( "lsigma_D", $fieldSize );
        $html .= $params->insertTextField( "lsigma_cutoff", $fieldSize );
        $html .= $params->insertTextField( "lave_D", $fieldSize );
        $html .= $params->insertTextField( "pre_hp", $fieldSize );


	return $html;
	
	}
        public function generateAdvancedTableRight() {}
        public function generateAdvancedFormRight() {}
        public function generateAdditionalFormRightHeader() {}

/*
 	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand( $postArray );
		$params = $this->getFormParams();

		return $command;
	}
*/
 public function validate( $postArray ) {}

}
?>

<script type="text/javascript">

function checkAll(bx) {
  var cbs = document.getElementsByTagName('input');

  for(var i=0; i < cbs.length; i++) {
    if(cbs[i].type == 'checkbox') {
      cbs[i].checked = bx.checked;
    }
  }

var selectallText = document.getElementById('selectallLabel');

if (selectallText.innerHTML == 'Select all templates') {
	selectallText.innerHTML = 'Deselect all templates';
	}

else {
	selectallText.innerHTML = 'Select all templates';
	}


};


</script>
