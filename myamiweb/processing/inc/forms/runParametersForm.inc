<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "../inc/formParameters.inc";

class RunParametersForm
{
	function __construct( $runname='', $outdir='' ) 
	{
		$this->params = new FormParameters();
		
		$this->params->addParam( "runname", $runname, "Run name" );
		$this->params->addParam( "outdir", $outdir, "Output directory" );
	}
	
	public function generateForm( $postArray )
	{
		// if the form is being reloaded, make sure we keep anything the user already set.
		$this->params->getPostedValues( $postArray );

		$html = "
	    <br />
	    <H4>Processing Run Parameters</H4>
	    <hr />";
	
		$html.= $this->params->insertStackedTextField( "runname", 20 );
		$html.= "<br/>\n";
		$html.= $this->params->insertStackedTextField( "outdir", 50 );
			
		$html.= "<br/>\n";

		return $html;
	}
	
	// TODO: probably dont need this...as the rundir and runname are already added to the command. 
	// may need to change our "outdir" to "rundir" for it to work.
	public function buildCommand( $postArray )
	{
		$this->params->getPostedValues( $postArray );
		$paramArray = $this->params->getParamArray();
		
		$command = "--rp_runname=".$paramArray["runname"]["value"]." ";
		$command.= "--rp_outdir=".$paramArray["outdir"]["value"]." ";
		
		return $command;
	}
	
}
?>