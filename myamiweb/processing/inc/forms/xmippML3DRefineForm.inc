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
	public function getMethodType() { return "xmippml3d"; }
	public function createFormParams() { return new XmippML3DParams(); }
	
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
		echo $params->insertCheckboxField( "DoMlf", $longSize );
		echo $params->insertTextField( "HighResLimit", $longSize );
		echo $params->insertCheckboxField( "DoCorrectGreyScale", $longSize );
		echo $params->insertTextField( "ProjMatchSampling", $longSize );
		echo $params->insertTextField( "LowPassFilterReference", $longSize );
		echo $params->insertTextField( "NumberOfReferences", $longSize );
								
		echo "<br/>\n";		
	}
	
	public function buildCommand( $params )
	{		
		$command = 'prepXmippML3D.py ';
		$command.= '--AngularSampling='.$params["angSampRate"]["value"].' ';
		$command.= '--symid='.$params["symmetry"]["value"].' ';
		$command.= '--DoMlf='.$params["DoMlf"]["value"].' ';
		$command.= '--HighResLimit='.$params["HighResLimit"]["value"].' ';
		$command.= '--DoCorrectGreyScale='.$params["DoCorrectGreyScale"]["value"].' ';
		$command.= '--ProjMatchSampling='.$params["ProjMatchSampling"]["value"].' ';
		$command.= '--LowPassFilterReference='.$params["LowPassFilterReference"]["value"].' ';
		$command.= '--NumberOfReferences='.$params["NumberOfReferences"]["value"].' ';
		
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
		$this->disableParam("outerMaskRadius");
		$this->disableParam("innerMaskRadius");
		$this->disableParam("outerAlignRadius");
		$this->disableParam("innerAlignRadius");
		$this->disableParam("percentDiscard");
		$this->disableParam("filterEstimated");
		$this->disableParam("filterResolution");
		$this->disableParam("filterComputed");
		$this->disableParam("filterConstant");

		// add parameter requirements
		$this->addValidation( "symmetry", "req" );
		$this->addValidation( "angSampRate", "req" );
		$this->addValidation( "NumberOfReferences", "req" );
	}
	
	function validate() 
	{
		$msg = parent::validate();
		
		
		// TODO: if amask is used, then xfiles must also be used
//		if ($_POST['amask1'.$i] || $_POST['amask2'.$i] || $_POST['amask3'.$i]) {
//			if (!($_POST['amask1'.$i] && $_POST['amask2'.$i] && $_POST['amask3'.$i]))
//				jobForm("ERROR: All 3 amask values of amask must be entered for iteration $i");
//			if (!$_POST['xfiles'.$i])
//				jobForm("ERROR: amask requires the use of xfiles for iteration $i");
//		}
		
		
		return $msg;
	}
}

?>
