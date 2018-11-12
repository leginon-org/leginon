<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicLayoutForm.inc"; //includes the BasicLayoutForm class that this class extends
require_once "inc/particledata.inc"; // needed to look up symmetry values

class GenerateMissingStackForm extends BasicLayoutForm
{
	protected $stackIds;
	
	// Set Default values in the constructor
	function __construct( $expId, $extraHTML='',$stackId='',$commit='on' 
		) 
	{
		parent::__construct($expId, $extraHTML);
		
		//------ Set Parameters for the parent class, BasicLoopForm (general Appion params) -----//
		
		// Set the publications to be references on the web pages
		$pubList = array('appion'); // Keys are found in publicationList.inc
		$this->setPublications( $pubList ); // list of references to display
		
		$this->setJobType( 'stacktool' ); //Job type stored in database
		$this->setOutputDirectory( 'stacktool' ); // the general folder this job run will be stored in, along with others of this type
		$this->setBaseRunName( 'missingstack' ); // a unique number will be added to this to create the run name
		$this->setTitle( 'Missing Stack Generator Launcher' ); // Shows up in the browser tab
		$this->setHeading( 'Generate Mission Stack' ); // shows at the top of the processing page
		$this->setExeFile( 'generateMissingStack.py' ); // added to the command string
		$this->setGuideURL( "http://emg.nysbc.org/redmine/projects/appion/wiki/Make_Stack" );
		$this->setTestable( False ); // True to activate "test single image".
		$this->setUseLegOutDir( False ); // The output directory will be created in the Appion run directory rather than Leginon.
		$this->setShowDesc( False ); // Flag to hide the description field of the run parameters.
		$this->setUseCluster( False ); // Shows the processing host params to set processors and memory
		
		//------ Add JavaScript functions needed for this form -------------------------//
		
		$javascript = "<script src='../js/viewer.js'></script>\n";
		// javascript to switch the defaults based on the stack
		$javascript .= "<script>\n";
		$javascript .= "function switchDefaults(stackval) {\n";
		$javascript .= "	var stackArray = stackval.split('|--|');\n";
		// remove commas from number
		$javascript .= "	stackArray[3] = stackArray[3].replace(/\,/g,'');\n";
		$javascript .= "	document.viewerform.numpart.value = stackArray[3];\n";
		$javascript .= "	document.viewerform.clip.value = stackArray[2];\n";
		// set max last ring radius
		$javascript .= "	var bestbin = Math.floor(stackArray[2]/64);\n";
		$javascript .= "	if (bestbin < 1) {\n";
		$javascript .= "		var bestbin = 1 ;}\n";
		$javascript .= "	document.viewerform.bin.value = bestbin;\n";
		// set particle & mask radius and lp
		$javascript .= "}\n";
		$javascript .= "
			function enablefastmode() {
				if (document.viewerform.fast.checked){
					document.viewerform.fastmode.disabled=false;
				} else {
					document.viewerform.fastmode.disabled=true;
				}
	
			}
			\n";
		$javascript .= "</script>\n";
		
		$this->addJavaScript( $javascript );
		
		//------ Set Parameters specific to the program that requires this new form -----//
		
		$particle = new particledata();
		$this->stackIds = $particle->getStackIds($expId);
	
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );
				
		// Add each of the parameters here. 
		// addParam( "key", default_value, "Label that appears in GUI")
		$params->addParam( "stack", $stackId, "Select a stack of particles to use" );
		
	}
		
	// Generate a form for the parameters that are specific to this program 
	// The Left side will just show the stack and model that the user selected
	// on the previous pages. This overrides the generateAdditionalFormLeft() 
	// function that is found in the BasicLayoutForm class.
	public function generateAdditionalFormRight()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 5;
		
		// When loading this page the first time, use the switchDefaults javascript function to set 
		// form parameters based on the currently selected stack.
		if (!$_POST['process']) {
			$html.= "<script>switchDefaults(document.viewerform.stack.options[document.viewerform.stack.selectedIndex].value);</script>\n";
		}
		
		return $html;
	}	
	
	public function generateAdditionalFormLeft()
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		if (!$this->stackIds) {
			$html =  "<font color='red'><B>No Stacks for this Session</B></FONT>\n";
		} else {
			$onchange 	= "switchDefaults(this.value)";
			$particle 	= new particledata();
			$options 	= $particle->getStackOptions($this->stackIds);
			$html 		= $params->insertStackedSelectField( "stack", $options,'', '', $onchange );
		}
		
		$html .= "<br />";
		
		return $html;
	}
	
	// Override the buildCommand function to adapt to the old python command
	// that uses "-" in params and parse the stack id.
	public function buildCommand( $postArray )
	{	
		$command = parent::buildCommand( $postArray );
		
		$params = $this->getFormParams();
		
		// Extract the stack id from the stack string
		$stack = $params->getParamValue( "stack" );
		list($stackid, $apix, $boxsz, $totpart) = preg_split('%\|--\|%',$stack);
		$command = $this->removeCommandFlag( $command, "stack" );
		$command = $this->addCommandFlag( $command, "stack", "stack", $stackid );
		
		return $command;		
	}
	
	// Override the validate function to add more complex validations than are available in the formValidator class.
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		
		$params = $this->getFormParams();
		
		// Extract the stack id from the stack string
		$stack = $params->getParamValue( "stack" );
		list($stackid, $apix, $boxsz, $totpart) = preg_split('%\|--\|%',$stack);
		
		return $msg;
	}	
}
?>
