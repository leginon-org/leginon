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


class FrealignRefineForm extends BasicRefineForm 
{
	// return an instance of this refine forms parameter class which is 
	// an extension of the FormParameters class.
	public function createFormParams() { return new FrealignParams(); }
	
	// this is where a form for this recon methods specific parameters
	// is defined. 
	// outputs html. 
	public function advancedParamForm()
	{
		// classes extended from BasicRefineForm should get the selected default values
		$paramSet = $this->getFormParams();
		
		// set field sizes
		$shortSize = 4;
		$longSize = 20;
		
		
		// display form title
		$html .= "
	    <br />
	    <H4>Frealign Reconstruction Parameters</H4>
	    <hr />";
				
		// find each stack entry in database
		$reconstackid = $paramSet->getParamValue( 'reconstackid' );
		$particle = new particledata();
		$stackIds = $particle->getStackIds( $_GET['expId'] );
		if (count($stackIds) > 0) {
			$html .=  "<br />\n";
			$html .=  "<b>Select Reconstruction Stack:</b>\n";
			$html .=  "<br />\n";
			$html .=  $this->reconStackSelector($stackIds, $reconstackid);
			$html .=  "<br />\n";
		}
		
		// TODO: add javascript so that this updates when a stack is selected
		if ( $reconstackid ) {
			$html .=  stacksummarytable( $reconstackid, true);
		}		
		
		$html .=  "<br />\n";
		$html .=  "<b>Initial Orientations</b>\n";
		$html .=  "<br />\n";
		
		$html .=  $paramSet->insertRadioField( "initmethod", "importrecon", "Import from EMAN reconstruction:");
		$html .=  $this->addReconSelectBox();

		$html .=  "<br />\n";
		
		$html .=  $paramSet->insertRadioField( "initmethod", "projmatch", "Determine with Frealign" );
		$html .=  "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n";		
		$html .=  $paramSet->insertTextField( "dang", $shortSize );
		$html .=  "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n";
		$html .=  $paramSet->insertTextField( "initlp", $shortSize );
		
		$html .=  "<br />\n";
		$html .=  "<b>Card #2</b>\n";
		$html .=  "<br />\n";
	
		$html .=  $paramSet->insertTextField( "wgh", $longSize );
		$html .=  $paramSet->insertTextField( "xstd", $longSize, "(0 = no filtering)" );
		$html .=  $paramSet->insertTextField( "pbc", $longSize );
		$html .=  $paramSet->insertTextField( "boff", $longSize );
		$html .=  $paramSet->insertTextField( "itmax", $longSize );
		$html .=  $paramSet->insertTextField( "ipmax", $longSize );
				
		$html .=  "<br />\n";
		$html .=  "<b>Card #6</b>\n";
		$html .=  "<br />\n";
	
		$html .=  $paramSet->insertTextField( "target", $longSize );
		$html .=  $paramSet->insertTextField( "thresh", $longSize );
				
		$html .=  "<br />\n";
		$html .=  "<b>Card #7</b>\n";
		$html .=  "<br />\n";
	
		$html .=  $paramSet->insertTextField( "rrec", $longSize, "(in &Aring;ngstroms; default Nyquist)" );
		$html .=  $paramSet->insertTextField( "hp", $longSize, "(in &Aring;ngstroms)" );
		$html .=  $paramSet->insertTextField( "lp", $longSize, "(in &Aring;ngstroms; default 2*Nyquist)" );
		$html .=  $paramSet->insertTextField( "rbfact", $longSize, "(0 = off)" );
		
		// find if there are ctffind runs (for frealign option)
		$particle = new particledata();
		$showCTFFind = $particle->getCtfRunIds($_GET['expId'], $showHidden=False, $ctffind=True);
		
		// give option of only using ctffind runs
		if ( $showCTFFind ) {
			$html .=  "<br/>\n";
			$html .=  $paramSet->insertCheckboxField( "ctffindonly" );
			$html .=  "&nbsp;&nbsp;&nbsp;&nbsp;\n";
		}
		
		return $html;
	}
	
	function addReconSelectBox()
	{
		$particle = new particledata();

		$recons = $particle->getReconIterIdRelatedToStackid($stackid);
		$html .=  "&nbsp;&nbsp;&nbsp; Reconstruction:\n";
		if (!empty($recons)) {
			$html .=  "<select name='importrecon' onchange='prepRefine.submit()'>\n";
			$html .=  "   <option value='None'>Select Reconstruction</option>\n";
			foreach ($recons as $r) {
				$ropt = "<option value='".$r['DEF_id']."' ";
				$ropt.= ($_POST['importrecon']==$r['DEF_id']) ? 'selected':'';
				$ropt.= ">";
				$ropt.= $r['name']." (id: ".$r['DEF_id'].") -- ".substr($r['description'],0,60);
				$ropt.= "</option>\n";
				$html .=  $ropt;
			}
		} else {
			$html .=  "<i>no EMAN recons available to import Euler angles</i>\n";
		}
		$html .=  "</select>\n";
		$html .=  "<br/>\n";
		
		// if a reconstruction has been selected, show iterations & resolutions
		if ($_POST['importrecon'] && $_POST['importrecon']!='None') {
			$html .=  "&nbsp;&nbsp;&nbsp; Iteration:\n";
			$iterinfo = $particle->getRefinementData($_POST['importrecon']);
			$html .=  "<select name='importiter'>\n";
			if (is_array($iterinfo)) {
				foreach ($iterinfo as $iter){
					$iterstuff = $particle->getIterationInfo($_POST['importrecon'],$iter['iteration']);
					$rmeas = $particle->getRMeasureInfo($iter['REF|ApRMeasureData|rMeasure']);
					$fsc = $particle->getResolutionInfo($iter['REF|ApResolutionData|resolution']);
					$iopt.="<option value='".$iter['DEF_id']."' ";
					$iopt.= ($_POST['importiter']==$iter['DEF_id']) ? 'selected':'';
					$iopt.= ">Iter ".$iter['iteration'];
					$iopt.= ": Ang=".$iterstuff['ang'];
					$iopt.= ", FSC=".sprintf('%.1f',$fsc['half']);
					$iopt.= ", Rmeas=".sprintf('%.1f',$rmeas['rMeasure']);
					$iopt.= "</option>\n";
				}
			}
			$html .=  $iopt;
			$html .=  "</select>\n";
			$html .=  "<br/>\n";
		}
		
		return $html;
	}
		
	// display a selection box with any valid stacks. 
	// compares stacks to the refine stack previously selected by the user
	function reconStackSelector($stackIds, $stackidval) 
	{		
		$particle = new particledata();
		
		// get refine stack
		$refineStackId = $this->getStackId();
		$refineStackParams = $particle->getStackParams( $refineStackId );
		
		// get number of particles
		$refineTotPart = $particle->getNumStackParticles( $refineStackId );
		$refineNumPart = commafy($totalp);
		
		// get box size
		$refineBox = $refineStackParams['boxsize'];
		
		// get pixel size of stack
		$refineApix = ($particle->getStackPixelSizeFromStackId($refineStackId))*1e10;
			
		$html .=  "<SELECT NAME='reconstackid' >\n";
		$html .=  "<OPTION VALUE='' style='color:green;' >Same as refinement</option>\n";
		foreach ($stackIds as $stackid){
			// get stack parameters from database
			$s = $particle->getStackParams($stackid['stackid']);
			// get number of particles in each stack
			$totalp = $particle->getNumStackParticles($stackid['stackid']);
			$nump = commafy($totalp);
			// get pixel size of stack
			$apix = ($particle->getStackPixelSizeFromStackId($stackid['stackid']))*1e10;
			// truncated pixel size
			$showapix = sprintf("%.2f",$apix);
			// get box size
			$box = $s['boxsize'];

			// if this is not a valid stack, don't add it to the list
			if ( $nump != $refineNumPart || $apix != $refineApix || $box != $refineBox ) {
				continue;
			}

			$html .=  "<OPTION VALUE='$stackid[stackid]'";
			// select previously set stack on resubmita
			if ($stackid['stackid']==$stackidval) $html .=  " SELECTED";
			$html .= ">$s[shownstackname] ID: $stackid[stackid] ($nump particles, $showapix &Aring;/pix, ".$box."x".$box.")</OPTION>\n";
		}
		$html .=  "</SELECT>\n";
		return $html;
	}	
	

	public function buildCommand( $params )
	{
		
		$command = "prepFrealign.py ";
		if ( $params->getParamValue("reconstackid") )
			$command.= "--reconstackid=".$params->getParamValue("reconstackid")." ";
		if ( $params->getParamValue("importiter") ) 
			$command.= "--reconiterid=".$params->getParamValue("importiter")." ";
		if ( ($params->getParamValue('initmethod') == 'projmatch') && $params->getParamValue("dang") ) 
			$command.= "--dang=".$params->getParamValue("dang")." ";
			    
		$command.= "--mask=".$params->getParamValue("outerMaskRadius")." ";
		$command.= "--imask=".$params->getParamValue("innerMaskRadius")." ";
		$command.= "--wgh=".$params->getParamValue("wgh")." ";
		$command.= "--xstd=".$params->getParamValue("xstd")." ";
		$command.= "--pbc=".$params->getParamValue("pbc")." ";
		$command.= "--boff=".$params->getParamValue("boff")." ";;
		$command.= "--itmax=".$params->getParamValue("itmax")." ";
		$command.= "--ipmax=".$params->getParamValue("ipmax")." ";
		$command.= "--sym=".$params->getParamValue("symmetry")." ";
		$command.= "--target=".$params->getParamValue("target")." ";
		$command.= "--thresh=".$params->getParamValue("thresh")." ";
		$command.= "--rrec=".$params->getParamValue("rrec")." ";
		$command.= "--hp=".$params->getParamValue("hp")." ";
		$command.= "--lp=".$params->getParamValue("lp")." ";
		$command.= "--rbfact=".$params->getParamValue("rbfact")." ";
		$command.= "--numiter=".$params->getParamValue("numIters")." ";

		$ctffindonly = $params->getParamValue("ctffindonly");
		if (!empty($ctffindonly)) $command.= "--ctfmethod=ctffind ";
		if ($last) $command.= "--last=$last ";
		
		return $command;
	}
	
	protected function setImportParams()
	{
		// add default value sets to populate the import parameters form 
		$id 				= 'asymm';
		$label 				= 'asymmetric particles';
		$outerMaskRadius 	= ''; //round($apix*$box/3.0)
		$innerMaskRadius 	= '0';
		$outerAlignRadius 	= '';	 
		$innerAlignRadius 	= ''; 
		$symmetry 			= 'c1'; 
		$numIters 			= '10'; 
		$angSampRate 		= '';
		$percentDiscard 	= '';  
		$filterEstimated 	= ''; 
		$filterResolution	= ''; 
		$filterComputed 	= ''; 
		$filterConstant 	= '';
		$wgh 				= '0.07';
		$xstd 				= '0';
		$pbc  				= '100';
		$boff  				= '70';
		$itmax 				= '10';
		$ipmax				= '0';
		$target				= '15';
		$thresh				= '85';
		$rrec 				= ''; //(ceil($apix*20))/10
		$hp 				= '50';
		$lp 				= ''; //(ceil($apix*40))/10
		$rbfact 			= '0';
		$ctffindonly  		= 'CHECKED';
		$reconstackid		= '';
		$initmethod			= '';
		$importrecon		= '';
		$dang				= '5';
		$initlp				= '25';
		$importiter			= '';
		
		$asymmSet = new FrealignParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$wgh, $xstd, $pbc, $boff, $itmax, $ipmax, $target,
							$thresh, $rrec, $hp, $lp, $rbfact, $ctffindonly, $reconstackid,
							$initmethod, $importrecon, $dang, $initlp, $importiter );
		$this->addDefaultParams( $asymmSet );
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
	      if (obj.outerMaskRadius) obj.outerMaskRadius.value = $rad;
	      if (obj.innerMaskRadius) obj.innerMaskRadius.value = $rad;
	      if (obj.symmetry) obj.symmetry.value = 'c1';
	      if (obj.numIters) obj.numIters.value = '10';
	      if (obj.wgh) obj.wgh.value = '';
	      if (obj.xstd) obj.xstd.value = '';
	      if (obj.pbc) obj.pbc.value = '';
	      if (obj.boff) obj.boff.value = '';
	      if (obj.itmax) obj.itmax.value = '';
	      if (obj.ipmax) obj.ipmax.value = '';
	      if (obj.target) obj.target.value = '';
	      if (obj.thresh) obj.thresh.value = '';
	      if (obj.rrec) obj.rrec.value = '';
	      if (obj.hp) obj.hp.value = '';
	      if (obj.lp) obj.lp.value = '';
	      if (obj.rbfact) obj.rbfact.value = '';
	      if (obj.ctffindonly) obj.ctffindonly.checked = '';
	      if (obj.reconstackval) obj.reconstackval.value = '';
	      if (obj.initmethod) obj.initmethod.value = '';
	      if (obj.importrecon) obj.importrecon.value = '';
	      if (obj.dang) obj.dang.value = '';
	      if (obj.initlp) obj.initlp.value = '';
	      if (obj.importiter) obj.importiter.value = '';
	      
	      return;
	    }
	  </script>\n";
		return $javafunc;
	}
		
}

// extend the RefineFormParameters class to add the xmipp 
// advanced parameter default values. 
class FrealignParams extends RefineFormParameters
{
	function __construct( $id='', $label='', $outerMaskRadius='', $innerMaskRadius='', $outerAlignRadius='', 
							$innerAlignRadius='', $symmetry='', $numIters='', $angSampRate='', $percentDiscard='',  
							$filterEstimated='', $filterResolution='', $filterComputed='', $filterConstant='',
							$wgh='', $xstd='', $pbc='', $boff='', $itmax='', $ipmax='', $target='', 
							$thresh='', $rrec='', $hp='', $lp='', $rbfact='', $ctffindonly='', $reconstackid='', 
							$initmethod='', $importrecon='', $dang='', $initlp='', $importiter='' ) 
	{
		parent::__construct($id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant );
		
		$this->addParam( "wgh", $wgh, "Amplitude contrast (WGH)" );
		$this->addParam( "xstd", $xstd, "Standard deviation filtering (XSTD)" );
		$this->addParam( "pbc", $pbc, "Phase B-factor weighting constant (PBC)" );
		$this->addParam( "boff", $boff, "B-factor offset (BOFF)" );
		$this->addParam( "itmax", $itmax, "Number of randomized search trials (ITMAX)" );
		$this->addParam( "ipmax", $ipmax, "Number of potential matches to refine (IPMAX)" );
		$this->addParam( "target", $target, "Target phase residual (TARGET)" );
		$this->addParam( "thresh", $thresh, "Worst phase residual for inclusion (THRESH)" );
		$this->addParam( "rrec", $rrec, "Resolution limit of reconstruction (RREC)" );
		$this->addParam( "hp", $hp, "Lower resolution limit or high-pass filter (RMAX1)" );
		$this->addParam( "lp", $lp, "Higher resolution limit or low-pass filter (RMAX2)" );
		$this->addParam( "rbfact", $rbfact, "B-factor correction (RBFACT)" );
		$this->addParam( "ctffindonly", $ctffindonly, "Only use CTFFIND values" );
		$this->addParam( "reconstackval", $reconstackid, "Reconstruction Stack" );
		$this->addParam( "initmethod", $initmethod, "Initial orientation method");
		$this->addParam( "importrecon", $importrecon, "Import from EMAN Reconstruction" );
		$this->addParam( "dang", $dang, "Angular increment" );
		$this->addParam( "initlp", $initlp, "Initial LP filter" );
		$this->addParam( "importiter", $importiter, "Recon import iteration number" );
		
		// disable any general params that do not apply to this method
		$this->hideParam("outerAlignRadius");
		$this->hideParam("innerAlignRadius");
		$this->hideParam("angSampRate");
		$this->hideParam("percentDiscard");
		$this->hideParam("filterEstimated");
		$this->hideParam("filterResolution");
		$this->hideParam("filterComputed");
		$this->hideParam("filterConstant");
		
		// add parameter requirements
		$this->addValidation( "outerMaskRadius", "req" );	
	}
	
	// add custom validations
	function validate() 
	{
		$msg = parent::validate();

		if ( ($this->params["initmethod"]["value"] == 'projmatch') && empty($this->params["dang"]["value"]) ) {
			$msg .= "<b>Error:</b> Enter an angular increment";
		}
		
		return $msg;
	}
	
}

?>
