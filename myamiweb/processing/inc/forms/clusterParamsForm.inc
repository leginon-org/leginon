<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicForm.inc";
require_once "inc/cluster.inc";

// TODO: docpop params need to change name: cputime, reconpernode, procpernode
class ClusterParamsForm extends BasicForm
{
	private $cluster;
	
	function __construct( $processinghost='', $nodes='', $ppn='', $rpn='', $mem='', $walltime='', $cput='', $localhost='', $remoteoutdir='' ) 
	{
		parent::__construct();		
		
		// create a new cluster object, use the first occurance of a processing host
		// in the config.php file if needed.
		if ($_POST['changehostname']) {
			$processinghost = $_POST['changehostname'];
		} else if ($_POST['processinghost']) {
			$processinghost = $_POST['processinghost'];
		} else {
			global $PROCESSING_HOSTS;
			$processinghost = ( $processinghost == '') ? $PROCESSING_HOSTS[0]['host'] : $processinghost;
		}
		
		$this->cluster = new Cluster( $processinghost );
		
		// Set default values based on the selected cluster
		$nodes 		= ( $nodes == '') ? $this->cluster->getNodesDef() : $nodes;
		$ppn 		= ( $ppn == '') ? $this->cluster->getPpnDef() : $ppn;
		$rpn 		= ( $rpn == '') ? $this->cluster->getRpnDef() : $rpn;
		$mem 		= ( $mem == '') ? $this->cluster->getMemoryMax() : $mem;
		$walltime 	= ( $walltime == '') ? $this->cluster->getWallTimeDef() : $walltime;
		$cput 		= ( $cput == '') ? $this->cluster->getCpuTimeDef() : $cput;
		$localhost 	= ( $localhost == '') ? $this->cluster->getLocalHelperHost() : $localhost;
		$remoteoutdir = ( $remoteoutdir == '') ? $this->cluster->get_path() : $remoteoutdir;
		
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "cluster" );
				
		$params->addParam( "processinghost", $processinghost, "Selected Host" );
		$params->addParam( "nodes", $nodes, "Nodes" );
		$params->addParam( "ppn", $ppn, "Proc/Node" );
		$params->addParam( "rpn", $rpn, "Recons/Node" );
		$params->addParam( "mem", $mem, "Memory" );
		$params->addParam( "walltime", $walltime, "Wall Time" );
		$params->addParam( "cput", $cput, "CPU Time" );
		$params->addParam( "localhost", $localhost, "Local host for rsync from remote host" ); //local host the the remote host can use to rsync results to (not editable)
		$params->addParam( "remoteoutdir", $remoteoutdir, "Processing host output directory" );
		
		// add validations
		$params->addValidation( "processinghost", "req" );
		$params->addValidation( "nodes", "req" );
		$params->addValidation( "nodes", "num" );
		$params->addValidation( "ppn", "req" );
		$params->addValidation( "ppn", "num" );
		$params->addValidation( "walltime", "req" );
		$params->addValidation( "walltime", "num" );
		$params->addValidation( "cput", "req" );
		$params->addValidation( "cput", "num" );
		
		$valcheck = "maxval=".$this->cluster->getPpnMax();
		$params->addValidation( "ppn", $valcheck );
		$valcheck = "maxval=".$this->cluster->getNodesMax();
		$params->addValidation( "nodes", $valcheck );
		$valcheck = "maxval=".$this->cluster->getWallTimeMax();
		$params->addValidation( "walltime", $valcheck );
		$valcheck = "maxval=".$this->cluster->getCpuTimeMax();
		$params->addValidation( "cput", $valcheck );	
	}
	
	public function generateForm()
	{
		// if the user selects a new cluster, don't bother checking the previous values
		// or it will overwrite the new ones.
		$clusterSelection = $_POST['changehostname'];
		if ( !$clusterSelection ) {
			$this->updateFormParams();
		}
		
		$params = $this->getFormParams();
		
		// set form field size
		$size = 4;
		
		//--- Cluster Parameters
		$html.= "<table border='0' cellpadding='4' cellspacing='4'>\n";

		// row 1
		// add cluster selection box
		$html.= "<tr><td>\n";
		$html.= $this->instertHostSelectionBox();
		$html.= "</td>\n";
		$html.= "<td>\n";
		$html.= $params->insertTextFieldInRow( "processinghost", 20 );
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
		global $PROCESSING_HOSTS;
		
		$html.= "<select name='changehostname' onchange='this.form.submit()'>\n";
		$html.= '<option value=""> Change Host Selection </option>'."\n";
		foreach ($PROCESSING_HOSTS as $cluster) {
			$html.= '<option value="'.$cluster['host'].'" >'.$cluster['host'].'</option>'."\n";
		}
		$html.= "</select>\n";
				
		return $html;
	}	
}
?>