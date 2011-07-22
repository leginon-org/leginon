<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicForm.inc";

// include the required cluster configuration file
$selectedcluster=$CLUSTER_CONFIGS[0];
if ($_POST['changecluster']) {
	$selectedcluster = $_POST['changecluster'];
} elseif ( $_POST['cluster'] ) {
	$selectedcluster = $_POST['cluster'];
}
$selectedcluster=strtolower($selectedcluster);
@include_once $selectedcluster.".php";

// TODO: docpop params need to change name: cputime, reconpernode, procpernode
class clusterParamsForm extends BasicForm
{
	function __construct( $nodes='', $ppn='', $rpn='', $mem='', $walltime='', $cput='', $cluster='', $remoteoutdir='' ) 
	{
		parent::__construct();		
		
		// Set default values based on the selected cluster
		$nodes 		= ( $nodes == '') ? C_NODES_DEF : $nodes;
		$ppn 		= ( $ppn == '') ? C_PPN_DEF : $ppn;
		$rpn 		= ( $rpn == '') ? C_RPROCS_DEF : $rpn;
		$mem 		= ( $mem == '') ? C_MEMORY_MAX : $mem;
		$walltime 	= ( $walltime == '') ? C_WALLTIME_DEF : $walltime;
		$cput 		= ( $cput == '') ? C_CPUTIME_DEF : $cput;

		// TODO: known issue- the first time through, if a host is returning the path
		// based on the $_POST var containing the outdir, the remoteoutdir will be blank
		// because the outdir has not been posted.
		if ( $remoteoutdir == '' ) {
			global $clusterdata;
			$clusterdata->post_data();
			$remoteoutdir = $clusterdata->get_path();
		}
		
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "cluster" );
				
		$params->addParam( "nodes", $nodes, "Nodes" );
		$params->addParam( "ppn", $ppn, "Proc/Node" );
		$params->addParam( "rpn", $rpn, "Recons/Node" );
		$params->addParam( "mem", $mem, "Memory" );
		$params->addParam( "walltime", $walltime, "Wall Time" );
		$params->addParam( "cput", $cput, "CPU Time" );
		$params->addParam( "cluster", $cluster, "Select Host" );
		$params->addParam( "remoteoutdir", $remoteoutdir, "Processing host output directory" );
		
		// add validations
		$params->addValidation( "nodes", "req" );
		$params->addValidation( "nodes", "num" );
		$params->addValidation( "ppn", "req" );
		$params->addValidation( "ppn", "num" );
		$params->addValidation( "walltime", "req" );
		$params->addValidation( "walltime", "num" );
		$params->addValidation( "cput", "req" );
		$params->addValidation( "cput", "num" );
		
		$valcheck = "maxval=".C_PPN_MAX;
		$params->addValidation( "ppn", $valcheck );
		$valcheck = "maxval=".C_NODES_MAX;
		$params->addValidation( "nodes", $valcheck );
		$valcheck = "maxval=".C_WALLTIME_MAX;
		$params->addValidation( "walltime", $valcheck );
		$valcheck = "maxval=".C_CPUTIME_MAX;
		$params->addValidation( "cput", $valcheck );	

	}
	
	public function generateForm()
	{
		global $selectedcluster;
		// if the user selects a new cluster, get the default values here
		$clusterSelection = $_POST['changecluster'];
		$this->updateFormParams( $clusterSelection );
		$params = $this->getFormParams();
		$html.= "<input type='hidden' NAME='cluster' value='".$selectedcluster."'>\n";
		
		// set form field size
		$size = 4;
		
		//--- Cluster Parameters
		$html.= "<table border='0' cellpadding='4' cellspacing='4'>\n";

		// row 1
		// add cluster selection box
		$html.= "<tr><td>\n";
		$html.= $this->instertHostSelectionBox( "cluster" );
		$html.= "</td>\n";
		$html.= "<td>\n";
		$html.= "<b>Selected Host:</b> ".$selectedcluster;
		$html.= "</td></tr>\n";
		
		// row 2
		$html.= "<tr><td>\n";
		$html.= $params->insertTextFieldInRow( "nodes", $size );
		$html.= "</td><td>\n";
		$html.= $params->insertTextFieldInRow( "ppn", $size );
		$html.= "</td><td>\n";
		$html.= $params->insertTextFieldInRow( "rpn", $size );
		$html.= "</td></tr>";

		// row 3
		$html.= "<tr><td>\n";
		$html.= $params->insertTextFieldInRow( "walltime", $size, "(hours)" );
		$html.= "</td><td>\n";
		$html.= $params->insertTextFieldInRow( "cput", $size, "(hours)" );
		$html.= "</td><td>\n";
		$html.= $params->insertTextFieldInRow( "mem", $size );
		$html.= "</td></tr>\n";
		
		// row 4
		$html.= "<tr><td colspan=3>\n";
		$html.= $params->insertTextFieldInRow( "remoteoutdir", 50 );
		$html.= "</td></tr>\n";
		
		// End table
		$html.= "</table>\n";
		
		return $html;
	}
	
	private function instertHostSelectionBox()
	{
		global $CLUSTER_CONFIGS;
		
		$html.= "<select name='changecluster' onchange='this.form.submit()'>\n";
		$html.= '<option value=""> Change Host Selection </option>'."\n";
		foreach ($CLUSTER_CONFIGS as $cluster) {
			$html.= '<option value="'.$cluster.'" >'.$cluster.'</option>'."\n";
		}
		$html.= "</select>\n";
		
		return $html;
	}	
	
	// points the form parameters to the correct set of default
	// values based on the users selection.
	// Takes the default set Id, which corresponds to a set available
	// in the "Import Parameters" drop down list.
	final protected function updateFormParams( $defaultSetId='' )
	{
		global $CLUSTER_CONFIGS;
		$params = &$this->getFormParams();
		
		if (in_array($defaultSetId, $CLUSTER_CONFIGS) ) {

			// TODO: I don't think we need to include all this setting here,
			// since when we select a new cluster, the form is reloaded and 
			// the constructor is called. Are there other cases when we may want to call this?
			$params->setParamValue( 'nodes', C_NODES_DEF );
			$params->setParamValue( 'ppn', C_PPN_DEF );
			$params->setParamValue( 'rpn', C_RPROCS_DEF );
			$params->setParamValue( 'mem', C_MEMORY_MAX );
			$params->setParamValue( 'walltime', C_WALLTIME_DEF );
			$params->setParamValue( 'cput', C_CPUTIME_DEF );

			global $clusterdata;
			$clusterdata->post_data();
			$remoteoutdir = $clusterdata->get_path();
			$params->setParamValue( 'remoteoutdir', $remoteoutdir );
			
			// TODO: this might not work...may need to remove old validations first
			$valcheck = "maxval=".C_PPN_MAX;
			$params->addValidation( "ppn", $valcheck );
			$valcheck = "maxval=".C_NODES_MAX;
			$params->addValidation( "nodes", $valcheck );
			$valcheck = "maxval=".C_WALLTIME_MAX;
			$params->addValidation( "walltime", $valcheck );
			$valcheck = "maxval=".C_CPUTIME_MAX;
			$params->addValidation( "cput", $valcheck );
			
		} else {
			parent::updateFormParams( $defaultSetId );
		}
	}
}
?>