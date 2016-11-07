<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicForm.inc";
require_once "inc/particledata.inc";

class DDStackSelectTable extends BasicForm
{
	protected $alignedDDStackIds; //array of (id=>runname)

	function __construct ($expId, $useDDStack=false, $ddstackid=false )
	{
		parent::__construct();
		$this->particle = new particledata();
		$this->alignedDDStackIds = $this->particle->getDDStackRunIdsAlign($expId);
		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );
		
		$params->addParam( "useDDStack",$useDDStack,"Use DD Stack");	
		$params->addParam( "ddstackid", $ddstackid, "Select an aligned framestack");
	}

	public function generateForm( $displayAdvanced=False )
	{
		$this->updateFormParams();
		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();
		
		$html.= "<!-- Start ddstack Selector -->\n";
		$html.=$params->insertCheckboxField("useDDStack");
		if(!$this->alignedDDStackIds) {
			$html.= "<font color='red'><B>No aligned ddstacks for this session</B></FONT>\n";
		} else{
			$onchange = "switchDefaults(this.value)";
//		$ddoptions[0] = 'Select DD stack';
			for($i=0;$i<count($this->alignedDDStackIds);$i++)
			{
				$ddoptions[$this->alignedDDStackIds[$i]['stackid']] = $this->alignedDDStackIds[$i]['runname'];
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
