<?php

require_once "refineJobs.inc";

// This class is used to keep track of how many alignment jobs are queued, running, ready for upload and complete 
// Based on Refine Jobs, some of the stuff in Refine Jobs is not needed, so maybe another level of extraction would be good,
// but this is OK for now.


class AlignJobs extends RefineJobs
{
	public function setDBValues()
	{
//		$this->methods 		= array("maxlikealignment","runxmippcl2d","runxmipp3cl2d", "sparxisac");
//		$this->prepTypes 	= array(); // there are no prep steps in alignments so far
//		$this->refineTypes 	= array("maxlikealignment","runxmippcl2d","runxmipp3cl2d", "sparxisac");
//		$this->uploadTypes 	= array("uploadsparxisac");

		// Just do ISAC for now
		$this->methods 		= array("maxlikealignment","sparxisac");
		$this->prepTypes 	= array(); // there are no prep steps in alignments so far
		$this->refineTypes 	= array("maxlikealignment","sparxisac");
		$this->uploadTypes 	= array("uploadsparxisac");
	}
	
	// TODO: finish this up for align uploads
	public function getUploadRefineDone()
	{
		$reconRuns = $this->particle->getSingleModelReconIdsFromSession( $this->expId );
		return $reconRuns;
	}		
	
	// override this for ISAC Jobs
	public function getRefinesReadyToUpload()
	{ 
		// Find alignments ready to upload
		$refineReadyUpload = array();

		foreach ($this->runJobs as $job ) {
			$jobid = $job['DEF_id'];
			$pathid = $job['REF|ApPathData|path'];
			
			// check if job has been uploaded
			if ($this->particle->getAlignRunIdFromAppionPathId($jobid)) {
				//echo "recon $jobid";
				continue;
			}
	
			// check if job has been aborted
			if ($job['status'] == 'A') {
				//echo "abort $jobid";
				continue;
			}
			
			// check if job has been run
			if ( $job['status'] == 'D' ) {
				$refineReadyUpload[] = $job;
			}
		}	
		
		return $refineReadyUpload;
	}
	
	public function getUnfinishedRefineJobs($showall=false)
	{		
		$jobs = array();
		foreach ($this->runJobs as $job) {
			$jobid = $job['DEF_id'];
			$pathid = $job['REF|ApPathData|path'];
	
			// check if job has been uploaded
			if ($this->particle->getAlignRunIdFromAppionPathId($pathid)) {
				//echo "recon $jobid";
				continue;
			}
	
			// check if job has been aborted
			if ($showall != True && $job['status'] == 'A') {
				//echo "abort $jobid";
				continue;
			}
	
			$jobs[] = $job;
		}
		return $jobs;
	}
}

?>
