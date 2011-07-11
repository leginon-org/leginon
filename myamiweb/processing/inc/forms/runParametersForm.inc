<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicForm.inc";

class RunParametersForm extends BasicForm

{
	function __construct( $runname='', $outdir='', $description='' ) 
	{
		parent::__construct();
		$params = $this->getFormParams();
				
		$params->addParam( "runname", $runname, "Run name" );
		$params->addParam( "outdir", $outdir, "Output directory" );
		$params->addParam( "description", $description, "Description" );
	}
		
	public function generateForm()
	{
		// if the form is being reloaded, make sure we keep anything the user already set.
		//$this->params->getPostedValues( $postArray );
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$html = "
	    <br />
	    <H4>Processing Run Parameters</H4>
	    <hr />";
		
		$html.= $params->insertStackedTextField( "runname", 20 );
		$html.= "<br/>\n";
		$html.= $params->insertStackedTextField( "outdir", 56 );
		$html.= "<br/>\n";
		$html.= $params->insertTextArea( "description");
			
		$html.= "<br/>\n";

		return $html;
	}	
	
	// override build Command because runname and outdir are a special case, they
	// are handled in showOrSubmitCommand. We should refactor appion so all methods
	// use this class and remove the special cases.
	public function buildCommand( $postArray )
	{
		$params = $this->getFormParams();
		$params->getPostedValues( $postArray );
		
		$command = $this->addCommandFlag( $command, "description" );
		
		//$this->params->getPostedValues( $postArray );
		//$paramArray = $this->params->getParamArray();
		
		// runname and outdir are currently handled in showOrSubmitCommand().
		// TODO: Pull params out of showOrSubmitCommand and move to general form for all processing
		//$command = "--runname=".$paramArray["runname"]["value"]." ";
		//$command.= "--outdir=".$paramArray["outdir"]["value"]." ";
		//$command.= "--description=".$paramArray["description"]["value"]." ";
		
		return $command;
	}
	
}
?>