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


class XmippML3DRefineForm extends BasicRefineForm 
{
	public function createFormParams() { return new XmippML3DParams(); }

	protected function setPublications()
	{
		$this->pubKeyList = array("xmipp", "scheres07", "scheres10");
	}
		
	public function advancedParamForm()
	{
		// classes extended from BasicRefineForm should get the selected default values
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "xmippml3d" );		
		
		$shortSize = 4;
		$longSize = 20;
		$html .= $params->insertCheckboxField( "ImagesArePhaseFlipped" );
//		$html .= $params->insertTextField( "HighResLimit", $longSize );
		$html .= $params->insertTextField( "ProjMatchSampling", $longSize );
		$html .= $params->insertTextField( "LowPassFilter", $longSize );
		$html .= $params->insertTextField( "NumberOfReferences", $longSize );
		$html .= $params->insertCheckboxField( "DoCorrectGreyScale" );
				
		return $html;
	}
	
	protected function setImportParams()
	{
		$sym = $this->getSymmetry();
		
		// add default value sets to populate the import parameters form 
		$id 				= 'asymm';
		$label 				= 'Mostly asymmetric particle';
		$outerMaskRadius 	= '';
		$innerMaskRadius 	= '';
		$outerAlignRadius 	= '';	 
		$innerAlignRadius 	= ''; 
		$symmetry 			= $sym; 
		$endIter 			= '25'; 
		$angSampRate 		= '10';
		$percentDiscard 	= '';  
		$filterEstimated 	= ''; 
		$filterResolution	= ''; 
		$filterComputed 	= ''; 
		$filterConstant 	= '';
		$HighResLimit			= '15';
		$DoCorrectGreyScale 	= 'checked';
		$ImagesArePhaseFlipped  = 'checked';
		$ProjMatchSampling	= '15';
		$LowPassFilter		= '50';
		$NumberOfReferences	= '3'; 

		
		$asymmSet = new XmippML3DParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $endIter, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
					  		$HighResLimit, $DoCorrectGreyScale, $ImagesArePhaseFlipped, $ProjMatchSampling,
							$LowPassFilter, $NumberOfReferences);
		$this->addDefaultParams( $asymmSet );

	}

	// TODO: when we know what the database looks like for this method, add the 
	// column names that correspond to the form parameters here. This will 
	// populate the form when parameters are imported from a prior recon.
//	protected function addImportedRefineIter( $paramSet, $iter ) 
//	{
//		$paramSet->addIterationToValue( "angSampRate", $iter['angularStep'] );
//	}	
	
	// set the default values that are populated
	// when the user selects the "Set Defaults" button.
	// $box is the box size from the selected stack.
	public function setDefaults()
	{
		$sym = $this->getSymmetry();
		
		$javafunc = "
	  <script type='text/javascript'>
	    function setDefaults(obj) {
	      if (obj.symmetry) obj.symmetry.value = '$sym';
	      if (obj.endIter) obj.endIter.value = '10';
	      if (obj.angSampRate) obj.angSampRate.value = '4x10:2x5:2x3:2x2';
		if (obj.ImagesArePhaseFlipped) obj.ImagesArePhaseFlipped.checked = '';
	      if (obj.HighResLimit) obj.HighResLimit.value = '';
	      if (obj.DoCorrectGreyScale) obj.DoCorrectGreyScale.checked = '';
		if (obj.ProjMatchSampling) obj.ProjMatchSampling.value = '';
	      if (obj.LowPassFilter) obj.LowPassFilter.value = '';
	      if (obj.NumberOfReferences) obj.NumberOfReferences.value = '';
	      
	      return;
	    }
	  </script>\n";
		return $javafunc;
	}
	
}


// extend the RefineFormParameters class to add the Xmipp 
// advanced parameter default values. 
class XmippML3DParams extends RefineFormParameters
{
	function __construct( $id='', $label='', $outerMaskRadius='', $innerMaskRadius='', $outerAlignRadius='', 
							$innerAlignRadius='', $symmetry='', $endIter='', $angSampRate='', $percentDiscard='',  
							$filterEstimated='', $filterResolution='', $filterComputed='', $filterConstant='',
							$HighResLimit='', $DoCorrectGreyScale='', $ImagesArePhaseFlipped='', $ProjMatchSampling='',
							$LowPassFilter='', $NumberOfReferences='') 
	{
		parent::__construct($id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $endIter, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant );
		
		$this->addParam( "HighResLimit", $HighResLimit, "high resolution limit" );
		$this->addParam( "ImagesArePhaseFlipped", $ImagesArePhaseFlipped, "input images are phaseflipped" );
		$this->addParam( "DoCorrectGreyScale", $DoCorrectGreyScale, "correct greyscale values" );
		$this->addParam( "ProjMatchSampling", $ProjMatchSampling, "projection matching angular sampling" );
		$this->addParam( "LowPassFilter", $LowPassFilter, "Low pass filter reference volume" );
		$this->addParam( "NumberOfReferences", $NumberOfReferences, "number of references" );
		
		// disable any general params that do not apply to this method
		$this->hideParam("outerMaskRadius");
		$this->hideParam("innerMaskRadius");
		$this->hideParam("outerAlignRadius");
		$this->hideParam("innerAlignRadius");
		$this->hideParam("percentDiscard");
		$this->hideParam("filterEstimated");
		$this->hideParam("filterResolution");
		$this->hideParam("filterComputed");
		$this->hideParam("filterConstant");

		// add parameter requirements
		$this->addValidation( "symmetry", "req" );
		$this->addValidation( "angSampRate", "req" );
		$this->addValidation( "NumberOfReferences", "req" );
	}
}

?>
