<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "stackPrepForm.inc";
require_once "inc/particledata.inc";

class StackPrepFormFrealign extends StackPrepForm
{
	function __construct( $stackid='', $lastParticle='', $lowpass='', $highpass='', $bin='', $reconiterid='', $noctf='', $dang='', $initlp='', $initmethod='', $ctffindonly='' ) 
	{
		parent::__construct($lastParticle, $lowpass, $highpass, $bin);
		$params = $this->getFormParams();
				
		// add a couple of params to the basic prep refine params
		$params->addParam( "reconiterid", $reconiterid, "previous EMAN refinement iteration for initializing particle orientation" );
		$params->addParam( "noctf", $noctf, "Allow Frealign to determine ctf estimation" );
		$params->addParam( "dang", $dang, "Angular increment" );
		$params->addParam( "initlp", $initlp, "Initial LP filter" );
		$params->addParam( "initmethod", $initmethod, "Initial orientation method" );
		$params->addParam( "ctffindonly", $ctffindonly, "Only use CTFFIND values" );
		
		$this->stackid = $stackid;
	}
	
	public function generateForm()
	{
		// The size of the text fields
		$shortSize = 4;
		
		// get the html for the basic prep refine form
		$html = parent::generateForm();
		$params = $this->getFormParams();
	
		$html.= $params->insertCheckboxField("noctf");
		
		// Don't include the ctffindonly flag for now
		$usectffindonly = false;
		if ( $usectffindonly ) {
			// find if there are ctffind runs (for frealign option)
			$particle = new particledata();
			$showCTFFind = $particle->getCtfRunIds($_GET['expId'], $showHidden=False, $ctffind=True);
			
			// give option of only using ctffind runs
			if ( $showCTFFind ) {
				$html .=  "<br/>\n";
				$html .=  $params->insertCheckboxField( "ctffindonly" );
				$html .=  "&nbsp;&nbsp;&nbsp;&nbsp;\n";
			}
		}
		
		$html .=  "<br />\n";
		$html .=  "<b>Initial Orientations</b>\n";
		$html .=  "<br />\n";
		
		$html .=  $params->insertRadioField( "initmethod", "importrecon", "Import from EMAN reconstruction:");
		$html .=  $this->addReconSelectBox();

		$html .=  "<br />\n";
		
		$html .=  $params->insertRadioField( "initmethod", "projmatch", "Determine with Frealign" );
		$html .=  "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n";		
		$html .=  $params->insertTextField( "dang", $shortSize );
		$html .=  "&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;\n";
		$html .=  $params->insertTextField( "initlp", $shortSize );
					
		$html.= "<br/>\n";

		return $html;
	}
	
	// Override the basic build command function to include the 
	// logic required for the initial orientation flags.
	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand($postArray);
		$params = $this->getFormParams();
		
		// check which radio button was selected
		// if neither were selected, remove all flags related to orientation
		if ( $params->getParamValue("initmethod") == 'projmatch' ) {
			$command = $this->removeCommandFlag($command, "reconiterid" );
		} else if ( $params->getParamValue("initmethod") == 'importrecon' ) {
			$command = $this->removeCommandFlag($command, "dang" );			
			$command = $this->removeCommandFlag($command, "initlp" );			
		} else {
			$command = $this->removeCommandFlag($command, "dang" );			
			$command = $this->removeCommandFlag($command, "initlp" );			
			$command = $this->removeCommandFlag($command, "reconiterid" );
		}
						
		// see if checkbox was selected
		$ctffindonly = $params->getParamValue("ctffindonly");
		if ( $ctffindonly == 'on' ) $command.= "--ctfmethod=ctffind ";
		
		// remove params not needed in command
		$command = $this->removeCommandFlag($command, "initmethod" );
		$command = $this->removeCommandFlag($command, "ctffindonly" );
		
		return $command;
	}	
	
	// add custom parameter validations
	public function validate($postArray) 
	{
		$msg = parent::validate($postArray);
		$params = $this->getFormParams();

		if ( ($_POST['initmethod'] == 'projmatch') && $params->getParamValue("dang")=='' ) {
			$msg .= "<b>Error:</b> Enter an angular increment";
		}
		
		return $msg;
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