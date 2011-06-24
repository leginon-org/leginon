<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "../inc/formParameters.inc";
require_once "runParametersForm.inc";

class RunParametersReport extends RunParametersForm
{
	public function generateForm( $postArray )
	{
		// if the form is being reloaded, make sure we keep anything the user already set.
		$this->params->getPostedValues( $postArray );
		$paramArray = $this->params->getParamArray();

		// Display Run Parameters form
		$html.= "<table border='0' cellpadding='0' cellspacing='0' width='650'>\n";
		$html.= "<tr><td>\n";
		$html.= openRoundBorder();
		$html.= "<table border='0' cellpadding='4' cellspacing='4'>\n";
		
		foreach ( $paramArray as $key=>$param ) {
			$html.= "<tr><td><b>".$param['label'].":</b></td><td>".$param['value']."</td></tr>\n";
			// Since just displaying the values does not add them to the post array, 
			// post them here so we can still add them to a command later 
			$html.= "<input type='hidden' NAME='".$param['name']."' value='".$param['value']."'>\n";
		}
//		$html.= "<input type='hidden' name='runname' value='$name'>\n";
//		$html.= "<tr><td><b>Run Directory:</b></td><td>$rundir</td></tr>\n";
//		$outdir = ereg_replace($name."$", "", $rundir);
//		$html.= "<input type='hidden' name='rundir' value='$rundir'>\n";
//		$html.= "<input type='hidden' name='outdir' value='$outdir'>\n";
		$html.= "</table>\n";
		$html.= closeRoundBorder();
		$html.= "</td></tr>\n";
		$html.= "</table>\n";
		
		$html.= "<br/>\n";

		return $html;
	}
}	
?>