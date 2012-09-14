<?php

require_once "refineJobs.inc";


class RefineJobsSingleModel extends RefineJobs
{
	public function setDBValues()
	{
		$this->methods 		= array("xmipprecon", "emanrecon", "frealignrecon", "relionrecon");
		$this->prepTypes 	= array("preprefinexmipp", "preprefineeman", "preprefinefrealign", "preprefinerelion");
		$this->refineTypes 	= array("xmipprecon", "emanrecon", "frealignrecon", "relionrecon");
		$this->uploadTypes 	= array("uploadrecon");
	}
	public function getUploadRefineDone()
	{
		$reconRuns = $this->particle->getSingleModelReconIdsFromSession( $this->expId );
		return $reconRuns;
	}		
}

?>