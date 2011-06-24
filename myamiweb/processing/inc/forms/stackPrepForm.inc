<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "../inc/formParameters.inc";


class StackPrepForm
{
	function __construct( $lastParticle='', $lpFilter='', $hpFilter='', $binning='' ) 
	{
		$this->params = new FormParameters();
		
		$this->params->addParam( "lastParticle", $lastParticle, "last particle to use" );
		$this->params->addParam( "lpFilter", $lpFilter, "low-pass filter" );
		$this->params->addParam( "hpFilter", $hpFilter, "high-pass filter" );
		$this->params->addParam( "binning", $binning, "binning" );
	}
	
	public function generateForm( $postArray )
	{
		// if the form is being reloaded, make sure we keep anything the user already set.
		$this->params->getPostedValues( $postArray );

		$html = "
	    <br />
	    <H4>Stack Preparation Parameters</H4>
	    <hr />";
	
		$html.= $this->params->insertTextField( "lastParticle", 4 );
		$html.= $this->params->insertTextField( "lpFilter", 4, "(angstroms)" );
		$html.= $this->params->insertTextField( "hpFilter", 4, "(angstroms)" );
		$html.= $this->params->insertTextField( "binning", 4 );
			
		$html.= "<br/>\n";

		return $html;
	}
	
	public function validate( $postArray )
	{
		$this->params->getPostedValues( $postArray );
		$msg = $this->params->validate();
		
		return $msg;
	}
	
	public function buildCommand( $postArray )
	{
		$this->params->getPostedValues( $postArray );

		$sp_lastParticle 	= $this->params->getParamValue( "lastParticle" ); 
		$sp_lpFilter	 	= $this->params->getParamValue( "lpFilter" ); 
		$sp_hpFilter 		= $this->params->getParamValue( "hpFilter" ); 
		$sp_binning 		= $this->params->getParamValue( "binning" ); 
		
		if ($sp_lastParticle != '') $command = "--sp_lastParticle=".$sp_lastParticle." ";
		if ($sp_lpFilter != '') $command.= "--sp_lpFilter=".$sp_lpFilter." ";
		if ($sp_hpFilter != '') $command.= "--sp_hpFilter=".$sp_hpFilter." ";
		if ($sp_binning != '') $command.= "--sp_binning=".$sp_binning." ";
		
		return $command;
	}
	
}
?>