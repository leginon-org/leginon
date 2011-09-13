<?php

require_once "refineJobs.inc";


class RefineJobsSingleModel extends RefineJobs
{
	public function setDBValues()
	{
		$this->methods 		= array("xmipprecon", "emanrecon", "frealignrecon");
		$this->prepTypes 	= array("preprefinexmipp", "preprefineeman", "preprefinefrealign");
		$this->refineTypes 	= array("xmipprecon", "emanrecon", "frealignrecon");
		$this->uploadTypes 	= array("uploadrecon");
	}
	public function getUploadRefineDone()
	{
		$reconRuns = $this->particle->getSingleModelReconIdsFromSession( $this->expId );
		return $reconRuns;
	}		
}

?>