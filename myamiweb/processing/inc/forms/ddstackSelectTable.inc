<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicForm.inc";
require_once "inc/particledata.inc";

class DDStackSelectTable extends BasicForm
{
	protected $ddStackIds; //array of (id=>runname)

	function __construct ($expId, $useDDStack=false, $ddstackid=false )
	{
		parent::__construct();
		$this->particle = new particledata();
		$this->only_aligned = true;
		$this->expId = $expId;
		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );
		
		$params->addParam( "useDDStack",$useDDStack,"Use DD Stack");	
		$params->addParam( "ddstackid", $ddstackid, "Select an aligned framestack");
	}

	public function setOnlyAligned( $value )
	{
		$this->only_aligned = $value;
	}

	public function generateForm( $displayAdvanced=False )
	{
		$this->updateFormParams();
		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();

		// Update label according to only_aligned		
		$this->ddStackIds = $this->particle->getDDStackRunIdsAlign($this->expId);
		$ddstack_type = 'aligned';
		if (!$this->only_aligned) {
			$unaligned = $this->particle->getDDStackRunIdsUnAligned($this->expId);
			$this->ddStackIds = array_merge($this->ddStackIds, $unaligned);
			$ddstack_type = '';
		}
		$params->setParamLabel("ddstackid","Select one ".$ddstack_type." framestack");
		$html.= "<!-- Start ddstack Selector -->\n";
		$html.=$params->insertCheckboxField("useDDStack");
		if(!$this->ddStackIds) {
			$html.= "<font color='red'><B>No ".$ddstack_type." ddstacks for this session</B></FONT>\n";
		} else{
			$onchange = "switchDefaults(this.value)";
//		$ddoptions[0] = 'Select DD stack';
			for($i=0;$i<count($this->ddStackIds);$i++)
			{
				$ddoptions[$this->ddStackIds[$i]['stackid']] = $this->ddStackIds[$i]['runname'];
			//      echo $ddoptions[$i];
			}

			$html .= $params->insertStackedSelectField("ddstackid",$ddoptions,'','',$onchange);
		}

		$html .= "<br />";
		$html.= "<!-- END ddstack Selector -->\n";
			
		return $html;
	}

	function buildCommand($postArray) {
		// This only includes command related to this form.
		$command = parent::buildCommand( $postArray );
		$this->updateFormParams();
		$params = $this->getFormParams();

		$useDDStackv = $params->getParamValue( 'useDDStack' );
		if ($useDDStackv != 'on') {
			return '';
		} else {
			$command = $this->removeCommandFlag($command,'useDDStack',null);
			return $command;
		}
	}
}

?>
