<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "mathParticleForm.inc";
require_once "inc/particledata.inc";
require_once "inc/processing.inc";
require_once "templateTable.inc";

class TemplatePickerForm extends MathParticleForm

{
	protected $availableTemplate;			// an array of templateinfo availble in the project

	function __construct(  $expId, $errorHTML='', $infoHTML='', $threadfindemv='on',$spectralv=false,$usemirrorv=false ) 
	{
		parent::__construct($expId, $errorHTML, $infoHTML);
		
		// initialize private variables;
		$this->availableTemplates = array();

		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		$this->setShowPreForm(true);


		// Set the publications to be references on the web pages
		$pubList = array('roseman04');
		$this->setLogoImagePath( 'img/findem.png' );
		$this->setPublications( $pubList );
		$this->setJobType( 'templatecorrelator' );
		$this->setOutputDirectory( 'extract' );
		$this->setBaseRunName( 'tmplrun' );
		$this->setTitle( 'templateCorrelator.py Launcher' );
		$this->setHeading( 'Automated Particle Selection with Template Correlator' );
		$this->setExeFile( 'templateCorrelator.py' );
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Appion_Processing" );
		$this->setTestable( True ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		$this->setUseCluster( True ); // Shows the processing host params to set processors and memory
		
		//------ Set Parameters specific to the program that requires this new form -----//
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );
				
		//findem settings
		$params->addParam( "thread_findem", $threadfindemv, "Multi thread template correlation" );
		$params->addParam( "spectral", $spectralv, "Use spectral correlation" );
		$params->addParam( "use_mirrors", $usemirrorv, "Use template mirrors" );
		
		//template settings
		$this->createTemplateTableForm();

		// different defaults
		$math_params = $this->mathTable->getFormParams();
		$math_params->setParamValue('minthresh',0.5);
		// old default is '' (unset) but form wants a value for validation purpose
		$math_params->setParamValue('maxthresh','5');
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

	public function generatePreForm() {
		// get parent pre-form elements
		$html  .= '<input type="checkbox" id="selectall" onclick="checkAll(this)"></input>';
		$html  .= '<label id="selectallLabel" for="selectall">Select all templates</label>';
		$html  .= parent::generatePreForm();
		// Select template in the pre-form
		$html .= $this->TemplateTable->generateForm($enable=true);
		return $html;
		
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
		$params = $this->getFormParams();
		if ( count($used_templates) > 1 )
			
			$params->setParamValue('thread_findem','on');
		$html .= $params->insertHiddenField( "thread_findem" );
		return $html;
	}

	public function generateAdditionalFormRightHeader() {
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 3;

		$html = parent::generateAdditionalFormRightHeader();

		$html .= $params->insertCheckboxField( "use_mirrors" );
		$html .="<br />\n";
		return $html;
	}
	
	public function buildCommand($postArray) {
		// multi-thread findem by template

		$command .= parent::buildCommand($postArray);
		$command .= $this->TemplateTable->buildCommand( $postArray);
		return $command;
	}
		
	// Override the validate function so that we can verify the Template Correlator parameters
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		$msg .= $this->TemplateTable->validate( $postArray );
		
		return $msg;
	}


	// getTestResults() return the HTML code needed to display test results from this method
	static public function getTestResults( $outdir, $runname, $testfilename )
	{
		$testjpg = preg_replace("%.mrc%","",$testfilename);
		$testResultFile = $testjpg.".prtl.jpg";
		$jpgimg = Path::join($outdir, $runname, "jpgs", $testResultFile);
		
		$pathToMaps = Path::join($outdir, $runname, "maps");

		// Fix me, Not the best way to get binning
		$bin = $_POST['binval'];
		$process = $_POST['process'];

		$filePattern = $testjpg."*.jpg";
		$pathPattern = Path::join($pathToMaps, $filePattern);
		$ccmaplist = glob($pathPattern);
		$html .= writeTestResults($jpgimg, $ccmaplist, $bin, $process);
		return $html;
	}
}
?>

<script type="text/javascript">

var selectall = document.getElementById('selectall');
var cbs = document.getElementsByTagName('input');

if (cbs.length) {
	selectall.style.display = 'none';
	}
else {
	selectall.style.display = 'block';
     }

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
