<?php

require_once "inc/particledata.inc";


abstract class RefineJobs
{
	protected $particle;
	protected $expId;
	private $prepJobs;
	protected $runJobs; // make this visible to child classes
	private $uploadJobs;
	
	function __construct($expId) 
	{
		$this->expId = $expId;
		$this->particle = new particledata();
		$this->setDBValues();
		$this->setPrepJobs();
		$this->setRefineJobs();
		$this->setUploadJobs();
	}	
	
	// setDBValues must be defined by child classes and include a definition like:
	//	$this->methods 		= array("xmippml3d");
	//	$this->prepTypes 	= array("preprefinexmippml3d");
	//	$this->refineTypes 	= array("xmippml3drecon");
	//	$this->uploadTypes 	= array("uploadrecon");
	//
	abstract function setDBValues();
	
	private function setPrepJobs()
	{		
		$jobs = array(); // This is an array of jobtypes, each with an array of jobs
		foreach ( $this->prepTypes as $type ) {
			$jobs[] = $this->particle->getJobIdsFromSession($this->expId, $type);			
		}		
		
		// move all the jobs into a single dimentional array
		// so all we have is an array of jobs, not separated by jobtype
		$this->prepJobs = array();
		foreach ( $jobs as $jobtype ) {
			foreach ( $jobtype as $job ) {
				$this->prepJobs[] = $job;
			}
		}		
	}
	
	private function setRefineJobs()
	{
		$jobs = array();
		foreach ( $this->refineTypes as $type ) {
			$jobs[] = $this->particle->getJobIdsFromSession($this->expId, $type, $status=False, $ignore=True);			
		}		

		// move all the jobs into a single dimentional array
		// so all we have is an array of jobs, not separated by jobtype
		$this->runJobs = array();
		
		foreach ( $jobs as $jobtype ) {
			foreach ( $jobtype as $job ) {
				$this->runJobs[] = $job;
			}
		}	
		
		// Sort the job array by the timestamp (default)
		$this->sortJobs($this->runJobs);
		
	}
	
	# Sort a given array of Jobs by the given key
	private function sortJobs( &$jobArray, $key="'DEF_timestamp'" )
	{
		$compareFunction = create_function('$a, $b','if ($a['.$key.'] == $b['.$key.']) return 0; return ($a['.$key.'] > $b['.$key.']) ? -1 : 1;');
		usort( $jobArray, $compareFunction);
	}
		
	public function getRefineJobs()
	{
		return $this->runJobs;
	}
		
	private function setUploadJobs()
	{
		$jobs = array();
		foreach ( $this->uploadTypes as $type ) {
			$jobs[] = $this->particle->getJobIdsFromSession($this->expId, $type);			
		}		

		// move all the jobs into a single dimentional array
		// so all we have is an array of jobs, not separated by jobtype
		$this->uploadJobs = array();
		foreach ( $jobs as $jobtype ) {
			foreach ( $jobtype as $job ) {
				$this->uploadJobs[] = $job;
			}
		}		
	}
	
	public function getPrepRefineJobTypes()
	{
		return $this->prepTypes;
	}

	public function getRefineJobTypes()
	{
		return $this->refineTypes;
	}
	
	public function getUploadJobTypes()
	{
		return $this->uploadTypes;
	}
	
	public function getRefinesReadyToRun()
	{ 
		// Get all preparred refines
		$prepRefineRuns = $this->particle->getPreparedRefineJobs(false, false, false);
		// echo $prepRefineRuns;
		// Get the number of prepared refines that have not yet been run
		$refinejobs = array();
		
		// if we did not get an array from the database, exit.
		if (!is_array($prepRefineRuns)) return $refinejobs; 
		
		
		foreach ($prepRefineRuns as $refinejob) {
			if ( !in_array( $refinejob['method'], $this->methods ) ) continue;
			//echo $refinejob['method']." -- test <br/>\n";
			$refinerun = $this->particle->getClusterJobByTypeAndPath($refinejob['method'], $refinejob['path']);
			if (!$refinerun) {
				//echo $refinejob['method']." -- PASS <br/>\n";
				$refinejobs[] = $refinejob;
			}
		}
		//echo "<br/>RETURN<br/>";
		//print_r($refinejobs);
		return $refinejobs;
	}
	
	public function countRefinesReadyToRun()
	{ 
		$refinejobs = $this->getRefinesReadyToRun();

		$prepRefineDone = ($refinejobs) ? count($refinejobs) : 0;
		return 	$prepRefineDone;
	}
	
	public function getRefinesReadyToUpload()
	{ 
		// Find refines ready to upload
		$refineReadyUpload = array();
		foreach ($this->runJobs as $job ) {
			$jobid = $job['DEF_id'];
			
			// check if job has been uploaded
			if ($this->particle->getReconIdFromAppionJobId($jobid)) {
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
	
	 
	public function countRefinesReadyToUpload()
	{ 
		$refinejobs = $this->getRefinesReadyToUpload();

		$refineDone = ($refinejobs) ? count($refinejobs) : 0;
		return 	$refineDone;
	}
	
	public function countJobStatus( $jobs, $status )
	{
		$statusCount = 0; //total number of prep refines with provided status
		
		foreach ( $jobs as $job ) {
			if ( $job['status'] == $status ) {
				$statusCount++;
			}
		}
		
		return $statusCount;
	}
	
	public function countPrepRefineQueue()
	{
		return $this->countJobStatus($this->prepJobs, "Q");
	}
	public function countPrepRefineRun()
	{
		return $this->countJobStatus($this->prepJobs, "R");
	}
	public function countRunRefineQueue()
	{
		return $this->countJobStatus($this->runJobs, "Q");
	}
	public function countRunRefineRun()
	{
		return $this->countJobStatus($this->runJobs, "R");
	}
	public function countUploadRefineQueue()
	{
		return $this->countJobStatus($this->uploadJobs, "Q");
	}
	public function countUploadRefineRun()
	{
		return $this->countJobStatus($this->uploadJobs, "R");
	}
	
	public function getUploadRefineDone()
	{
		$reconRuns = $this->particle->getReconIdsFromSession( $this->expId );
		return $reconRuns;
	}
	
	public function countUploadRefineDone()
	{
		$reconRuns = $this->getUploadRefineDone();
		$refinesComplete = ($reconRuns) ? count($reconRuns): 0;
		
		return $refinesComplete;
	}
	
	public function getUnfinishedRefineJobs($showall=false)
	{		
		$jobs = array();
		foreach ($this->runJobs as $job) {
			$jobid = $job['DEF_id'];
	
			// check if job has been uploaded
			if ($this->particle->getReconIdFromAppionJobId($jobid)) {
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
