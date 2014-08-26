<?php

require_once "refineJobs.inc";


class RefineJobsSingleModel extends RefineJobs
{
	public function setDBValues()
	{
		$this->methods 		= array("xmipprecon", "emanrecon", "eman2recon", "frealignrecon");
		$this->prepTypes 	= array("preprefinexmipp", "preprefineeman", "preprefineeman2", "preprefinefrealign");
		$this->refineTypes 	= array("xmipprecon", "emanrecon", "eman2recon", "frealignrecon");
		$this->uploadTypes 	= array("uploadrecon");
	}
	public function getUploadRefineDone()
	{
		$reconRuns = $this->particle->getSingleModelReconIdsFromSession( $this->expId );
		return $reconRuns;
	}		
}

?>
