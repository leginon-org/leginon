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
	
	function __construct(  ) 
	{
	}
		
	// TUTORIAL: "abstract" means that extending classes MUST define this function
	// ex: public getMethodType() { return "eman"; } 
	abstract public function getMethodType(); 
	abstract public function buildCommand( $params ); 
	
	public function advancedParamForm() {}
	public function setAdvancedDefaults() {}
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
		$asymmSet = new RefineFormParameters('asymm', 'asymmetric particles',1,1,1,1,1,1,1,1,'',1,'checked',1);
		$this->addDefaultParams( $asymmSet );
	}
		
	final protected function addDefaultParams( $newSet )
	{
		$this->defaultParamSets[$newSet->id] = $newSet;
	}
	
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
	final protected function getFormParams()
	{
		return $this->selectedParams;
	}
	
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
	
		echo "<input type='BUTTON' onClick='setDefaults(this.form)' VALUE='Set Defaults'>\n";
		echo "<select name='import' onChange='prepRefine.submit()'>\n";
		echo "<option>Import parameters</option>\n";
		foreach ($this->defaultParamSets as $defaultSet) {
			echo "<option value='$defaultSet->id'>$defaultSet->label</option>\n";
		}
		echo "<option value=''>------------------------------</option>\n";
		echo $ropt;
		echo "</select>\n";
		echo "<br />\n";
		echo "<br />\n";
	}	
	
	final protected function importParamsFromRefinement( $defaultSetId )
	{
		$particle = new particledata();
		$iterinfo = $particle->getIterationInfo( $defaultSetId );
		
		// get initial model info
		$refinfo 	= $particle->getRefinementRunInfo( $defaultSetId );
		$initmodel 	= $particle->getInitModelInfo($refinfo['REF|ApInitialModelData|initialModel']);
		$stackinfo 	= $particle->getStackParams($refinfo['REF|ApStackData|stack']);
		
		// get scaling factor for box sizes
		$prevboxsize	= $stackinfo['boxsize'];
		$boxscale 		= $box / $prevboxsize;
		$numiters 		= count($iterinfo);
		
		// TODO: refactor this to work in xmipp format
		for ( $i=1; $i<=$numiters; $i++ ) {
			$angn="ang".$i;
			$maskn="mask".$i;
			$imaskn="imask".$i;
			$amask1n="amask1".$i;
			$amask2n="amask2".$i;
			$amask3n="amask3".$i;
			$symn="sym".$i;
			$maxshiftn="maxshift".$i;
			$hardn="hard".$i;
			$classkeepn="classkeep".$i;
			$classitern="classiter".$i;
			$filt3dn="filt3d".$i;
			$shrinkn="shrink".$i;
			$euler2n="euler2".$i;
			$xfilesn="xfiles".$i;
			#$perturbn="perturb".$i;
			$treen="tree".$i;
			$mediann="median".$i;
			$phaseclsn="phasecls".$i;
			#$fsclsn="fscls".$i;
			$refinen="refine".$i;
			#$goodbadn="goodbad".$i;
			$eotestn="eotest".$i;
			$corann="coran".$i;
			$coranCCn="coranCC".$i;
			$coranmaskn="coranmask".$i;
			$coranlpn="coranlp".$i;
			$coranhpn="coranhp".$i;
			$coranhccn="coranhcc".$i;
			$affpropn="affprop".$i;
			$affpropCCn="affpropCC".$i;
			$affpropMPn="affpropMP".$i;
			
			foreach ($iterinfo as $iter) {
				if ($iter['iteration'] == $i) {
					$ang=$iter['ang'];
					$mask=ceil($iter['mask']*$boxscale);
					if (floor($iter['imask']*$boxscale) > 0)
						$imask=floor($iter['imask']*$boxscale);
					$amask1=$iter['EMAN_amask1'];
					$amask2=$iter['EMAN_amask2'];
					$amask3=$iter['EMAN_amask3'];
					$maxhsift=$iter['EMAN_maxshift'];
					$hard=$iter['EMAN_hard'];
					$classiter=$iter['EMAN_classiter'];
					$classkeep=$iter['EMAN_classkeep'];
					$filt3d=$iter['EMAN_filt3d'];
					$shrink=$iter['EMAN_shrink'];
					$euler2=$iter['EMAN_euler2'];
					$xfiles=$iter['EMAN_xfiles'];
					$median = ($iter['EMAN_median']) ? 'CHECKED' : '';
					$phasecls = ($iter['EMAN_phasecls']) ? 'CHECKED' : '';
					#$fscls = ($iter['EMAN_fscls']) ? 'CHECKED' : '';
					$refine = ($iter['EMAN_refine']) ? 'CHECKED' : '';
					#$goodbad = ($iter['EMAN_goodbad']) ? 'CHECKED' : '';
					$coran = ($iter['postRefineClassAverages']) ? 'CHECKED' : '';
					#$perturb = ($iter['EMAN_perturb']) ? 'CHECKED' : '';
					$eotest = ($iter['REF|ApResolutionData|resolution']) ? 'CHECKED' : '';
					$symmetry = $particle->getSymInfo($iter['REF|ApSymmetryData|symmetry']);
					if (!is_array($symmetry)) $sym=$modsym;
					else $sym = $symmetry['eman_name'];
					continue;
				}
			}
		}
		
	}
		
	final public function generalParamForm( ) 
	{
		// display the heading
		echo "
	    <br />
	    <H4 style='align=\'center\' >General Refinement Parameters</H4>
	    <hr />";
	
		// display a form allowing users to fill in parameters with default or imported values
		$this->defaultOptionsForm();

		// if the user selects to import parameters, get the values here
		$defaultSetId = $_POST['import'];
		$paramSet = $this->setFormParams( $defaultSetId );

		// extending classes must define a method type
		$method = $this->getMethodType();
		echo "** Fields that may be specified per iteration should be entered in the format 'iterations'x'value'.<br />";
		echo "** Disabled fields are not available for $method procedures. <br />";
	
		echo "<br />\n";
		echo "<b>Particle dependent parameters</b>\n";
		echo "<br />\n";
		
		$shortSize = 4;
		$longSize = 20;
		
		echo $paramSet->insertTextField( "outerMaskRadius", $shortSize, "(pixels)" );
		echo $paramSet->insertTextField( "innerMaskRadius", $shortSize, "(pixels)" );
		echo $paramSet->insertTextField( "outerAlignRadius", $shortSize, "(pixels)" );
		echo $paramSet->insertTextField( "innerAlignRadius", $shortSize, "(pixels)" );
		echo $paramSet->insertTextField( "symmetry", $shortSize );
			
		echo "<br />\n";
		echo "<br />\n";
		echo "<b>Particle independent parameters</b>\n";
		echo "<br />\n";
		
		echo $paramSet->insertTextField( "numIters", $shortSize );
		echo $paramSet->insertTextField( "angSampRate", $longSize );
		echo $paramSet->insertTextField( "percentDiscard", $longSize );
		
		echo "<br/>\n";
	
		echo $paramSet->insertCheckboxField( "filterEstimated" );
		echo "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n";
		echo $paramSet->insertTextField( "filterResolution", $shortSize, "(angstroms)" );

		echo "<br/>\n";

		echo $paramSet->insertCheckboxField( "filterComputed" );
		echo "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n";
		echo $paramSet->insertTextField( "filterConstant", $shortSize, "(angstroms)" );
		
		echo "<br/><br/>\n";
	}
		
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
		if ($errorMsg) $errorCallbackFunc($errorMsg);

		/* *******************
		 PART 3: Create program command
		 ******************** */
		$params = $paramSet->params;
		$command = $this->buildCommand($params);		

		// add parameters from other forms
		$command .= $commandAddOn;
	
		/* *******************
		 PART 4: Create header info, i.e., references
		 ******************** */
		// Add reference to top of the page
		$headinfo .= showReference($_POST['method']);
	
		/* *******************
		 PART 5: Show or Run Command
		 ******************** */
		// submit command
		$errors = showOrSubmitCommand($command, $headinfo, 'prepfrealign', $nproc);
		// if error display them
		if ($errors) $errorCallbackFunc($errors);
		exit;
	}
	
	public function setGeneralDefaults($box)
	{
		$rad = ($box/2)-2;
		$javafunc = "
	  <script type='text/javascript'>
	    function setDefaults(obj) {
	      obj.outerMaskRadius.value = $rad;
	      obj.innerMaskRadius.value = $rad;
	      obj.innerAlignRadius.value = '4';
	      obj.outerAlignRadius.value = $rad;
	      obj.SymmetryGroup.value = 'c1';
	      obj.NumberOfIterations.value = '10';
	      obj.AngularSteps.value = '4x10 2x5 2x3 2x2';
	      obj.DiscardPercentage.value = '10';
	      obj.filterEstRes.checked = false;
	      obj.filterResolution.value = '';
	      obj.filterFscRes.checked = true;
	      obj.filterConstant.value = '0.1';
	      return;
	    }
	  </SCRIPT>\n";
		return $javafunc;
	}

}

// I would like this to ba a nested class, but apparently PHP does not 
// yet support nested classes.
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
}

?>