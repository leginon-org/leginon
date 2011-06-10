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
	public function getMethodType() { return "xmipp"; }
	public function createFormParams() { return new XmippParams(); }
	
	public function advancedParamForm()
	{
		// classes extended from BasicRefineForm should get the selected default values
		$params = $this->getFormParams();
		
		// display form title
		echo"
	    <br />
	    <H4>Xmipp Reconstruction Parameters</H4>
	    <hr />";
		
		$shortSize = 4;
		$longSize = 20;
		
		echo $params->insertTextField( "mask", $longSize, "(if you use this field you cannot use Mask Radius)" );
		echo $params->insertTextField( "maxAngularChange", $longSize );
		echo $params->insertTextField( "maxChangeOffset", $longSize );
		echo $params->insertTextField( "search5DShift", $longSize );
		echo $params->insertTextField( "search5DStep", $longSize );
		echo $params->insertTextField( "reconMethod", $longSize );
		echo $params->insertTextField( "ARTLambda", $longSize );
		echo $params->insertTextField( "fourierMaxFrequencyOfInterest",  $shortSize );
		
		echo $params->insertCheckboxField( "doComputeResolution" );
		echo "<br/>\n";	

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
	    $command.='--NumberOfIterations='.$params["numIters"]["value"].' ';
	    $command.='--MaskRadius='.$params["outerMaskRadius"]["value"].' ';
	    $command.='--Mask='.$params["mask"]["value"].' ';
	    $command.='--InnerRadius='.$params["innerAlignRadius"]["value"].' ';
	    $command.='--OuterRadius='.$params["outerAlignRadius"]["value"].' ';
	    $command.='--AngularSteps='.$params["angSampRate"]["value"].' ';
	    $command.='--MaxAngularChange='.$params["maxAngularChange"]["value"].' ';
	    $command.='--MaxChangeOffset='.$params["maxChangeOffset"]["value"].' ';
	    $command.='--Search5DShift='.$params["search5DShift"]["value"].' ';
	    $command.='--Search5DStep='.$params["search5DStep"]["value"].' ';
	    $command.='--SymmetryGroup='.$params["symmetry"]["value"].' ';
	    $command.='--DiscardPercentage='.$params["percentDiscard"]["value"].' ';
	    $command.='--ReconstructionMethod='.$params["reconMethod"]["value"].' ';
	    $command.='--ARTLambda='.$params["ARTLambda"]["value"].' ';
	    $command.='--FourierMaxFrequencyOfInterest='.$params["fourierMaxFrequencyOfInterest"]["value"].' ';
	    
	    if ( !empty($params["doComputeResolution"]["value"]) )
	        $command.='--DoComputeResolution ';
	    if ( !empty($params["filterComputed"]["value"]) || !empty($params["filterEstimated"]["value"]) ) 
	        $command.='--DoLowPassFilter ';
	    if ( !empty($params["filterEstimated"]["value"]) )
	        $command.='--DontUseFscForFilter ';
	    $command.='--ConstantToAddToFiltration='.$params["filterConstant"]["value"].' ';	
	    			
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
		$this->disableParam("innerMaskRadius");		
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
