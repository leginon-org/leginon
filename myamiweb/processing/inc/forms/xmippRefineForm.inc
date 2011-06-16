<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

//--------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------

require_once "basicRefineForm.inc";


class XmippRefineForm extends BasicRefineForm 
{
	public function createFormParams() { return new XmippParams(); }
	
	public function advancedParamForm()
	{
		// classes extended from BasicRefineForm should get the selected default values
		$params = $this->getFormParams();
		
		// display form title
		$html .="
	    <br />
	    <H4>Xmipp Reconstruction Parameters</H4>
	    <hr />";
		
		$shortSize = 4;
		$longSize = 20;
		
		$html .= $params->insertTextField( "mask", $longSize, "(if you use this field you cannot use Mask Radius)" );
		$html .= $params->insertTextField( "maxAngularChange", $longSize );
		$html .= $params->insertTextField( "maxChangeOffset", $longSize );
		$html .= $params->insertTextField( "search5DShift", $longSize );
		$html .= $params->insertTextField( "search5DStep", $longSize );
		$html .= $params->insertTextField( "reconMethod", $longSize );
		$html .= $params->insertTextField( "ARTLambda", $longSize );
		$html .= $params->insertTextField( "fourierMaxFrequencyOfInterest",  $shortSize );
		
		$html .= $params->insertCheckboxField( "doComputeResolution" );
		$html .= "<br/>\n";	
		
		return $html;
	}
	
	public function buildCommand( $params )
	{
		
		$command ='prepXmipp.py ';
	    $command.='--projectid='.$projectid.' ';
	    $command.='--stackid='.$stackidval.' ';
	    $command.='--modelid='.$modelid.' ';
	    $command.='--rundir=. ';
	    $command.='--pixelSize='.$apix.' ';
	    $command.='--boxSize='.$box.' ';
	    $command.='--NumberOfIterations='.$params->getParamValue("numIters").' ';
	    $command.='--MaskRadius='.$params->getParamValue("outerMaskRadius").' ';
	    $command.='--Mask='.$params->getParamValue("mask").' ';
	    $command.='--InnerRadius='.$params->getParamValue("innerAlignRadius").' ';
	    $command.='--OuterRadius='.$params->getParamValue("outerAlignRadius").' ';
	    $command.='--AngularSteps='.$params->getParamValue("angSampRate").' ';
	    $command.='--MaxAngularChange='.$params->getParamValue("maxAngularChange").' ';
	    $command.='--MaxChangeOffset='.$params->getParamValue("maxChangeOffset").' ';
	    $command.='--Search5DShift='.$params->getParamValue("search5DShift").' ';
	    $command.='--Search5DStep='.$params->getParamValue("search5DStep").' ';
	    $command.='--SymmetryGroup='.$params->getParamValue("symmetry").' ';
	    $command.='--DiscardPercentage='.$params->getParamValue("percentDiscard").' ';
	    $command.='--ReconstructionMethod='.$params->getParamValue("reconMethod").' ';
	    $command.='--ARTLambda='.$params->getParamValue("ARTLambda").' ';
	    $command.='--FourierMaxFrequencyOfInterest='.$params->getParamValue("fourierMaxFrequencyOfInterest").' ';
	    
	    $doComputeResolution 	= $params->getParamValue("doComputeResolution");
	    $filterComputed 		= $params->getParamValue("filterComputed");
	    $filterEstimated 		= $params->getParamValue("filterEstimated");
	    
	    if ( !empty($doComputeResolution) )
	        $command.='--DoComputeResolution ';
	    if ( !empty($filterComputed) || !empty($filterEstimated) ) 
	        $command.='--DoLowPassFilter ';
	    if ( !empty($filterEstimated) )
	        $command.='--DontUseFscForFilter ';
	    $command.='--ConstantToAddToFiltration='.$params->getParamValue("filterConstant").' ';	
	    			
		return $command;
	}
	
	// @override
	protected function setImportParams()
	{
		// add default value sets to populate the import parameters form 
		$id 				= 'asymm';
		$label 				= 'asymmetric particles';
		$outerMaskRadius 	= '';
		$innerMaskRadius 	= '';
		$outerAlignRadius 	= '';	 
		$innerAlignRadius 	= ''; 
		$symmetry 			= 'c1'; 
		$numIters 			= '10'; 
		$angSampRate 		= '2x12:2x10:2x8:2x6:2x5:2x4:2x3:2x2';
		$percentDiscard 	= '10';  
		$filterEstimated 	= ''; 
		$filterResolution	= ''; 
		$filterComputed 	= 'CHECKED'; 
		$filterConstant 	= '0.1';
		$mask 				= ''; 
		$maxAngularChange 	= '4x1000:2x20:2x9:2x6'; 
		$maxChangeOffset 	= '1000';
		$search5DShift 		= '4x5:0';
		$search5DStep 		= '2';
		$reconMethod 		= 'fourier';
		$ARTLambda 			= '0.15'; 
		$doComputeResolution = 'CHECKED';
		$fourierMaxFrequencyOfInterest = '0.25';
		
		$asymmSet = new XmippParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$mask, $maxAngularChange, $maxChangeOffset, $search5DShift, $search5DStep,
							$reconMethod, $ARTLambda, $doComputeResolution, $fourierMaxFrequencyOfInterest );
		$this->addDefaultParams( $asymmSet );

		$id 				= 'low';
		$label 				= 'low symmetry particles';
		$maxAngularChange 	= '4x1000:2x20:2x9:2x6:5x4';
		$lowSet = new XmippParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$mask, $maxAngularChange, $maxChangeOffset, $search5DShift, $search5DStep,
							$reconMethod, $ARTLambda, $doComputeResolution, $fourierMaxFrequencyOfInterest );
		$this->addDefaultParams( $lowSet );
		
		$id 				= 'icos';
		$label 				= 'icosahedral particles';
		$maxAngularChange 	= '4x1000:2x10:2x8:2x6:5x4';
		$icosSet = new XmippParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$mask, $maxAngularChange, $maxChangeOffset, $search5DShift, $search5DStep,
							$reconMethod, $ARTLambda, $doComputeResolution, $fourierMaxFrequencyOfInterest );
		$this->addDefaultParams( $icosSet );
	}
	
	// set the default values that are populated
	// when the user selects the "Set Defaults" button.
	// $box is the box size from the selected stack.
	public function setDefaults($box)
	{
		$rad = ($box/2)-2;
		$javafunc = "
	  <script type='text/javascript'>
	    function setDefaults(obj) {
	      if (obj.outerMaskRadius) obj.outerMaskRadius.value = $rad;
	      if (obj.innerMaskRadius) obj.innerMaskRadius.value = $rad;
	      if (obj.innerAlignRadius) obj.innerAlignRadius.value = '4';
	      if (obj.outerAlignRadius) obj.outerAlignRadius.value = $rad;
	      if (obj.symmetry) obj.symmetry.value = 'c1';
	      if (obj.numIters) obj.numIters.value = '10';
	      if (obj.angSampRate) obj.angSampRate.value = '4x10:2x5:2x3:2x2';
	      if (obj.percentDiscard) obj.percentDiscard.value = '10';
	      if (obj.filterEstimated) obj.filterEstimated.checked = false;
	      if (obj.filterResolution) obj.filterResolution.value = '';
	      if (obj.filterComputed ) obj.filterComputed.checked = true;
	      if (obj.filterConstant) obj.filterConstant.value = '0.1';
	      if (obj.mask) obj.mask.value = '';
	      if (obj.maxAngularChange) obj.maxAngularChange.value = '4x1000:2x20:2x9:2x6';
	      if (obj.maxChangeOffset) obj.maxChangeOffset.value = '1000';
	      if (obj.search5DShift) obj.search5DShift.value = '4x5:0';
	      if (obj.search5DStep) obj.search5DStep.value = '2';
	      if (obj.reconMethod) obj.reconMethod.value = 'fourier';
	      if (obj.ARTLambda) obj.ARTLambda.value = '0.15';
	      if (obj.doComputeResolution) obj.doComputeResolution.checked = true;
	      if (obj.fourierMaxFrequencyOfInterest) obj.fourierMaxFrequencyOfInterest.value = '0.25';

	      return;
	    }
	  </script>\n";
		return $javafunc;
	}
	
	
}

// extend the RefineFormParameters class to add the xmipp 
// advanced parameter default values. 
class XmippParams extends RefineFormParameters
{
	function __construct( $id='', $label='', $outerMaskRadius='', $innerMaskRadius='', $outerAlignRadius='', 
							$innerAlignRadius='', $symmetry='', $numIters='', $angSampRate='', $percentDiscard='',  
							$filterEstimated='', $filterResolution='', $filterComputed='', $filterConstant='',
							$mask='', $maxAngularChange='', $maxChangeOffset='', $search5DShift='', $search5DStep='',
							$reconMethod='', $ARTLambda='', $doComputeResolution='', $fourierMaxFrequencyOfInterest='' ) 
	{
		parent::__construct($id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant );
									
		$this->addParam( "mask", $mask, "Mask filename" );
		$this->addParam( "maxAngularChange", $maxAngularChange, "Max. Angular change " );		
		$this->addParam( "maxChangeOffset", $maxChangeOffset, "Maximum change offset " );
		$this->addParam( "search5DShift", $search5DShift, "Search range for 5D translational search " );
		$this->addParam( "search5DStep", $search5DStep, "Step size for 5D translational search " );
		$this->addParam( "reconMethod", $reconMethod, "Reconstruction method " );
		$this->addParam( "ARTLambda", $ARTLambda, "Values of lambda for ART " );
		$this->addParam( "doComputeResolution", $doComputeResolution, "Compute resolution? " );
		$this->addParam( "fourierMaxFrequencyOfInterest", $fourierMaxFrequencyOfInterest, "Initial maximum frequency used by reconstruct fourier " );
		
		// disable any general params that do not apply to this method
		$this->hideParam("innerMaskRadius");		
	}
	
	function validate() 
	{
		$msg = parent::validate();

		if ( !empty($this->params["mask"]["value"]) && !empty($this->params["outerMaskRadius"]["value"]) )
			$msg .= "<b>Error:</b> You may not define both the outer mask raduis and a mask file.";
				
		return $msg;
	}
}

?>
