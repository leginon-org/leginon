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
	public function getMethodType() { return "frealign"; }
	public function createFormParams() { return new FrealignParams(); }
	
	public function advancedParamForm()
	{
		// classes extended from BasicRefineForm should get the selected default values
		$params = $this->getFormParams();
		
		// display form title
		echo"
	    <br />
	    <H4>Frealign Reconstruction Parameters</H4>
	    <hr />";
		
		$this->initialOrientForm();
		
		echo "<b>Card #2</b>\n";
		echo "<br />\n";
	
		$shortSize = 4;
		$longSize = 20;
		
		echo $this->insertTextField( $params["wgh"]["name"], $params["wgh"]["label"], $params["wgh"]["value"], $longSize, $params["wgh"]["enable"] );
		echo $this->insertTextField( $params["xstd"]["name"], $params["xstd"]["label"], $params["xstd"]["value"], $longSize, $params["xstd"]["enable"], "(0 = no filtering)" );
		echo $this->insertTextField( $params["pbc"]["name"], $params["pbc"]["label"], $params["pbc"]["value"], $longSize, $params["pbc"]["enable"] );
		echo $this->insertTextField( $params["boff"]["name"], $params["boff"]["label"], $params["boff"]["value"], $longSize, $params["boff"]["enable"] );
		echo $this->insertTextField( $params["itmax"]["name"], $params["itmax"]["label"], $params["itmax"]["value"], $longSize, $params["itmax"]["enable"] );
		echo $this->insertTextField( $params["ipmax"]["name"], $params["ipmax"]["label"], $params["ipmax"]["value"], $longSize, $params["ipmax"]["enable"] );
				
		echo "<br />\n";
		echo "<b>Card #6</b>\n";
		echo "<br />\n";
	
		echo $this->insertTextField( $params["target"]["name"], $params["target"]["label"], $params["target"]["value"], $longSize, $params["target"]["enable"] );
		echo $this->insertTextField( $params["thresh"]["name"], $params["thresh"]["label"], $params["thresh"]["value"], $longSize, $params["thresh"]["enable"] );
				
		echo "<br />\n";
		echo "<b>Card #7</b>\n";
		echo "<br />\n";
	
		echo $this->insertTextField( $params["rrec"]["name"], $params["rrec"]["label"], $params["rrec"]["value"], $longSize, $params["rrec"]["enable"], "(in &Aring;ngstroms; default Nyquist)" );
		echo $this->insertTextField( $params["hp"]["name"], $params["hp"]["label"], $params["hp"]["value"], $longSize, $params["hp"]["enable"], "(in &Aring;ngstroms)" );
		echo $this->insertTextField( $params["lp"]["name"], $params["lp"]["label"], $params["lp"]["value"], $longSize, $params["lp"]["enable"], "(in &Aring;ngstroms; default 2*Nyquist)" );
		echo $this->insertTextField( $params["rbfact"]["name"], $params["rbfact"]["label"], $params["rbfact"]["value"], $longSize, $params["rbfact"]["enable"], "(0 = off)" );
		
		// find if there are ctffind runs (for frealign option)
		$particle = new particledata();
		$showCTFFind = $particle->getCtfRunIds($_GET['expId'], $showHidden=False, $ctffind=True);
		
		// give option of only using ctffind runs
		if ( $showCTFFind ) {
			echo "<br/>\n";
			echo $this->insertCheckboxField($params["ctffindonly"]["name"], $params["ctffindonly"]["label"], $params["ctffindonly"]["value"], $params["ctffindonly"]["enable"] );
			echo "&nbsp;&nbsp;&nbsp;&nbsp;\n";
		}
	}
	
	function initialOrientForm()
	{
		// if importing reconstruction eulers
		if ($_POST['importrecon'] && $_POST['importrecon']!='None'){
			$_POST['initmethod']='importrecon';
			$_POST['write']='True';
			$importcheck='checked';
		}
		$angcheck = ($_POST['initmethod']=='projmatch' || !$_POST['write']) ? 'checked' : '';
		$inparfilecheck = ($_POST['initmethod']=='inparfile') ? 'checked' : '';
		$numiter = ($_POST['numiter']) ? $_POST['numiter'] : '10';
	
		/* ******************************************
		 INITIAL ORIENTATIONS BOX
		 ****************************************** */
	
		### Frealign initial search only
		$dang   = $_POST['dang'] ? $_POST['dang'] : '5';
		$initlp = $_POST['initlp'] ? $_POST['initlp'] : '25';
	
		echo "<br/>\n";
		echo openRoundBorder();
		echo "<table border='0' cellpadding='4' cellspacing='4'>\n";
		echo "<tr><td>\n";
		echo "<h4>Initial Orientations</h4>\n";
	
		echo "</td></tr><tr><td>\n";
	
		echo "<input type='radio' name='initmethod' value='importrecon' $importcheck>\n";
		$particle = new particledata();
		// Neil:: Switching code ; why do want recons from other sessions, we don't have a mathcing stack
		//$recons = $particle->getReconIdsFromSession($expId);
		$recons = $particle->getReconIterIdRelatedToStackid($stackid);
		if (is_array($recons)) {
			echo "<b>Import from EMAN reconstruction:</b>";
			echo "<br/>&nbsp;&nbsp;&nbsp; Reconstr.:\n";
			echo "<select name='importrecon' onchange='prepRefine.submit()'>\n";
			echo "   <option value='None'>Select Reconstruction</option>\n";
			foreach ($recons as $r) {
				$ropt = "<option value='".$r['DEF_id']."' ";
				$ropt.= ($_POST['importrecon']==$r['DEF_id']) ? 'selected':'';
				$ropt.= ">";
				$ropt.= $r['name']." (id: ".$r['DEF_id'].") -- ".substr($r['description'],0,60);
				$ropt.= "</option>\n";
				echo $ropt;
			}
		} else {
			echo "<i>no EMAN recons to import Euler angles</i>\n";
		}
		echo "</select>\n";
		echo "<br/>\n";
	
		// if a reconstruction has been selected, show iterations & resolutions
		if ($_POST['importrecon'] && $_POST['importrecon']!='None') {
			echo "&nbsp;&nbsp;&nbsp; Iteration:\n";
			$iterinfo = $particle->getRefinementData($_POST['importrecon']);
			echo "<select name='importiter'>\n";
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
			echo $iopt;
			echo "</select>\n";
			echo "<br/>\n";
		}
		echo "</td></tr><tr><td>\n";
	
		echo "<input type='radio' name='initmethod' value='projmatch' $angcheck>\n";
		echo "<b>Determine with Frealign</b>";
		echo "<br/>\n";
		echo docpop('dang',"&nbsp;&nbsp;&nbsp; Angular increment: ");
		echo " <input type='text' name='dang' value='$dang' size='4'>\n";
		echo "&nbsp;&nbsp;&nbsp; Initial LP filter: ";
		echo " <input type='text' name='initlp' value='$initlp' size='4'>\n";
	
		//echo "</td></tr><tr><td>\n";
	
		//echo "<input type='radio' name='initmethod' value='inparfile' $inparfilecheck>\n";
		//echo docpop('inpar',"Use input Frealign parameter file:");
		//echo " <input type='text' name='inparfile' value='$inparfile' size='50'>\n";
	
		echo "</td></tr><tr><td>\n";
	
		echo " <input type='text' name='numiter' value='$numiter' size='4'>\n";
		echo docpop('numiter','Number of refinement iterations')." <font size='-2'><i></i></font>\n";
		echo "<br/>\n";
	
		echo "</td></tr>\n";
		echo "</table>\n";
		echo closeRoundBorder();
		echo "<br/>\n";
	}


	public function buildCommand( $params )
	{
		/* *******************
		 PART 1: Get variables
		 ******************** */
//		$last 	= $_POST['last'];
//		$kv 	= $_POST['kv'];
//		$dang 	= ($_POST['initmethod']=='projmatch') ? $_POST["ang"] : '';
//		$inpar	= $_POST['inparfile'];
//		$importiter=$_POST['importiter'];
	
		/* *******************
		 PART 2: Check for conflicts, if there is an error display the form again
		 ******************** */
//	
//		if ($_POST['initmethod']=='projmatch' && !$_POST['dang'])
//		jobForm("<b>ERROR:</b> Enter an angular increment");
		
		
		$command = "prepFrealign.py ";
		$command.= "--stackid=$stackid ";
		if ($reconstackid)
			$command.= "--reconstackid=$reconstackid ";
		$command.= "--modelid=$modelid ";
		if ($importiter) $command.= "--reconiterid=$importiter ";
		if ($dang) $command.= "--dang=$dang ";
			    
		$command.= "--mask=".$params["outerMaskRadius"]["value"]." ";
		$command.= "--imask=".$params["innerMaskRadius"]["value"]." ";
		$command.= "--wgh=".$params["wgh"]["value"]." ";
		$command.= "--xstd=".$params["xstd"]["value"]." ";
		$command.= "--pbc=".$params["pbc"]["value"]." ";
		$command.= "--boff=".$params["boff"]["value"]." ";;
		$command.= "--itmax=".$params["itmax"]["value"]." ";
		$command.= "--ipmax=".$params["ipmax"]["value"]." ";
		$command.= "--sym=".$params["symmetry"]["value"]." ";
		$command.= "--target=".$params["target"]["value"]." ";
		$command.= "--thresh=".$params["thresh"]["value"]." ";
		$command.= "--rrec=".$params["rrec"]["value"]." ";
		$command.= "--hp=".$params["hp"]["value"]." ";
		$command.= "--lp=".$params["lp"]["value"]." ";
		$command.= "--rbfact=".$params["rbfact"]["value"]." ";
		$command.= "--numiter=".$params["numIters"]["value"]." ";

		if (!empty($params["ctffindonly"]["value"])) $command.= "--ctfmethod=ctffind ";
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
		
		$asymmSet = new FrealignParams( $id, $label, $outerMaskRadius, $innerMaskRadius, $outerAlignRadius, 
							$innerAlignRadius, $symmetry, $numIters, $angSampRate, $percentDiscard,  
							$filterEstimated, $filterResolution, $filterComputed, $filterConstant,
							$wgh, $xstd, $pbc, $boff, $itmax, $ipmax, $target,
							$thresh, $rrec, $hp, $lp, $rbfact, $ctffindonly );
		$this->addDefaultParams( $asymmSet );
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
							$thresh='', $rrec='', $hp='', $lp='', $rbfact='', $ctffindonly='' ) 
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
		
		// disable any general params that do not apply to this method
		$this->disableParam("outerAlignRadius");
		$this->disableParam("innerAlignRadius");
		$this->disableParam("angSampRate");
		$this->disableParam("percentDiscard");
		$this->disableParam("filterEstimated");
		$this->disableParam("filterComputed");
	}
	
	function validate() 
	{
		$parentMsg = parent::validate();
		
		$validator = new formValidator();
		 
		$validator->addValidation($this->params['outerMaskRadius']['name'], $this->params['outerMaskRadius']['value'], "req", "Enter an outer mask radius.");
		
		$validator->runValidation();
		$msg = $validator->getErrorMessage();	
		
		$errMsg = array_merge( $parentMsg, $msg );
		return $errMsg;
	}
}

?>
