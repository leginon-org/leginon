<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "../inc/formParameters.inc";

// include the required cluster configuration file
$selectedcluster=$CLUSTER_CONFIGS[0];
if ($_POST['cluster']) {
	$selectedcluster=$_POST['cluster'];
}
$selectedcluster=strtolower($selectedcluster);
@include_once $selectedcluster.".php";

// TODO: docpop params need to change name: cputime, reconpernode, procpernode
class clusterParamsForm
{
	function __construct( $nodes='', $ppn='', $rpn='', $memory='', $walltime='', $cput='', $cluster='' ) 
	{
		$this->params = new FormParameters();
		
		// TODO: can I get default values from the cluster?
		
		$this->params->addParam( "nodes", $nodes, "Nodes" );
		$this->params->addParam( "ppn", $ppn, "Proc/Node" );
		$this->params->addParam( "rpn", $rpn, "Recons/Node" );
		$this->params->addParam( "memory", $memory, "Memory" );
		$this->params->addParam( "walltime", $walltime, "Wall Time" );
		$this->params->addParam( "cput", $cput, "CPU Time" );
		$this->params->addParam( "cluster", $cluster, "Select Host" );
	}
	
	public function generateForm( $postArray )
	{
		// if the form is being reloaded, make sure we keep anything the user already set.
		$this->params->getPostedValues( $postArray );
		
		$size = 4;
		
		// overall table
		$html.= "<table border='0'><tr><td valign='top'>"; 
	
		//--- Cluster Parameters
		$html.= openRoundBorder();
		$html.= "<table border='0' cellpadding='4' cellspacing='4'>\n";
		$html.= "<tr>\n";
		$html.= "<td colspan='4' align='center'>\n";
		$html.= "<h4>Processing Host Parameters</h4>\n";
		$html.= "</td>\n";
		$html.= "</tr><tr>\n";
		
		// row 1
		// add cluster selection box
		$html.= "<td>\n";
		$html.= $this->instertHostSelectionBox( "cluster" );
		$html.= "<b>Select Host</b>";
		$html.= "</td></tr>\n";
		
		// row 2
		$html.= "<tr><td>\n";
		$html.= $this->params->insertTextFieldInRow( "nodes", $size );
		$html.= "</td><td>\n";
		$html.= $this->params->insertTextFieldInRow( "ppn", $size );
		$html.= "</td><td>\n";
		$html.= $this->params->insertTextFieldInRow( "rpn", $size );
		$html.= "</td><td>\n";
		$html.= $this->params->insertTextFieldInRow( "memory", $size );

		// row 3
		$html.= "</td></tr><tr><td>\n";
		$html.= $this->params->insertTextFieldInRow( "walltime", $size, "(hours)" );
		$html.= "</td><td>\n";
		$html.= $this->params->insertTextFieldInRow( "cput", $size, "(hours)" );
		$html.= "</td></tr>\n";
		$html.= "</table>\n";
		
		//$html.= $clusterdata->cluster_parameters();
		$html.= closeRoundBorder();
		$html.= "<br/>\n";
		$html.= "<br/>\n";
	
		$html.="</td></tr></table>"; //overall table		
					
		$html.= "<br/>\n";

		return $html;
	}
	
	private function instertHostSelectionBox( $name )
	{
		global $clusterdata, $CLUSTER_CONFIGS, $selectedcluster;
		
		$value = $this->params->getParamValue( $name );
		
		// TODO: handle the onchange
		$html.= "<select name='$name' onchange='frealignjob.submit()'>\n";
		foreach ($CLUSTER_CONFIGS as $cluster) {
			$s = ($cluster == $value) ? 'selected' : '';
			$html.= '<option value="'.$cluster.'" '.$s.' >'.$cluster.'</option>'."\n";
		}
		$html.= "</select>\n";
		
		return $html;
	}
	
	public function validate( $postArray )
	{
		$this->params->getPostedValues( $postArray );
		$msg = $this->params->validate();
		
		return $msg;
	}
	
	// TODO: probably dont need this...as the rundir and runname are already added to the command. 
	// may need to change our "outdir" to "rundir" for it to work.
	public function buildCommand( $postArray )
	{
		$this->params->getPostedValues( $postArray );
		$paramArray = $this->params->getParamArray();
		
		// runname and outdir are currently handled in showOrSubmitCommand().
		// TODO: Pull params out of showOrSubmitCommand and move to general form for all processing
		//$command = "--rp_runname=".$paramArray["runname"]["value"]." ";
		//$command.= "--rp_outdir=".$paramArray["outdir"]["value"]." ";
		$command.= "--description=".$paramArray["description"]["value"]." ";
		
		return $command;
	}
	
}
?>