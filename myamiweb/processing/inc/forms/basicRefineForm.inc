<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

//--------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------

require_once "inc/particledata.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/summarytables.inc";
require_once "inc/forms/basicForm.inc";
require_once "../inc/formParameters.inc";


abstract class BasicRefineForm extends BasicForm
{
	private $stackInfo;
	private $defaultSym;
	protected $particle;
	
	function __construct( $method, $stacks='', $models='' ) 
	{
		parent::__construct();
		
		$this->particle = new particledata();
		
		$this->method = $method;
		$this->models = $models;
		$this->setParticleSymmetry( $models );
		$this->setPublications();
		
		if ( $stacks ) {
			$this->setStackInfo( $stacks );
		}
	}
	
	function __destruct() 
	{
		unset( $this->particle );
	}
	
	// extending classes should override this function and set the 
	// publication key list with key values that have been added 
	// to the array in publicationList.inc
	protected function setPublications()
	{
		$this->pubKeyList = array("appion");
	}
		
	// Extending classes should override this function to return the appropriate
	// class of form parameters if it has also extended the RefineFormParams class.
	// This createFormParams() function should always be used instead of 
	// directly creating an instance of RefineFormParameters.
	// GOOD: $params = $this->createFormParams();
	// BAD:  $params = new RefineFormParameters();
	public function createFormParams() { return new RefineFormParameters(); }
	
	private function setStackInfo( $stacks ) 
	{
		foreach ( $stacks as $stack ) {
			$isReconStack = $stack[recon];

			// make sure we are getting refine stack info rather than recon info
			if ( !$isReconStack ) {
				$this->stackInfo['lp'] 		= $stack[lowpass];
				$this->stackInfo['hp'] 		= $stack[highpass];
				$this->stackInfo['bin'] 	= $stack[bin];	
				$this->stackInfo['apix'] 	= $stack[apix];	
				$this->stackInfo['cs'] 		= $stack[cs];	
				$this->stackInfo['boxsize'] = $stack[boxsize];	
				$this->stackInfo['lastPart'] = $stack[last_part];
				$this->stackInfo['stackfilename'] = $stack[filename];
				$this->stackInfo['parent_apix'] = $stack[parent_pixelsize] / 1e-10; // the angstroms per pixel for the original stack the refine stack was made from
				$this->stackInfo['dstep'] = $stack[dstep];	
				
				break;
			}			
		}		
	}
	
	private function setParticleSymmetry( $models )
	{
		if ( $models ) {
			// For now, use the symmetry of the first available model
			$symmetryId = $models[0]['REF|ApSymmetryData|symmetry'];
			$symInfo 	= $this->particle->getSymInfo($symmetryId);
			$this->defaultSym = $symInfo['symmetry'];
		} else {
			$this->defaultSym = "C7 (z)";
		}
		
	}
	
	// getters
	public function getStackInfo()  { return $this->stackInfo; }
	public function getMethodType() { return $this->method; } 
	public function getSymmetry()   { return $this->defaultSym; } 
	
	// Extending classes MAY override this to add 
	// package specific parameters to the refine form 
	public function advancedParamForm() {}
		
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
		
	// points the form parameters to the correct set of default
	// values based on the users selection.
	// Takes the default set Id, which corresponds to a set available
	// in the "Import Parameters" drop down list.
	final protected function updateFormParams( $defaultSetId='' )
	{
		if (is_numeric( $defaultSetId ) ) {
			// the user just selected an existing refine run to import params from
			$this->importParamsFromRefinement( $defaultSetId );
		} else {
			parent::updateFormParams( $defaultSetId );
		}				
	}
	
	// Add import parameters drop down selector.
	final private function defaultOptionsForm()
	{
		$this->setImportParams();
		$defaultParamSets = $this->getDefaultParamSets();
		
		$leginondata = new leginondata();
	
		// import values from previous uploaded reconstruction
		$projectId = getProjectId();
		$sessions = $leginondata->getSessions("",$projectId);
		if (is_array($sessions)) {
			$ropt = "";
			foreach ($sessions as $s) {
				$recons = $this->particle->getReconIdsFromSession($s['id']);
				if (is_array($recons)) {
					foreach ($recons as $r) {
						// Only include previous runs that were using the same method/package
						// The database tends to store the package name as "EMAN", "Xmipp", "XmippML3D", or "Frealign",
						// While the web page is using "emanrecon", "xmipprecon", etc. Would be good to standardize some day. 
						$methodstring = $r['package']."recon";
						if ( strcasecmp($r['package'], $this->method) === 0 || strcasecmp($methodstring, $this->method) === 0 ) {
							// limit the length of the description
							$description = substr($r['description'], 0, 50);
							$ropt.= "<option value='".$r['DEF_id']."'>";
							$ropt.= $s['name']." : ";
							$ropt.= $r['name']." - ".$description;
							$ropt.= "</option>\n";
						}
					}
				}
			}
		}
	
		// when the import box selection changes, reload the form
		$html .= "<select name='import' onChange='this.form.submit()'>\n";
		$html .= "<option>Import parameters</option>\n";
		foreach ($defaultParamSets as $defaultSet) {
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
		$paramSet = $this->getFormParams();
		
		// set the symmetry to our default value which is based on the initial model		
		$symmetry = $this->getSymmetry();
		$paramSet->setParamValue( "symmetry", $symmetry );
		
		// get import refine stack info
		$refinfo 			= $this->particle->getRefinementRunInfo( $defaultSetId );
		$importStackInfo 	= $this->particle->getStackParams($refinfo['REF|ApStackData|stack']);
		$import_apix 		= $importStackInfo['pixelsize'] / 1e-10;
		
		// get our stack info
		$stackInfo 	= $this->getStackInfo();
		$box 		= $stackInfo['boxsize'];
		$parent_apix = $stackInfo['parent_apix'];
		
		// use the two stacks to get scaling factor for box sizes
		$importBox 	= $importStackInfo['boxsize'];
		$boxscale 	= $box / $importBox;
		
		// set the number of iterations
		$iterinfo = $this->particle->getIterationInfo( $defaultSetId );
		$endIter = count($iterinfo);
		$paramSet->setParamValue( "endIter", $endIter );
				
		// add each iteration value to our forms parameters
		for ( $i = 1; $i <= $endIter; $i++ ) {
			foreach ($iterinfo as $iter) {
				if ($iter['iteration'] == $i) {
					// The masks are stored as pixels in the database, so when importing from a prior run,
					// we need to multiply the original stack apix by the recorded mask pixel to get the angstroms				
					$outerMaskRadius = ceil($iter['mask']*$import_apix);
					$paramSet->addIterationToValue( "outerMaskRadius", $outerMaskRadius ); // in angstroms
					
					if (floor($iter['imask']*$import_apix) > 0)
						$paramSet->addIterationToValue( "innerMaskRadius", floor($iter['imask']*$import_apix) ); // in angstroms
						
					$this->addImportedRefineIter( $paramSet, $iter );
						
					continue;
				}
			}
		}		
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
		// Add Set Defaults button
		$html .= "<input type='BUTTON' onClick='setDefaults(this.form)' VALUE='Set Defaults'>\n";
		
		// display a form allowing users to fill in parameters with default or imported values
		$html .= $this->defaultOptionsForm();

		// if the user selects to import parameters, get the values here
		$defaultSetId = $_POST['import'];
		$this->updateFormParams( $defaultSetId );
		$paramSet = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$paramSet->setHelpSection( "basicrefine" );		

		// extending classes must define a method type
		$method = $this->getMethodType();
		$html .= "** Fields that may be specified per iteration should be entered in the format 'iterations'x'value'.<br />";
		$html .= "Example: 2x8:2x3:3x5 reads as 2 iters with value 8 followed by 2 iters at 3 then 3 iters at 5. <br />";
	
		$html .= "<br />\n";
		$html .= "<b>Particle dependent parameters</b>\n";
		$html .= "<br />\n";
		
		$shortSize = 4;
		$longSize = 20;
		
		$html .= $paramSet->insertTextField( "innerMaskRadius", $longSize, "(&Aring;ngstroms)" );
		$html .= $paramSet->insertTextField( "outerMaskRadius", $longSize, "(&Aring;ngstroms)" );
		$html .= $paramSet->insertTextField( "innerAlignRadius", $longSize, "(&Aring;ngstroms)" );
		$html .= $paramSet->insertTextField( "outerAlignRadius", $longSize, "(&Aring;ngstroms)" );
		$html .= $this->insertSymmetrySelectionBox( "symmetry", $paramSet->getParamValue("symmetry") );
		$html .= "&nbsp;";
		$html .=  docpop( "basicrefine.symmetry", $paramSet->getParamLabel("symmetry") );

		// only display this label if any of the following params are not hidden 
		if ( !($paramSet->isHidden("endIter") &&
			$paramSet->isHidden("endIter") &&
			$paramSet->isHidden("endIter") &&
			$paramSet->isHidden("endIter") &&
			$paramSet->isHidden("endIter") &&
			$paramSet->isHidden("endIter") &&
			$paramSet->isHidden("endIter")) ) {
				$html .= "<br />\n";
				$html .= "<br />\n";
				$html .= "<b>Particle independent parameters</b>\n";
				$html .= "<br />\n";
			}
		
		$html .= $paramSet->insertTextField( "endIter", $shortSize );
		$html .= $paramSet->insertTextField( "angSampRate", $longSize );
		$html .= $paramSet->insertTextField( "percentDiscard", $longSize );
		
		$html .= "<br/>\n";
	
		$html .= $paramSet->insertCheckboxField( "filterEstimated" );
		$html .= "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n";
		$html .= $paramSet->insertTextField( "filterResolution", $shortSize, "(&Aring;ngstroms)" );

		$html .= "<br/>\n";

		$html .= $paramSet->insertCheckboxField( "filterComputed" );
		$html .= "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n";
		$html .= $paramSet->insertTextField( "filterConstant", $shortSize, "(<b>digital frequency</b>)" );
		
		$html .= "<br/><br/>\n";
		
		return $html;
	}
	
	// returns the html to display a drop down selection box
	// containing all the available symmetry values as defined
	// in the apSymmetry table. 
	// Name is the name of the form parameter
	// Value is the currently selected symmetry id 
	// TODO: this is awfully similar to the box in UploadModel.php...merge? 
	function insertSymmetrySelectionBox( $name, $value ) 
	{
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
		
	// set the default values that are populated
	// when the user selects the "Set Defaults" button.
	// $box is the box size from the selected stack.
	// Extending classes should override this to set the 
	// values to something that makes sense for the method
	// and add method specific values.
	public function setDefaults()
	{
		$stack = $this->getStackInfo();
		$box = $stack['boxsize'];
		$apix = $stack['apix'];
		$sym = $this->getSymmetry();
		
		// make sure radius is smaller than half of the box size
		$radPix = ($box/2)-2;
		$radAng = round($radPix * $apix);
		$javafunc = "
	  <script type='text/javascript'>
	    function setDefaults(obj) {
	      if (obj.outerMaskRadius) obj.outerMaskRadius.value = $radAng;
	      if (obj.innerMaskRadius) obj.innerMaskRadius.value = 0;
	      if (obj.innerAlignRadius) obj.innerAlignRadius.value = '4';
	      if (obj.outerAlignRadius) obj.outerAlignRadius.value = $radAng;
	      if (obj.symmetry) obj.symmetry.value = '$sym';
	      if (obj.endIter) obj.endIter.value = '10';
	      if (obj.angSampRate) obj.angSampRate.value = '4x10 2x5 2x3 2x2';
	      if (obj.percentDiscard) obj.percentDiscard.value = '10';
	      if (obj.filterEstimated) obj.filterEstimated.checked = false;
	      if (obj.filterResolution) obj.filterResolution.value = '';
	      if (obj.filterComputed ) obj.filterComputed.checked = true;
	      if (obj.filterConstant) obj.filterConstant.value = '0.01';
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
							$innerAlignRadius='', $symmetry='', $endIter='', $angSampRate='', $percentDiscard='',  
							$filterEstimated='', $filterResolution='', $filterComputed='', $filterConstant='' ) 
	{
		parent::__construct( $id, $label );
				
		$this->addParam( "outerMaskRadius", $outerMaskRadius, "outer mask radius" );
		$this->addParam( "innerMaskRadius", $innerMaskRadius, "inner mask radius" );
		$this->addParam( "outerAlignRadius", $outerAlignRadius, "outer alignment radius" );
		$this->addParam( "innerAlignRadius", $innerAlignRadius, "inner alignment radius" );
		$this->addParam( "symmetry", $symmetry, "symmetry group" );
		$this->addParam( "endIter", $endIter, "number of iterations" );
		$this->addParam( "angSampRate", $angSampRate, "angular sampling rate" );
		$this->addParam( "percentDiscard", $percentDiscard, "percentage of worst images to discard" );
		$this->addParam( "filterEstimated", $filterEstimated, "filter reconstructed volume to estimated resolution" );
		$this->addParam( "filterResolution", $filterResolution, "resolution" );
		$this->addParam( "filterComputed", $filterComputed, "filter reconstructed volume to resolution computed by FSC" );
		$this->addParam( "filterConstant", $filterConstant, "add constant to computed filter value" );
		
		// add parameter requirements
		$this->addValidation( "endIter", "req" );
		$this->addValidation( "endIter", "num" );
		$this->addValidation( "symmetry", "req" );
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
		// TODO: python side can't handle "1x" yet so just return on null for now.
		if ( $newIterValue == NULL ) return;
		
		$currValue = $this->getParamValue( $name );
		
		// separate the current value into its iterations
		$currIterations = explode(":", $currValue);
		
		// go to the last iteration and see if the new iteration value matches 
		// the value of the last iteration of the current value
		$currIterCount 	= count( $currIterations );		
		$lastIterPos 	= $currIterCount-1;
		$lastIter 		= $currIterations[$lastIterPos];
		
		list($endIter, $value) = explode( "x", $lastIter );
		if ( $newIterValue == $value ) {
			// rebuild the value string, updating the last iteration  
			for ( $i=0; $i < $lastIterPos; $i++ ) {
				$newValueString .= ":".$currIterations[$i];
			}
			$endIter++;
			$newValueString .= ":".$endIter."x".$value;
		} else {
			// add a new iter to current value
			$newValueString = $currValue.":1x".$newIterValue;
		}		
		
		// remove any leading or following colons from the string
		$newValueString = trim( $newValueString, ":" );
		
		$this->setParamValue( $name, $newValueString );
	}
}
?>
