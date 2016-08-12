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
require_once "templatePickerForm.inc";

class GautomatchForm extends TemplatePickerForm

{

	function __construct(  $expId, $errorHTML='', $infoHTML='',$usemirrorv=false,$ac=0.1,$minthresh=0.4 ) 
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
		$params->addParam( "ac",$ac,"Amplitude contrast. Normal range 0.04~0.1; pure ice 0.04, carbon 0.1");


		//template settings
		$this->createTemplateTableForm();

		// different defaults
		$math_params = $this->mathTable->getFormParams();
		$math_params->setParamValue('minthresh',0.4);
		// old default is '' (unset) but form wants a value for validation purpose
		$math_params->setParamValue('maxthresh','1.0');
	}


 public function generatePreForm() {
                // get parent pre-form elements
		$html  .= '<div id="notice">(Leave all templates unchecked to run Gautomatch without templates.)</div><br>';
                $html  .= parent::generatePreForm();
                // Select template in the pre-form
 #               $html .= $this->TemplateTable->generateForm($enable=true);
                return $html;

        }

/*
        public function generateFormFooter() {
                // show selected templates with the entry disabled
                $html .= $this->TemplateTable->generateForm($enable=false);

                $used_templates = $this->TemplateTable->getUsedTemplateIds();
                // set multi thread according to number of templates;
                $params = $this->getFormParams();
                if ( count($used_templates) > 1 )

 #                       $params->setParamValue('thread_findem','on');
 #               $html .= $params->insertHiddenField( "thread_findem" );
                return $html;
        }


//	public function generateAdvancedTableRight() {}
        public function generateAdditionalFormRightHeader() {
                $this->updateFormParams();
                $params = $this->getFormParams();
                $fieldSize = 5;

	        $html .= "<b>Gautomatch Parameters:</b><br />\n";

                $html.= $params->insertTextField( "ac", $fieldSize);

                $html.= "<br/>\n";

                $html.= parent::generateAdditionalFormRightHeader();
                return $html;
        }

*/
 	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand( $postArray );
		$params = $this->getFormParams();

                $command = $this->removeCommandFlag( $command, "thread_findem" );
		$command = $this->removeCommandFlag( $command, "planereg" );
		$command = $this->removeCommandFlag( $command, "peaktype" );
		return $command;
	}
// public function validate( $postArray ) {}

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
