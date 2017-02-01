<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicForm.inc";
require_once "runParametersForm.inc";
require_once "clusterParamsForm.inc";

class RemoteJobParamsForm extends BasicForm
{
	
	protected $runname;
	protected $outdir;
	protected $description;
	protected $showDesc;
	protected $processinghost;
	protected $nodes;
	protected $ppn;
	protected $rpn;
	protected $mem;
	protected $walltime;
	protected $cput;
	protected $localhost;
	protected $remoteoutdir;
	protected $queue;
	
	function __construct( $runname='', $outdir='', $description='', $showDesc=True, 
							$processinghost='', $nodes='', $ppn='', $rpn='', $mem='', 
							$walltime='', $cput='', $localhost='', $remoteoutdir='', $queue='' ) 
	{
		parent::__construct();
		
		//TODO: use these to initialize the cluster params form if needed.
		$this->runname 		= $runname;
		$this->outdir 		= $outdir;
		$this->description 	= $description;
		$this->showDesc		= $showDesc;
		$this->processinghost = $processinghost;
		$this->nodes 		= $nodes;
		$this->ppn 			= $ppn;
		$this->rpn 			= $rpn;
		$this->mem 			= $mem;
		$this->walltime 	= $walltime;
		$this->cput 		= $cput;
		$this->localhost 	= $localhost;
		$this->remoteoutdir = $remoteoutdir;
		$this->queue 		= $queue;
		$this->showRemoteOutDir	= false;
		$this->enableLocalHost = false;
	}
	
	function setShowRemoteOutDir( $showRemoteOutDir )
	{
		$this->showRemoteOutDir = $showRemoteOutDir;
	}
	
	function setEnableLocalHost( $enableLocalHost )
	{
		$this->enableLocalHost = $enableLocalHost;
	}
	
	public function generateForm()
	{
		// if the form is being reloaded, make sure we keep anything the user already set.
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		// Create the run parameters form
		$runParamsForm = new RunParametersForm( $runname=$this->runname, $outdir=$this->outdir, $description='', $this->showDesc );
		$html .= $runParamsForm->generateForm();
		
		$html .= "<H4 style='align=\'center\' >Processing Host Parameters</H4><hr />";
		
		// Create the cluster params form 
		$runFolder = basename($this->outdir);
		$clusterParamsForm = new ClusterParamsForm($runFolder);
		$clusterParams = $clusterParamsForm->getFormParams();
		if ( !$this->showRemoteOutDir ) $clusterParams->hideParam('remoteoutdir');
		$clusterParams->hideParam('rpn');
		
		$html.= $clusterParamsForm->generateForm();

		return $html;
	}	
	
	// Override the validate function so that we can verify the appionLoopTable parameters
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );

		$clusterParamsForm = new ClusterParamsForm($this->outDir);
		$msg .= $clusterParamsForm->validate( $postArray );

		$runParametersForm = new RunParametersForm();
		$msg .= $runParametersForm->validate( $postArray );

		
		return $msg;
	}
	
	public function buildCommand( $postArray )
	{
		$command = parent::buildCommand( $postArray );
		
		$clusterParamsForm = new ClusterParamsForm($this->outDir);
		$command .= $clusterParamsForm->buildCommand( $postArray );

		// add params from run parameters form
		$runParametersForm = new RunParametersForm();
		$command .= $runParametersForm->buildCommand( $postArray );
		
		// Remove params from the command that are not needed by simple remote jobs
		$command = $clusterParamsForm->removeCommandFlag( $command, "processinghost" );
		$command = $clusterParamsForm->removeCommandFlag( $command, "rpn" );
		if ( !$this->showRemoteOutDir ) $command = $clusterParamsForm->removeCommandFlag( $command, "remoteoutdir" );
		if ( !$this->enableLocalHost) $command = $clusterParamsForm->removeCommandFlag( $command, "localhost" );
		
		// If the user selects to just show the command, we do not want to supply the selected queue.
		if ( $postArray['process'] == "Just Show Command" ) {
			$command = $clusterParamsForm->removeCommandFlag( $command, "queue" );
		}
		
		return $command;		
	}
	
}
?>
