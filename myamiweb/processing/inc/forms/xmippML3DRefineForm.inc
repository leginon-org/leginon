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


class XmippML3DRefineForm extends BasicRefineForm 
{
	public function createFormParams() { return new XmippML3DParams(); }
	
	public function advancedParamForm()
	{
		// classes extended from BasicRefineForm should get the selected default values
		$params = $this->getFormParams();
		
		$shortSize = 4;
		$longSize = 20;
		$html .= $params->insertTextField( "HighResLimit", $longSize );
		$html .= $params->insertTextField( "ProjMatchSampling", $longSize );
		$html .= $params->insertTextField( "LowPassFilterReference", $longSize );
		$html .= $params->insertTextField( "NumberOfReferences", $longSize );
		$html .= $params->insertCheckboxField( "DoMlf" );
		$html .= $params->insertCheckboxField( "DoCorrectGreyScale" );
				
		return $html;
	}
	
	public function buildCommand( $postArray )
	{	
		// make sure this forms params have been updated with the post array	
		$params = $this->getFormParams();
		$params->getPostedValues( $postArray );
		
		$command = '';
		$command = $this->addCommandFlag( $command, "jobtype", "", "xmippml3drecon" );
		$command = $this->addCommandFlag( $command, "angSampRate" );
		$command = $this->addCommandFlag( $command, "symmetry" );
		$command = $this->addCommandFlag( $command, "DoMlf" );
		$command = $this->addCommandFlag( $command, "HighResLimit" );
		$command = $this->addCommandFlag( $command, "DoCorrectGreyScale" );
		$command = $this->addCommandFlag( $command, "ProjMatchSampling" );
		$command = $this->addCommandFlag( $command, "LowPassFilterReference" );
		$command = $this->addCommandFlag( $command, "NumberOfReferences" );
		
		return $command;
	}
	
	protected function setImportParams()
	{
		// add default value sets to populate the import parameters form 
		$id 				= 'asymm';
		$label 				= 'Mostly asymmetric particle';
		$outerMaskRadius 	= '';
		$innerMaskRadius 	= '';
		$outerAlignRadius 	= '';	 
		$innerAlignRadius 	= ''; 
		$symmetry 			= 'c1'; 
		$numIters 			= '25'; 
		$angSampRate 		= '10';
		$percentDiscard 	= '';  
		$filterEstimated 	= ''; 
		$filterResolution	= ''; 
		$filterComputed 	= ''; 
		$filterConstant 	= '';
		$DoMlf 					= 'checked';
		$HighResLimit			= '15';
		$DoCorrectGreyScale 	= 'checked';
		$ProjMatchSampling	= '15';
		$LowPassFilterReference		= '50';
		$NumberOfReferences	= '3'; 

		
		$asymmSet = new XmippML3DParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$DoMlf, $HighResLimit, $DoCorrectGreyScale, $ProjMatchSampling,
							$LowPassFilterReference, $NumberOfReferences);
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
		$javafunc = "
	  <script type='text/javascript'>
	    function setDefaults(obj) {
	      if (obj.symmetry) obj.symmetry.value = 'c1';
	      if (obj.numIters) obj.numIters.value = '10';
	      if (obj.angSampRate) obj.angSampRate.value = '4x10:2x5:2x3:2x2';
	      if (obj.DoMlf) obj.DoMlf.checked = '';
	      if (obj.HighResLimit) obj.HighResLimit.value = '';
	      if (obj.DoCorrectGreyScale) obj.DoCorrectGreyScale.checked = '';
		  if (obj.ProjMatchSampling) obj.ProjMatchSampling.value = '';
	      if (obj.LowPassFilterReference) obj.LowPassFilterReference.value = '';
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
							$innerAlignRadius='', $symmetry='', $numIters='', $angSampRate='', $percentDiscard='',  
							$filterEstimated='', $filterResolution='', $filterComputed='', $filterConstant='',
							$DoMlf='', $HighResLimit='', $DoCorrectGreyScale='', $ProjMatchSampling='',
							$LowPassFilterReference='', $NumberOfReferences='') 
	{
		parent::__construct($id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant );
		
		$this->addParam( "DoMlf", $DoMlf, "DoMlf" );
		$this->addParam( "HighResLimit", $HighResLimit, "high resolution limit" );
		$this->addParam( "DoCorrectGreyScale", $DoCorrectGreyScale, "correct greyscale values" );
		$this->addParam( "ProjMatchSampling", $ProjMatchSampling, "projection matching angular sampling" );
		$this->addParam( "LowPassFilterReference", $LowPassFilterReference, "Low pass filter reference volume" );
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
