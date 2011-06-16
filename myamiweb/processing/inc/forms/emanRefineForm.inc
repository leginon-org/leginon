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


class EmanRefineForm extends BasicRefineForm 
{
	public function createFormParams() { return new EmanParams(); }
	
	public function advancedParamForm()
	{
		// classes extended from BasicRefineForm should get the selected default values
		$params = $this->getFormParams();
		
		// display form title
		$html .="
	    <br />
	    <H4>EMAN Reconstruction Parameters</H4>
	    <hr />";

		$shortSize = 4;
		$longSize = 20;
		$html .= $params->insertTextField( "imask", $longSize );
		$html .= $params->insertTextField( "amask", $longSize );
		$html .= $params->insertTextField( "maxshift", $longSize );
		$html .= $params->insertTextField( "hard", $longSize );
		$html .= $params->insertTextField( "clskeep", $longSize );
		$html .= $params->insertTextField( "clsiter", $longSize );
		$html .= $params->insertTextField( "xfiles", $longSize );
		$html .= $params->insertTextField( "shrink", $longSize );
		$html .= $params->insertTextField( "euler2", $longSize );
		$html .= $params->insertTextField( "median", $longSize );
		$html .= $params->insertTextField( "phscls", $longSize );
		$html .= $params->insertTextField( "refine", $longSize );
		$html .= $params->insertTextField( "tree", $longSize );
		
		$html .= "<br />\n";
		$html .= "<b>Coran parameters</b>\n";
		$html .= "<br />\n";
		
		$html .= $params->insertTextField( "coranCC", $longSize );
		$html .= $params->insertTextField( "coranmask", $longSize );
		$html .= $params->insertTextField( "coranlp", $longSize );
		$html .= $params->insertTextField( "coranhp", $longSize );
		$html .= $params->insertTextField( "coranhcc", $longSize );
								
		$html .= "<br/>\n";		
		
		return $html;
	}
	
	public function buildCommand( $paramSet )
	{		
		$command = 'prepEman.py ';
		$command.= '--ang='.$paramSet->getParamValue("angSampRate").' ';
		$command.= '--mask='.$paramSet->getParamValue("outerMaskRadius").' ';
		$command.= '--sym='.$paramSet->getParamValue("symmetry").' ';
		$command.= '--imask='.$paramSet->getParamValue("imask").' ';
		$command.= '--amask='.$paramSet->getParamValue("amask").' ';		
		$command.= '--maxshift='.$paramSet->getParamValue("maxshift").' ';
		$command.= '--hard='.$paramSet->getParamValue("hard").' ';
		$command.= '--clskeep='.$paramSet->getParamValue("clskeep").' ';
		$command.= '--clsiter='.$paramSet->getParamValue("clsiter").' ';
		$command.= '--xfiles='.$paramSet->getParamValue("xfiles").' ';
		$command.= '--shrink='.$paramSet->getParamValue("shrink").' ';
		$command.= '--euler2='.$paramSet->getParamValue("euler2").' ';
		$command.= '--median='.$paramSet->getParamValue("median").' ';
		$command.= '--phscls='.$paramSet->getParamValue("phscls").' ';
		$command.= '--refine='.$paramSet->getParamValue("refine").' ';
		$command.= '--tree='.$paramSet->getParamValue("tree").' ';
		$command.= '--coranCC='.$paramSet->getParamValue("coranCC").' ';
		$command.= '--coranmask='.$paramSet->getParamValue("coranmask").' ';
		$command.= '--coranlp='.$paramSet->getParamValue("coranlp").' ';
		$command.= '--coranhp='.$paramSet->getParamValue("coranhp").' ';
		$command.= '--coranhcc='.$paramSet->getParamValue("coranhcc").' ';	
		
		if ($paramSet->getParamValue("filterEstimated") == 'on')
			$command.= '--filt3d='.$paramSet->getParamValue("filterResolution").' ';
		
		return $command;
	}
	
	protected function setImportParams()
	{
		// add default value sets to populate the import parameters form 
		$id 				= 'asymm';
		$label 				= 'Mostly asymmetric particle';
		$outerMaskRadius 	= '126';
		$innerMaskRadius 	= '';
		$outerAlignRadius 	= '';	 
		$innerAlignRadius 	= ''; 
		$symmetry 			= 'd7'; 
		$numIters 			= '9'; 
		$angSampRate 		= '3x10:3x8:3x6';
		$percentDiscard 	= '';  
		$filterEstimated 	= ''; 
		$filterResolution	= ''; 
		$filterComputed 	= ''; 
		$filterConstant 	= '';
		$imask				= ''; 
		$amask				= '';
		$maxshift			= '';
		$hard				= '25';
		$clskeep			= '0.8';
		$clsiter			= '2x8:1x3:2x8:1x3:2x8:1x3'; 
		$xfiles				= '';
		$shrink				= '';
		$euler2				= '';
		$median				= '';
		$phscls				= '9x1';
		$refine				= '6x0:3x1';
		$tree				= '';
		$coranCC			= '';
		$coranmask			= '';
		$coranlp			= '';
		$coranhp			= '';
		$coranhcc			= '';
		
		$asymmSet = new EmanParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$imask, $amask, $maxshift, $hard, $clskeep,
							$clsiter, $xfiles, $shrink, $euler2, $median, $phscls, $refine, 
							$tree, $coranCC, $coranmask, $coranlp, $coranhp, $coranhcc );
		$this->addDefaultParams( $asymmSet );

		$id 				= 'groel1';
		$label 				= 'GroEL with 10,000+ particles';
		$numIters 			= '20'; 
		$angSampRate 		= '4x5:4x4:4x3:4x2:4x1';
		$clsiter			= '2x8:2x3:2x8:2x3:2x8:2x3:2x8:2x3:2x8:2x3'; 
		$refine				= '16x0:4x1';
		$groelSet = new EmanParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$imask, $amask, $maxshift, $hard, $clskeep,
							$clsiter, $xfiles, $shrink, $euler2, $median, $phscls, $refine, 
							$tree, $coranCC, $coranmask, $coranlp, $coranhp, $coranhcc );
		$this->addDefaultParams( $groelSet );
		
		$id 				= 'virusgood';
		$label 				= 'Icos Virus with good starting model';
		$numIters 			= '14'; 
		$angSampRate 		= '4x3:4x2:3x1:3x0.8';
		$clsiter			= '2x8:2x3:2x8:8x3'; 
		$refine				= '11x0:3x1';
		$virusSet = new EmanParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$imask, $amask, $maxshift, $hard, $clskeep,
							$clsiter, $xfiles, $shrink, $euler2, $median, $phscls, $refine, 
							$tree, $coranCC, $coranmask, $coranlp, $coranhp, $coranhcc );
		$this->addDefaultParams( $virusSet );
	}
	
	// The user selected to import parameters from an existing refinement.
	// This will gather the parameter values and put them into our param 
	// format ('iterations'x'value':)
	// Returns a set of Form Parameters.
	protected function importParamsFromRefinement( $defaultSetId )
	{
		$paramSet = $this->createFormParams();
		$particle = new particledata();
		$iterinfo = $particle->getIterationInfo( $defaultSetId );
		
		// get initial model info
		$refinfo 	= $particle->getRefinementRunInfo( $defaultSetId );
		$initmodel 	= $particle->getInitModelInfo($refinfo['REF|ApInitialModelData|initialModel']);
		$stackinfo 	= $particle->getStackParams($refinfo['REF|ApStackData|stack']);
		
		// get scaling factor for box sizes
		$prevboxsize	= $stackinfo['boxsize'];
		// TODO: get $box from our stack id
		$boxscale 		= $box / $prevboxsize;
		$numIters 		= count($iterinfo);
		
		$paramSet->setParamValue( "numIters", $numIters );
				
		for ( $i=1; $i<=$numIters; $i++ ) {
			foreach ($iterinfo as $iter) {
				if ($iter['iteration'] == $i) {
					//var_dump($iter);
					$paramSet->addIterationToValue( "angSampRate", $iter['ang'] );
					$outerMaskRadius = ceil($iter['mask']*$boxscale);
					if (floor($iter['imask']*$boxscale) > 0)
						$paramSet->addIterationToValue( "imask", floor($iter['imask']*$boxscale) );
					$paramSet->addIterationToValue( "amask1", $iter['EMAN_amask1'] );
					$paramSet->addIterationToValue( "amask2", $iter['EMAN_amask2'] );
					$paramSet->addIterationToValue( "amask3", $iter['EMAN_amask3'] );
					$paramSet->addIterationToValue( "maxhsift", $iter['EMAN_maxshift'] );
					$paramSet->addIterationToValue( "hard", $iter['EMAN_hard'] );
					$paramSet->addIterationToValue( "clsiter", $iter['EMAN_classiter'] );
					$paramSet->addIterationToValue( "clskeep", $iter['EMAN_classkeep'] );
					$paramSet->addIterationToValue( "filterResolution", $iter['EMAN_filt3d'] );
					$paramSet->addIterationToValue( "shrink", $iter['EMAN_shrink'] );
					$paramSet->addIterationToValue( "euler2", $iter['EMAN_euler2'] );
					$paramSet->addIterationToValue( "xfiles", $iter['EMAN_xfiles'] );
					$paramSet->addIterationToValue( "median", ($iter['EMAN_median']) ? '1' : '0' );
					$paramSet->addIterationToValue( "phscls", ($iter['EMAN_phasecls']) ? '1' : '0' );
					$paramSet->addIterationToValue( "refine", ($iter['EMAN_refine']) ? '1' : '0' );
					$paramSet->addIterationToValue( "coran", ($iter['postRefineClassAverages']) ? '1' : '0' );
					$symmetry = $particle->getSymInfo($iter['REF|ApSymmetryData|symmetry']);
					if (!is_array($symmetry)) $symmetry=$modsym;
					else $symmetry = $symmetry['eman_name'];
					continue;
				}
			}
		}
		
		return $paramSet;
	}
	
	// set the default values that are populated
	// when the user selects the "Set Defaults" button.
	// $box is the box size from the selected stack.
	public function setDefaults( $box )
	{
		$rad = ($box/2)-2;
		$javafunc = "
	  <script type='text/javascript'>
	    function setDefaults(obj) {
	      obj.outerMaskRadius.value = $rad;
	      obj.innerMaskRadius.value = $rad;
	      obj.angSampRate.value = '4x10:2x5:2x3:2x2';
	      obj.symmetry.value = 'c1';
	      obj.numIters.value = '10';
	      obj.percentDiscard.value = '10';
	      obj.filterEstimated.checked = false;
	      obj.filterResolution.value = '';
	      obj.imask.value = '';
	      obj.amask.value = '';		
	      obj.maxshift.value = '';
	      obj.hard.value = '25';
	      obj.clskeep.value = '0.8';
	      obj.clsiter.value = '8';
	      obj.xfiles.value = '';
	      obj.shrink.value = '';
	      obj.euler2.value = '';
	      obj.median.value = '';
	      obj.phscls.value = '10x1';
	      obj.refine.value = '';
	      obj.tree.value = '';
	      obj.coranCC.value = '';
	      obj.coranmask.value = '';
	      obj.coranlp.value = '';
	      obj.coranhp.value = '';
	      obj.coranhcc.value = '';	      
	      return;
	    }
	  </SCRIPT>\n";
		return $javafunc;
	}
	
}


// extend the RefineFormParameters class to add the EMAN 
// advanced parameter default values. 
class EmanParams extends RefineFormParameters
{
	function __construct( $id='', $label='', $outerMaskRadius='', $innerMaskRadius='', $outerAlignRadius='', 
							$innerAlignRadius='', $symmetry='', $numIters='', $angSampRate='', $percentDiscard='',  
							$filterEstimated='', $filterResolution='', $filterComputed='', $filterConstant='',
							$imask='', $amask='', $maxshift='', $hard='', $clskeep='',
							$clsiter='', $xfiles='', $shrink='', $euler2='', $median='', $phscls='', $refine='', 
							$tree='', $coranCC='', $coranmask='', $coranlp='', $coranhp='', $coranhcc='' ) 
	{
		parent::__construct($id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant );
		
		$this->addParam( "imask", $imask, "imask" );
		$this->addParam( "amask", $amask, "amask" );		
		$this->addParam( "maxshift", $maxshift, "maxshift " );
		$this->addParam( "hard", $hard, "hard" );
		$this->addParam( "clskeep", $clskeep, "clskeep" );
		$this->addParam( "clsiter", $clsiter, "clsiter" );
		$this->addParam( "xfiles", $xfiles, "xfiles" );
		$this->addParam( "shrink", $shrink, "shrink" );
		$this->addParam( "euler2", $euler2, "euler2" );
		$this->addParam( "median", $median , "median " );
		$this->addParam( "phscls", $phscls, "phscls" );
		$this->addParam( "refine", $refine, "refine" );
		$this->addParam( "tree", $tree, "tree" );
		$this->addParam( "coranCC", $coranCC, "CC cut" );
		$this->addParam( "coranmask", $coranmask, "Mask" );
		$this->addParam( "coranlp", $coranlp, "LP" );
		$this->addParam( "coranhp", $coranhp, "HP" );
		$this->addParam( "coranhcc", $coranhcc, "HaCC" );
		
		// hide any general params that do not apply to this method
		$this->hideParam("outerAlignRadius");
		$this->hideParam("innerAlignRadius");
		$this->hideParam("filterComputed");
		$this->hideParam("filterConstant");
		
		// add parameter requirements
		$this->addValidation( "outerMaskRadius", "req" );
		$this->addValidation( "symmetry", "req" );
		$this->addValidation( "angSampRate", "req" );
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
