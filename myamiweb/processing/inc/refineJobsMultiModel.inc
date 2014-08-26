<?php

require_once "refineJobs.inc";


class RefineJobsMultiModel extends RefineJobs
{
	public function setDBValues()
	{
		$this->methods 		= array("xmippml3d","xmippml3drecon");
		$this->prepTypes 	= array("preprefinexmippml3d");
		$this->refineTypes 	= array("xmippml3d","xmippml3drecon");
		$this->uploadTypes 	= array("uploadrecon");
	}	
	public function getUploadRefineDone()
	{
		$reconRuns = $this->particle->getMultiModelReconIdsFromSession( $this->expId );
		return $reconRuns;
	}	
}

?>