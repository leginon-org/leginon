<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "stackPrepForm.inc";
require_once "inc/particledata.inc";

class StackPrepFormFrealign extends StackPrepForm
{
	function __construct( $stackid='', $lastParticle='', $lowpass='', $highpass='', $bin='', $reconiterid='', $emaninit='', $ctffindonly='', $ctftilt='', $paramonly='' ) 
	{
		parent::__construct($lastParticle, $lowpass, $highpass, $bin);
		$params = $this->getFormParams();
				
		// add a couple of params to the basic prep refine params
		$params->addParam( "reconiterid", $reconiterid, "previous EMAN refinement iteration for initializing particle orientation" );
		$params->addParam( "emaninit", $emaninit, "Import initial orientations from completed reconstruction:" );
		$params->addParam( "ctffindonly", $ctffindonly, "Only use CTFFIND3 values" );
		$params->addParam( "ctftilt", $ctftilt, "Only use CTFTilt values" );
		$params->addParam( "paramonly", $paramonly, "Only create the Frealign paramter file, not the stack");
		
		// Frealign does not need the filter params 
		// that are defined in the base class
		$params->hideParam("lowpass");
		$params->hideParam("highpass");
		
		$this->stackid = $stackid;
	}
	
	public function generateForm()
	{
		// The size of the text fields
		$shortSize = 4;
		
		// get the html for the basic prep refine form
		$html = parent::generateForm();
		$params = $this->getFormParams();
		
		// make sure we are using the appropriate pop-up help messages
		$params->setHelpSection( "frealign" );	
				
		$html .=  $params->insertCheckboxField( "emaninit");
		$html .=  $this->addReconSelectBox();
					
		$html.= "<br/>\n";
		
		// find if there are ctffind runs (for frealign option)
		$particle = new particledata();
		$showCTFFind = $particle->getCtfRunIds($_GET['expId'], $showHidden=False, $ctffind=True);
			
		// give option of only using ctffind runs
		if ( $showCTFFind ) {
			$html .=  "<br/>\n";
			$html .=  $params->insertCheckboxField( "ctffindonly" );
		}
		// find if there are ctftilt runs (for frealign option)
		$showCTFTilt = $particle->hasCtfTiltData($_GET['expId']);
		if ( $showCTFTilt ) {
			$html .=  "<br>\n";
			$html .=  $params->insertCheckboxField( "ctftilt" );
		}

		$html.= "<br/>\n";

		$html .= $params->insertCheckboxField( "paramonly");
		return $html;
	}
	
	// Override the basic build command function to include the ctffind flag.
	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand($postArray);
		$params = $this->getFormParams();
						
		// see if checkbox was selected
		// TODO: use addCommandFlag()?
		$ctffindonly = $params->getParamValue("ctffindonly");
		if ( $ctffindonly == 'on' ) $command.= "--ctfmethod=ctffind ";
		
		// see if emaninit checkbox was selected
		$emaninit = $params->getParamValue("emaninit");
		if ( $emaninit != 'on' ) {
			$command = $this->removeCommandFlag($command, "reconiterid" );		
		}

		// remove params not needed in command
		$command = $this->removeCommandFlag($command, "ctffindonly" );
		$command = $this->removeCommandFlag($command, "emaninit" );
		
		return $command;
	}	
	
	function addReconSelectBox()
	{
		$particle = new particledata();
		$stackid = $this->stackid;
		
		if ( $stackid === '' ) {
			$html = "<i>Error: Unable to determine selected stack ID.</i>\n";
			return $html;
		}
		$recons = $particle->getReconIterIdRelatedToStackid($stackid);
		$html .=  "&nbsp;&nbsp;&nbsp; Reconstruction:\n";
		
		if (!empty($recons)) {
			$html .=  "<select name='importrecon' onchange='prepRefine.submit()'>\n";
			$html .=  "   <option value='None'>Select Reconstruction</option>\n";
			
			foreach ($recons as $r) {
				$ropt = "<option value='".$r['DEF_id']."' ";
				$ropt.= ($_POST['importrecon'] == $r['DEF_id']) ? 'selected':'';
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
			$html .=  "<select name='reconiterid'>\n";
			
			if (is_array($iterinfo)) {
				foreach ($iterinfo as $iter){
					$iterstuff = $particle->getIterationInfo($_POST['importrecon'],$iter['iteration']);
					$rmeas = $particle->getRMeasureInfo($iter['REF|ApRMeasureData|rMeasure']);
					$fsc = $particle->getResolutionInfo($iter['REF|ApResolutionData|resolution']);
					$iopt.="<option value='".$iter['DEF_id']."' ";
					$iopt.= ($_POST['reconiterid']==$iter['DEF_id']) ? 'selected':'';
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
	
}
?>
