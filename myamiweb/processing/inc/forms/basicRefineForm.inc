<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

//--------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------

require_once "inc/particledata.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/summarytables.inc";
require_once "../inc/formValidator.php";
require_once "../inc/formParameters.inc";


abstract class BasicRefineForm 
{
	private $defaultParamSets; 	// an array of parameter sets of type RefineFormParameters used for populating forms
	private $selectedParams; 	// the current user selected or modified parameter set
	private $stackInfo;
	
	function __construct( $method, $stackId, $modelArray, $kv ) 
	{
		$this->method 		= $method;
		$this->stackId 		= $stackId;
		$this->modelArray 	= $modelArray;
		$this->kv 			= $kv;
		
		$this->setStackInfo( $stackId );
	}
	
	// TODO: there is probably a better place for this so that it can be reused, or it 
	// may already exist somewhere???
	public function setStackInfo( $stackId ) 
	{
		$this->stackInfo['id'] = $stackId;
		
		$particle = new particledata();
		$stackParams = $particle->getStackParams( $stackId );
		
		// get number of particles
		$totalParticles = $particle->getNumStackParticles( $stackId );
		$this->stackInfo['numParticles'] = commafy($totalParticles);
		
		// get box size
		$this->stackInfo['box'] = $stackParams['boxsize'];
		
		// get pixel size of stack
		$this->stackInfo['apix'] = ($particle->getStackPixelSizeFromStackId($stackId))*1e10;
	}
	
	public function getStackInfo()
	{
		return $this->stackInfo;
	}
	
	// getters
	public function getMethodType() { return $this->method; } 
	public function getStackId() 	{ return $this->stackId; } 
	public function getModelArray() { return $this->modelArray; } 
	public function getKv() 		{ return $this->kv; } 
	
	// TUTORIAL: "abstract" means that extending classes MUST define this function
	// ex: public getMethodType() { return "eman"; } 
	abstract public function buildCommand( $params ); 
	
	// Extending classes MAY override this to add 
	// package specific parameters to the refine form 
	public function advancedParamForm() {}
		
	// Extending classes should override this function to return the appropriate
	// class of form parameters if it has also extended the RefineFormParams class.
	// This createFormParams() function should always be used instead of 
	// directly creating an instance of RefineFormParameters.
	// GOOD: $params = $this->createFormParams();
	// BAD:  $params = new RefineFormParameters();
	public function createFormParams() { return new RefineFormParameters(); }
	
	// to add default value sets to the Import Parameters form,
	// extending classes should override setImportParams() and
	// use addDefaultParams() to include a set in the list 
	// TUTORIAL: "protected" functions can be accessed only within the class itself 
	// and by inherited and parent classes
	protected function setImportParams()
	{
		// if the derived class does not override this function,
		// use general values associated with asymmetric particles for the general parameters in the form
		// TODO: decide on default values for this
		$asymmSet = new RefineFormParameters('asymm', 'asymmetric particles',1,1,1,1,1,1,1,1,'',1,'checked',1);
		$this->addDefaultParams( $asymmSet );
	}
		
	// adds a set of default values to the "Import Parameters"
	// drop dowm list.
	final protected function addDefaultParams( $newSet )
	{
		$this->defaultParamSets[$newSet->id] = $newSet;
	}
	
	// points the form parameters to the correct set of default
	// values based on the users selection.
	// Takes the default set Id, which corresponds to a set available
	// in the "Import Parameters" drop down list.
	final private function setFormParams( $defaultSetId='' )
	{
		if ( isset( $this->defaultParamSets[$defaultSetId] ) ) {
			// the user just selected an existing set of params to import
			$this->selectedParams = $this->defaultParamSets[$defaultSetId];
			
		} elseif (is_numeric( $defaultSetId ) ) {
			// the user just selected an existing refine run to import params from
			$this->selectedParams = $this->importParamsFromRefinement( $defaultSetId );
			
		} else {
			// the form may be refreshing after posting an error, make sure to get any previous values from the POST array
			$this->selectedParams = $this->createFormParams(); //creates new form params object
			$this->selectedParams->getPostedValues($_POST);
		}
		return $this->selectedParams;
	}
	
	// returns an array of all form parameters
	// with the currently set values
	final protected function getFormParams()
	{
		return $this->selectedParams;
	}
	
	// Add "Set Defaults" button and import parameters drop down selector.
	final private function defaultOptionsForm()
	{
		$this->setImportParams();
		
		$particle = new particledata();
		$leginondata = new leginondata();
	
		// import values from previous uploaded reconstruction
		$projectId=getProjectId();
		$sessions = $leginondata->getSessions("",$projectId);
		if (is_array($sessions)) {
			$ropt = "";
			foreach ($sessions as $s) {
				$recons = $particle->getReconIdsFromSession($s['id']);
				if (is_array($recons)) {
					foreach ($recons as $r) {
						$ropt.= "<option value='".$r['DEF_id']."'>";
						$ropt.= $s['name']." : ";
						$ropt.= $r['name']." - ".$r['description'];
						$ropt.= "</option>\n";
					}
				}
			}
		}
	
		$html .= "<input type='BUTTON' onClick='setDefaults(this.form)' VALUE='Set Defaults'>\n";
		$html .= "<select name='import' onChange='prepRefine.submit()'>\n";
		$html .= "<option>Import parameters</option>\n";
		foreach ($this->defaultParamSets as $defaultSet) {
			$html .= "<option value='$defaultSet->id'>$defaultSet->label</option>\n";
		}
		$html .= "<option value=''>------------------------------</option>\n";
		$html .= $ropt;
		$html .= "</select>\n";
		$html .= "<br />\n";
		$html .= "<br />\n";
		
		return $html;
	}	
	
	// The user selected to import parameters from an existing refinement.
	// This will gather the parameter values and put them into our param 
	// format ('iterations'x'value':)
	// Returns a set of Form Parameters.
	// If you are adding a new type of refinement to the pipeline, you need to edit
	// getIterationInfo() in particledata.inc to retrieve parameter data on the new method type
	// for this function to work on method specific parameters.
	protected function importParamsFromRefinement( $defaultSetId )
	{
		$paramSet = $this->createFormParams();
		$particle = new particledata();
		
		// get model info to set the symmetry
		$modelArray = $this->getModelArray();
		// this method is single model, so grab the first element only
		$modelId 	= $modelArray[0]['id'];
		$modelInfo 	= $particle->getInitModelInfo( $modelId );
		$symInfo 	= $particle->getSymInfo($modelInfo['REF|ApSymmetryData|symmetry']);
		// TODO: would like to use "symmetry" instead of "eman_name" but can't handle spaces in
		// showOrSubmitCommand().
		$symmetry = $symInfo['symmetry'];
		//$symmetry = '"'.$symmetry.'"';
		$paramSet->setParamValue( "symmetry", $symmetry );
		
		// get import refine stack info
		$refinfo 			= $particle->getRefinementRunInfo( $defaultSetId );
		$importStackInfo 	= $particle->getStackParams($refinfo['REF|ApStackData|stack']);
		
		// get our stack info
		$stackInfo 	= $this->getStackInfo();
		$box 		= $stackInfo['box'];
		
		// use the two stacks to get scaling factor for box sizes
		$importBox 	= $importStackInfo['boxsize'];
		$boxscale 	= $box / $importBox;
		
		// set the number of iterations
		$iterinfo = $particle->getIterationInfo( $defaultSetId );
		$numIters = count($iterinfo);
		$paramSet->setParamValue( "numIters", $numIters );
				
		// add each iteration value to our forms parameters
		for ( $i=1; $i<=$numIters; $i++ ) {
			foreach ($iterinfo as $iter) {
				if ($iter['iteration'] == $i) {					
					$outerMaskRadius = ceil($iter['mask']*$boxscale);
					$paramSet->addIterationToValue( "outerMaskRadius", $outerMaskRadius );
					
					if (floor($iter['imask']*$boxscale) > 0)
						$paramSet->addIterationToValue( "innerMaskRadius", floor($iter['imask']*$boxscale) );
						
					$this->addImportedRefineIter( $paramSet, $iter );
						
					continue;
				}
			}
		}
		
		return $paramSet;
	}
	
	// Extending classes may override this to import parameters from
	// a previous reconstruction to its method specific form parameters
	// $iter holds the values entered into the database in the ApRefinIterData
	// table and method specific tables specified by getIterationInfo() in 
	// particledata.inc.
	// use statement like this: $paramSet->addIterationToValue( "wgh", $iter['wgh'] );
	// to map the database column name to the form parameter name.
	protected function addImportedRefineIter( $paramSet, $iter ) {}
	
	// outputs the html required to display the general refine parameters
	final public function generalParamForm( ) 
	{
		// display the heading
		$html .= "
	    <br />
	    <H4 style='align=\'center\' >General Refinement Parameters</H4>
	    <hr />";
	
		// display a form allowing users to fill in parameters with default or imported values
		$html .= $this->defaultOptionsForm();

		// if the user selects to import parameters, get the values here
		$defaultSetId = $_POST['import'];
		$paramSet = $this->setFormParams( $defaultSetId );

		// extending classes must define a method type
		$method = $this->getMethodType();
		$html .= "** Fields that may be specified per iteration should be entered in the format 'iterations'x'value'.<br />";
		$html .= "** Disabled fields are not available for $method procedures. <br />";
	
		$html .= "<br />\n";
		$html .= "<b>Particle dependent parameters</b>\n";
		$html .= "<br />\n";
		
		$shortSize = 4;
		$longSize = 20;
		
		$html .= $paramSet->insertTextField( "outerMaskRadius", $longSize, "(&Aring;ngstroms)" );
		$html .= $paramSet->insertTextField( "innerMaskRadius", $longSize, "(&Aring;ngstroms)" );
		$html .= $paramSet->insertTextField( "outerAlignRadius", $longSize, "(&Aring;ngstroms)" );
		$html .= $paramSet->insertTextField( "innerAlignRadius", $longSize, "(&Aring;ngstroms)" );
		$html .= $paramSet->insertTextField( "symmetry", $longSize );
			
		$html .= "<br />\n";
		$html .= "<br />\n";
		$html .= "<b>Particle independent parameters</b>\n";
		$html .= "<br />\n";
		
		$html .= $paramSet->insertTextField( "numIters", $shortSize );
		$html .= $paramSet->insertTextField( "angSampRate", $longSize );
		$html .= $paramSet->insertTextField( "percentDiscard", $longSize );
		
		$html .= "<br/>\n";
	
		$html .= $paramSet->insertCheckboxField( "filterEstimated" );
		$html .= "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n";
		$html .= $paramSet->insertTextField( "filterResolution", $shortSize, "(&Aring;ngstroms)" );

		$html .= "<br/>\n";

		$html .= $paramSet->insertCheckboxField( "filterComputed" );
		$html .= "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n";
		$html .= $paramSet->insertTextField( "filterConstant", $shortSize, "(&Aring;ngstroms)" );
		
		$html .= "<br/><br/>\n";
		
		return $html;
	}
		
	// builds the run command and shows or submits the command
	// $errorCallbackFunc is the functions that displays the form
	// and calls this function....
	final public function createRunCommand( $postArray, $errorCallbackFunc, $commandAddOn='' ) 
	{
		/* ***********************************
		 PART 1: Get variables from POST array
		 ************************************* */
		$paramSet = $this->createFormParams();
		$paramSet->getPostedValues( $postArray );
		
		/* *******************
		 PART 2: Check for conflicts, if there is an error display the form again
		 ******************** */
		$errorMsg = $paramSet->validate();
		if ( $errorMsg ) $errorCallbackFunc( $errorMsg );

		/* *******************
		 PART 3: Create program command
		 ******************** */
		$command = $this->buildCommand( $paramSet );		

		// add parameters from other forms
		$command .= $commandAddOn;
	
		/* *******************
		 PART 4: Create header info, i.e., references
		 ******************** */
		// Add reference to top of the page
		$headinfo .= showReference( $this->method );
	
		/* *******************
		 PART 5: Show or Run Command
		 ******************** */
		// submit command
		$errors = showOrSubmitCommand($command, $headinfo, 'prepfrealign', $nproc);
		// if error display them
		if ($errors) $errorCallbackFunc($errors);
		exit;
	}
	
	// set the default values that are populated
	// when the user selects the "Set Defaults" button.
	// $box is the box size from the selected stack.
	// Extending classes should override this to set the 
	// values to something that makes sense for the method
	// and add method specific values.
	public function setDefaults()
	{
		$stack = $this->getStackInfo();
		$box = $stack['box'];
		
		$rad = ($box/2)-2;
		$javafunc = "
	  <script type='text/javascript'>
	    function setDefaults(obj) {
	      if (obj.outerMaskRadius) obj.outerMaskRadius.value = $rad;
	      if (obj.innerMaskRadius) obj.innerMaskRadius.value = 0;
	      if (obj.innerAlignRadius) obj.innerAlignRadius.value = '4';
	      if (obj.outerAlignRadius) obj.outerAlignRadius.value = $rad;
	      if (obj.symmetry) obj.symmetry.value = 'c1';
	      if (obj.numIters) obj.numIters.value = '10';
	      if (obj.angSampRate) obj.angSampRate.value = '4x10 2x5 2x3 2x2';
	      if (obj.percentDiscard) obj.percentDiscard.value = '10';
	      if (obj.filterEstimated) obj.filterEstimated.checked = false;
	      if (obj.filterResolution) obj.filterResolution.value = '';
	      if (obj.filterComputed ) obj.filterComputed.checked = true;
	      if (obj.filterConstant) obj.filterConstant.value = '0.1';
	      return;
	    }
	  </script>\n";
		return $javafunc;
	}

	function additionalJavaScript() 
	{
	}

}

// Extend the FormParameters class to contain all the general refine params.
// Extending classes may extend RefineFomParameters to add package specific 
// parameters as well.
class RefineFormParameters extends FormParameters
{
	function __construct( $id='', $label='', $outerMaskRadius='', $innerMaskRadius='', $outerAlignRadius='', 
							$innerAlignRadius='', $symmetry='', $numIters='', $angSampRate='', $percentDiscard='',  
							$filterEstimated='', $filterResolution='', $filterComputed='', $filterConstant='' ) 
	{
		parent::__construct();
		
		$this->id = $id;
		$this->label = $label;
		
		$this->addParam( "outerMaskRadius", $outerMaskRadius, "outer mask radius" );
		$this->addParam( "innerMaskRadius", $innerMaskRadius, "inner mask radius" );
		$this->addParam( "outerAlignRadius", $outerAlignRadius, "outer alignment radius" );
		$this->addParam( "innerAlignRadius", $innerAlignRadius, "inner alignment radius" );
		$this->addParam( "symmetry", $symmetry, "symmetry group" );
		$this->addParam( "numIters", $numIters, "number of iterations" );
		$this->addParam( "angSampRate", $angSampRate, "angular sampling rate" );
		$this->addParam( "percentDiscard", $percentDiscard, "percentage of worst images to discard" );
		$this->addParam( "filterEstimated", $filterEstimated, "filter reconstructed volume to estimated resolution" );
		$this->addParam( "filterResolution", $filterResolution, "resolution" );
		$this->addParam( "filterComputed", $filterComputed, "filter reconstructed volume to resolution computed by FSC" );
		$this->addParam( "filterConstant", $filterConstant, "add constant to computed filter value" );
		
		// add parameter requirements
		$this->addValidation( "numIters", "req" );
		$this->addValidation( "numIters", "num" );
	}
	
	// update the value of a parameter to reflect an 
	// additional iteration value. The result is in the 
	// format "iterations"x"value": so a resulting value string
	// could be "5x4:6x2" which means to run 5 iterations with 
	// a value of 4 followed by 6 iterations at a value of 2.
	function addIterationToValue( $name, $newIterValue )
	{
		// NULL values should be added as empty, in case 
		// early iterations are NULL and later ones are set.
		//if ( $newIterValue == NULL ) return;
		
		$currValue = $this->getParamValue( $name );
		
		// separate the current value into its iterations
		$currIterations = explode(":", $currValue);
		
		// go to the last iteration and see if the new iteration value matches 
		// the value of the last iteration of the current value
		$currIterCount 	= count( $currIterations );		
		$lastIterPos 	= $currIterCount-1;
		$lastIter 		= $currIterations[$lastIterPos];
		
		list($numIters, $value) = explode( "x", $lastIter );
		if ( $newIterValue == $value ) {
			// rebuild the value string, updating the last iteration  
			for ( $i=0; $i < $lastIterPos; $i++ ) {
				$newValueString .= ":".$currIterations[$i];
			}
			$numIters++;
			$newValueString .= ":".$numIters."x".$value;
		} else {
			// add a new iter to current value
			$newValueString = $currValue.":1x".$newIterValue;
		}		
		
		// remove any leading or following colons from the string
		$newValueString = trim( $newValueString, ":" );
		
		$this->setParamValue( $name, $newValueString );
	}
	
	// Appends a new command flag to a command string
	// If value is not passed, the param value is looked up.
	// If $paramName is not passed, it is assumed to be the same 
	// as the flag name.
	// If the value is an empty string, it is not added to the command.
	// Returns the new command string.
	function addCommandFlag( $command, $flagName, $paramName='', $value='' )
	{
		if ( $paramName == '' ) {
			$paramName = $flagName;
		}
		if ( $value === '' ) {
			$value = $this->getParamValue( $paramName );
		}
		if ( $value !== '' ) {
			$command .= "--".$flagName."=".$value." ";
		}
		
		return $command;
	}
}


?>