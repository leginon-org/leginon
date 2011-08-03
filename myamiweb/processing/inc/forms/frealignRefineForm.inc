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
	
	// This is where a form for this recon methods specific parameters is defined. 
	// Outputs html. 
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
		$stackIds = $this->particle->getStackIds( $_GET['expId'] );
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
		$showCTFFind = $this->particle->getCtfRunIds($_GET['expId'], $showHidden=False, $ctffind=True);
		
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
		$recons = $this->particle->getReconIterIdRelatedToStackid($stackid);
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
			$iterinfo = $this->particle->getRefinementData($_POST['importrecon']);
			$html .=  "<select name='importiter'>\n";
			if (is_array($iterinfo)) {
				foreach ($iterinfo as $iter){
					$iterstuff = $this->particle->getIterationInfo($_POST['importrecon'],$iter['iteration']);
					$rmeas = $this->particle->getRMeasureInfo($iter['REF|ApRMeasureData|rMeasure']);
					$fsc = $this->particle->getResolutionInfo($iter['REF|ApResolutionData|resolution']);
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
		$refineStack = $this->getStackInfo();
		
		$html .=  "<SELECT NAME='reconstackid' >\n";
		$html .=  "<OPTION VALUE='' style='color:green;' >Same as refinement</option>\n";
		foreach ($stackIds as $stackid){
			// get stack parameters from database
			$s = $this->particle->getStackParams($stackid['stackid']);
			// get number of particles in each stack
			$totalp = $this->particle->getNumStackParticles($stackid['stackid']);
			$nump = commafy($totalp);
			// get pixel size of stack
			$apix = ($this->particle->getStackPixelSizeFromStackId($stackid['stackid']))*1e10;
			// truncated pixel size
			$showapix = sprintf("%.2f",$apix);
			// get box size
			$box = $s['boxsize'];

			// if this is not a valid stack, don't add it to the list
			if ( $nump != $refineStack['lastPart'] || $apix != $refineStack['apix'] || $box != $refineStack['boxsize'] ) {
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
	

	public function buildCommand( $postArray )
	{
		$params = $this->getFormParams();
		$params->getPostedValues( $postArray );
		
		$command = '';
		$command = $this->addCommandFlag( $command, "outerMaskRadius" );
		$command = $this->addCommandFlag( $command, "innerMaskRadius" );
		$command = $this->addCommandFlag( $command, "endIter" );
		$command = $this->addCommandFlag( $command, "symmetry" );
		$command = $this->addCommandFlag( $command, "reconstackid" );
		$command = $this->addCommandFlag( $command, "wgh" );
		$command = $this->addCommandFlag( $command, "xstd");
		$command = $this->addCommandFlag( $command, "pbc" );
		$command = $this->addCommandFlag( $command, "boff" );
		$command = $this->addCommandFlag( $command, "itmax" );
		$command = $this->addCommandFlag( $command, "ipmax" );
		$command = $this->addCommandFlag( $command, "target" );
		$command = $this->addCommandFlag( $command, "thresh" );
		$command = $this->addCommandFlag( $command, "rrec" );
		$command = $this->addCommandFlag( $command, "hp" );
		$command = $this->addCommandFlag( $command, "lp" );
		$command = $this->addCommandFlag( $command, "rbfact" );
		$command = $this->addCommandFlag( $command, "importiter" );
		
		// check which radio button was selected
		if ( ($params->getParamValue('initmethod') == 'projmatch') ) {
			$command = $this->addCommandFlag( $command, "dang" );
			$command = $this->addCommandFlag( $command, "initlp" );
		} 
		
		// see if checkbox was selected
		$ctffindonly = $params->getParamValue("ctffindonly");
		if ( $ctffindonly == 'on' ) $command.= "--ctfmethod=ctffind ";
		
		return $command;
	}
	
	protected function setImportParams()
	{
		$stackInfo 	= $this->getStackInfo();
		$box 		= $stackInfo['boxsize'];
		$apix 		= $stackInfo['apix'];
		$sym 		= $this->getSymmetry();
		
		// add default value sets to populate the import parameters form 
		$id 				= 'asymm';
		$label 				= 'asymmetric particles';
		$outerMaskRadius 	= round($apix*$box/3.0);
		$innerMaskRadius 	= '0';
		$outerAlignRadius 	= '';	 
		$innerAlignRadius 	= ''; 
		$symmetry 			= $sym; 
		$endIter 			= '10'; 
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
		$rrec 				= (ceil($apix*20))/10;
		$hp 				= '50';
		$lp 				= (ceil($apix*40))/10;
		$rbfact 			= '0';
		$ctffindonly  		= 'CHECKED';
		$reconstackid		= '';
		$initmethod			= '';
		$importrecon		= '';
		$dang				= '5';
		$initlp				= '25';
		$importiter			= '';
		
		$asymmSet = new FrealignParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $endIter, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$wgh, $xstd, $pbc, $boff, $itmax, $ipmax, $target,
							$thresh, $rrec, $hp, $lp, $rbfact, $ctffindonly, $reconstackid,
							$initmethod, $importrecon, $dang, $initlp, $importiter );
		$this->addDefaultParams( $asymmSet );
	}
		
	protected function addImportedRefineIter( $paramSet, $iter ) 
	{
		$paramSet->addIterationToValue( "wgh", $iter['wgh'] );
		$paramSet->addIterationToValue( "xstd", $iter['xstd'] );
		$paramSet->addIterationToValue( "pbc", $iter['pbc'] );
		$paramSet->addIterationToValue( "boff", $iter['boff'] );
		$paramSet->addIterationToValue( "itmax", $iter['itmax'] );
		$paramSet->addIterationToValue( "ipmax", $iter['ipmax'] );
		$paramSet->addIterationToValue( "target", $iter['target'] );
		$paramSet->addIterationToValue( "thresh", $iter['thresh'] );
		$paramSet->addIterationToValue( "cs", $iter['cs'] );
		$paramSet->addIterationToValue( "rrec", $iter['rrec'] );
		$paramSet->addIterationToValue( "hp", $iter['highpass'] );
		$paramSet->addIterationToValue( "lp", $iter['lowpass'] );
		$paramSet->addIterationToValue( "rbfact", $iter['rbfact'] );		
	}	
	
	// set the default values that are populated
	// when the user selects the "Set Defaults" button.
	// $box is the box size from the selected stack.
	public function setDefaults()
	{
		// get the stack info for the stack selected by the user
		$stack 	= $this->getStackInfo();
		$box 	= $stack['boxsize'];
		$apix 	= $stack['apix'];
		$sym = $this->getSymmetry();
		
		// calculate default parameters
		$outerMaskRadius 	= round($apix * $box / 3.0);
		$rrec 				= (ceil($apix * 20)) / 10;
		$lp 				= (ceil($apix * 40)) / 10;
		
		$javafunc = "
	  <script type='text/javascript'>
	    function setDefaults(obj) {
	      if (obj.outerMaskRadius) obj.outerMaskRadius.value = $outerMaskRadius;
	      if (obj.innerMaskRadius) obj.innerMaskRadius.value = 0;
	      if (obj.symmetry) obj.symmetry.value = $sym;
	      if (obj.endIter) obj.endIter.value = '10';
	      if (obj.wgh) obj.wgh.value = '0.07';
	      if (obj.xstd) obj.xstd.value = '0';
	      if (obj.pbc) obj.pbc.value = '100';
	      if (obj.boff) obj.boff.value = '70';
	      if (obj.itmax) obj.itmax.value = '10';
	      if (obj.ipmax) obj.ipmax.value = '0';
	      if (obj.target) obj.target.value = '15';
	      if (obj.thresh) obj.thresh.value = '85';
	      if (obj.rrec) obj.rrec.value = $rrec;
	      if (obj.hp) obj.hp.value = '50';
	      if (obj.lp) obj.lp.value = $lp;
	      if (obj.rbfact) obj.rbfact.value = '0';
	      if (obj.ctffindonly) obj.ctffindonly.checked = '';
	      if (obj.reconstackval) obj.reconstackid.value = '';
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
							$innerAlignRadius='', $symmetry='', $endIter='', $angSampRate='', $percentDiscard='',  
							$filterEstimated='', $filterResolution='', $filterComputed='', $filterConstant='',
							$wgh='', $xstd='', $pbc='', $boff='', $itmax='', $ipmax='', $target='', 
							$thresh='', $rrec='', $hp='', $lp='', $rbfact='', $ctffindonly='', $reconstackid='', 
							$initmethod='', $importrecon='', $dang='', $initlp='', $importiter='' ) 
	{
		parent::__construct($id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $endIter, $angSampRate, $percentDiscard,  
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
		$this->addParam( "reconstackid", $reconstackid, "Reconstruction Stack" );
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
