<?php

require_once "refineJobs.inc";


class RefineJobsSingleModel extends RefineJobs
{
	public function setDBValues()
	{
		$this->methods 		= array("xmipprecon", "emanrecon", "eman2recon", "frealignrecon", "relionrecon");
		$this->prepTypes 	= array("preprefinexmipp", "preprefineeman", "preprefineeman2", "preprefinefrealign", "preprefinerelion");
		$this->refineTypes 	= array("xmipprecon", "emanrecon", "eman2recon", "frealignrecon", "relionrecon");
		$this->uploadTypes 	= array("uploadrecon");
	}
	public function getUploadRefineDone()
	{
		$reconRuns = $this->particle->getSingleModelReconIdsFromSession( $this->expId );
		return $reconRuns;
	}		
}

?>
