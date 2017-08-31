<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

//--------------------------------------------------------------------------------------
//--------------------------------------------------------------------------------------

require_once "basicRefineForm.inc";


class XmippRefineForm extends BasicRefineForm 
{
	public function createFormParams() { return new XmippParams(); }
	
	protected function setPublications()
	{
		$this->pubKeyList = array("xmipp");
	}
	
	public function advancedParamForm()
	{
		// classes extended from BasicRefineForm should get the selected default values
		$params = $this->getFormParams();
		
		$params->setHelpSection( "xmipp" );		
		
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
	
	public function buildCommand( $postArray )
	{
		// make sure this forms params have been updated with the post array	
		$params = $this->getFormParams();
		$params->getPostedValues( $postArray );
		
		$command = '';
		$command = $this->addCommandFlag( $command, "endIter" );
		$command = $this->addCommandFlag( $command, "outerMaskRadius" );
		$command = $this->addCommandFlag( $command, "mask" );
		$command = $this->addCommandFlag( $command, "innerAlignRadius" );
		$command = $this->addCommandFlag( $command, "outerAlignRadius" );
		$command = $this->addCommandFlag( $command, "angSampRate" );
		$command = $this->addCommandFlag( $command, "maxAngularChange" );
		$command = $this->addCommandFlag( $command, "maxChangeOffset" );
		$command = $this->addCommandFlag( $command, "search5DShift" );
		$command = $this->addCommandFlag( $command, "search5DStep" );
		$command = $this->addCommandFlag( $command, "symmetry" );
		$command = $this->addCommandFlag( $command, "percentDiscard" );
		$command = $this->addCommandFlag( $command, "reconMethod" );
		$command = $this->addCommandFlag( $command, "ARTLambda" );
		$command = $this->addCommandFlag( $command, "fourierMaxFrequencyOfInterest" );
		
	    $doComputeResolution 	= $params->getParamValue("doComputeResolution");
	    $filterComputed 		= $params->getParamValue("filterComputed");
	    $filterEstimated 		= $params->getParamValue("filterEstimated");

	    if ( $doComputeResolution == 'on' ) {
	        $command.=' --DoComputeResolution ';
	    }
	    if ( $filterComputed == 'on') {
	        $command.=' --DoLowPassFilter ';
	        $command = $this->addCommandFlag( $command, "filterConstant" );
	    }
	    if ( $filterEstimated == 'on' ) {
	        $command.=' --DoLowPassFilter ';
	        $command.=' --DontUseFscForFilter ';
	        $command = $this->addCommandFlag( $command, "filterResolution" );
	    }
	    			
		return $command;
	}
	
	// @override
	protected function setImportParams()
	{
		$sym = $this->getSymmetry();
		
		// add default value sets to populate the import parameters form 
		$id 				= 'asymm';
		$label 				= 'asymmetric particles';
		$outerMaskRadius 	= '';
		$innerMaskRadius 	= '';
		$outerAlignRadius 	= '';	 
		$innerAlignRadius 	= ''; 
		$symmetry 			= $sym; 
		$endIter 			= '10'; 
		$angSampRate 		= '4x10:2x5:2x3:2x2';
		$percentDiscard 	= '10';  
		$filterEstimated 	= ''; 
		$filterResolution	= ''; 
		$filterComputed 	= 'CHECKED'; 
		$filterConstant 	= '0.01';
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
							$innerAlignRadius, $symmetry, $endIter, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$mask, $maxAngularChange, $maxChangeOffset, $search5DShift, $search5DStep,
							$reconMethod, $ARTLambda, $doComputeResolution, $fourierMaxFrequencyOfInterest );
		$this->addDefaultParams( $asymmSet );

		$id 				= 'low';
		$label 				= 'low symmetry particles';
		$maxAngularChange 	= '4x1000:2x20:2x9:2x6:5x4';
		$lowSet = new XmippParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $endIter, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$mask, $maxAngularChange, $maxChangeOffset, $search5DShift, $search5DStep,
							$reconMethod, $ARTLambda, $doComputeResolution, $fourierMaxFrequencyOfInterest );
		$this->addDefaultParams( $lowSet );
		
		$id 				= 'icos';
		$label 				= 'icosahedral particles';
		$maxAngularChange 	= '4x1000:2x10:2x8:2x6:5x4';
		$icosSet = new XmippParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $endIter, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$mask, $maxAngularChange, $maxChangeOffset, $search5DShift, $search5DStep,
							$reconMethod, $ARTLambda, $doComputeResolution, $fourierMaxFrequencyOfInterest );
		$this->addDefaultParams( $icosSet );
	}
	
	protected function addImportedRefineIter( $paramSet, $iter ) 
	{
		$paramSet->addIterationToValue( "angSampRate", $iter['angularStep'] );
		$paramSet->addIterationToValue( "maxAngularChange", $iter['maxChangeInAngles'] );
		$paramSet->addIterationToValue( "maxChangeOffset", $iter['maxChangeOffset'] );
		$paramSet->addIterationToValue( "search5DShift", $iter['search5dShift'] );
		$paramSet->addIterationToValue( "search5DStep", $iter['search5dStep'] );
		$paramSet->addIterationToValue( "percentDiscard", $iter['discardPercentage'] );
		$paramSet->addIterationToValue( "reconMethod", $iter['reconstructionMethod'] );
		$paramSet->addIterationToValue( "ARTLambda", $iter['ARTLambda'] );
		$paramSet->addIterationToValue( "filterConstant", $iter['constantToAddToFiltration'] );
	}	
	
	// set the default values that are populated
	// when the user selects the "Set Defaults" button.
	// $box is the box size from the selected stack.
	public function setDefaults()
	{
		$stack = $this->getStackInfo();
		$box = $stack['boxsize'];
		$apix = $stack['apix'];
		$sym = $this->getSymmetry();
		
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
	      if (obj.angSampRate) obj.angSampRate.value = '4x10:2x5:2x3:2x2';
	      if (obj.percentDiscard) obj.percentDiscard.value = '10';
	      if (obj.filterEstimated) obj.filterEstimated.checked = false;
	      if (obj.filterResolution) obj.filterResolution.value = '';
	      if (obj.filterComputed ) obj.filterComputed.checked = true;
	      if (obj.filterConstant) obj.filterConstant.value = '0.01';
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
							$innerAlignRadius='', $symmetry='', $endIter='', $angSampRate='', $percentDiscard='',  
							$filterEstimated='', $filterResolution='', $filterComputed='', $filterConstant='',
							$mask='', $maxAngularChange='', $maxChangeOffset='', $search5DShift='', $search5DStep='',
							$reconMethod='', $ARTLambda='', $doComputeResolution='', $fourierMaxFrequencyOfInterest='' ) 
	{
		parent::__construct($id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $endIter, $angSampRate, $percentDiscard,  
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
			$msg .= "<b>Error:</b> You may not define both the outer mask radius and a mask file.";
				
		return $msg;
	}
}

?>
