<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicForm.inc";
require_once "inc/cluster.inc";

// TODO: docpop params need to change name: cputime, reconpernode, procpernode
class ClusterParamsForm extends BasicForm
{
	private $cluster;
	
	function __construct( $runFolder='',$processinghost='', $nodes='', $ppn='', $rpn='', $mem='', $walltime='', $cput='', $localhost='', $remoteoutdir='', $queue='' ) 
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
		$remoteoutdir = ( $remoteoutdir == '') ? $this->cluster->getPath($runFolder) : $remoteoutdir;
		$queue 		= ( $queue == '') ? $this->cluster->getQueue() : $queue;
		
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
		$params->addParam( "queue", $queue, "Queue" );
		
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
		
		// Add check for max values only if they have been set in the config file
		if ($this->cluster->getPpnMax() > 0) {
			$valcheck = "maxval=".$this->cluster->getPpnMax();
			$params->addValidation( "ppn", $valcheck );
		}
		if ( $this->cluster->getNodesMax() > 0 ) {
			$valcheck = "maxval=".$this->cluster->getNodesMax();
			$params->addValidation( "nodes", $valcheck );
		}
		if ( $this->cluster->getWallTimeMax() > 0 ) {
			$valcheck = "maxval=".$this->cluster->getWallTimeMax();
			$params->addValidation( "walltime", $valcheck );
		}
		if ( $this->cluster->getCpuTimeMax() > 0 ) {
			$valcheck = "maxval=".$this->cluster->getCpuTimeMax();
			$params->addValidation( "cput", $valcheck );
		}	
	}
	
	public function generateForm()
	{
		// if the user selects a new cluster, don't bother checking the previous values
		// or it will overwrite the new ones.
		$clusterSelection = $_POST['changehostname'];
		if ( !$clusterSelection ) {
			$this->updateFormParams();
		}
		
		// Get the cluster queue options 
		$queueOptions = $this->getQueueOptions();
		
		$params = $this->getFormParams();
		
		// set form field size
		$size = 4;
		
		//--- Cluster Parameters
		$html.= "<table border='0' cellpadding='4' cellspacing='4'>\n";
		
		// Insert Hidden Fields so they stick around after a reload
		$html.= $params->insertHiddenField("localhost");

		// row 1
		// add cluster selection box
		$html.= "<tr><td>\n";
		$html.= $this->instertHostSelectionBox();
		$html.= "</td>\n";
		$html.= "<td>\n";
		$html.= $params->insertTextFieldInRow( "processinghost", 20 );
		if ( $queueOptions ) {
			$html.= "</td>\n";
			$html.= "<td>\n";
			$html.= $params->insertSelectField("queue", $queueOptions);
		}
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
	
	public function generateFormBasic()
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
	
	private function getQueueOptions()
	{
		$queues = $this->cluster->getAvailableQueues();
		$options = array();
		
		if ( !empty($queues) ) {
			foreach ($queues as $queue) {
				// ignore empty lines and the header 'Queue'
				if ( $queue != '' && $queue != 'Queue') {
					$options[$queue] = $queue;
				}
			}
		}
		
		return $options;
	}	

	// returns the total number of processors requested by the 
	public function addNProcToCommand( $command )
	{
		// calculate the total number of nodes requested
		$params = $this->getFormParams();
		$numNodes = $params->getParamValue("nodes");
		$ppn = $params->getParamValue("ppn");
		$nproc = $numNodes * $ppn;
		
		$command = $this->addCommandFlag( $command, "nproc", "", $nproc );
		return $command;
	}
	
	// Override the validate function to add more complex validations than are available in the formValidator class.
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		
		$params = $this->getFormParams();
		$ppn = $params->getParamValue( "ppn" );
		$rpn = $params->getParamValue( "rpn" );
		
		if ( $rpn > $ppn ) {
			$msg .= "<B>Error:</B> Recons/Node may not be greater than Proc/Node";
		}
		
		return $msg;
	}	
}
?>
