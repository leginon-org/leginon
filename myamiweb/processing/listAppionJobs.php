<?php
require "inc/particledata.inc";
require "inc/util.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/processing.inc";

checkJobs();

function checkJobs($showjob=False,$showall=False,$extra=False) {
	$expId= $_GET['expId'];
	$jobtype = $_GET['jobtype'];
	$particle = new particledata();

	processing_header("Appion Jobs Currently Running","Appion Jobs Currently Running");

	$formAction=$_SERVER['PHP_SELF']."?expId=$expId&jobtype=$jobtype";

	$user = $_SESSION['username'];
	$pass = $_SESSION['password'];

	
	// get info for specified job types
	$jobinfo = $particle->getJobIdsFromSession($expId,$jobtype,'R');

	if ($jobinfo[0]) {
		foreach ($jobinfo as $job) {
			$jobid = $job['DEF_id'];
			$name = $job['name'];
			$display_keys['time']=$job['DEF_timestamp'];
			$running=time()-strtotime($job['DEF_timestamp']);
			$rundays = floor($running/60/60/24);
			$runhours = floor(($running-$rundays*60*60*24)/60/60);
			$runmins = floor(($running-$rundays*60*60*24-$runhours*60*60)/60);
			$display_keys['runtime'] =($rundays>0) ? "$rundays days, ":'';
			$display_keys['runtime'].=($runhours>0) ? "$runhours hours, ":'';
			$display_keys['runtime'].=($runmins>0) ? "$runmins mins":'';
			$display_keys['path']=$job['appath'];
			$display_keys['cluster']=$job['cluster'];
       			$display_keys['PBS ID'] = $job['clusterjobid'];	

			// based on the jobtype, add extra info:

			// if a particle picker, show # particles so
			// far and correlation values
			if ($jobtype=='dogpicker' || $jobtype=='templatepicker') {
				$pickerinfo = $particle->getSelectionRunIdFromPath($job['appath']);
				$pstats = $particle->getStats($pickerinfo[0]['DEF_id']);
				$numptl=$pstats['totparticles'];
				$numimg=$pstats['num'];
				$ppimg = ($numimg > 0) ? (sprintf("%.1f", $numptl/$numimg)) : 0;
				$extraKeys['imgs processed']=commafy($numimg);
				$extraKeys['particles so far']=commafy($numptl);
				$extraKeys['particles per img']=$ppimg;
				$perimg=$running/$numimg;
				$perimg_m=floor($perimg/60);
				$perimg_s=floor($perimg-$perimg_m*60);
				$extraKeys['time per img'] = ($perimg_m>0) ? "$perimg_m min, ":'';
				$extraKeys['time per img'].= ($perimg_s>0) ? "$perimg_s sec":'';
				$extraKeys['min']=format_sci_number($pstats['min'],4);
				$extraKeys['max']=format_sci_number($pstats['max'],4);
				$extraKeys['avg']=format_sci_number($pstats['avg'],4);
				$extraKeys['stddev']=format_sci_number($pstats['stddev'],4);

			}

			// if makestack, show num particles so far
			elseif ($jobtype=='makestack') {
				$stackinfo = $particle->getStackRunIdFromPath($job['appath']);
				$numptl = $particle->getNumStackParticles($stackinfo[0]['DEF_id']);
				$extraKeys['particles so far']=commafy($numptl);
			}

			// if ace, show stats:
			elseif ($jobtype=='ace') {
				$aceinfo = $particle->getAceRunIdFromPath($job['appath']);
				$fields = array('defocus1', 'confidence', 'confidence_d');
				$astats = $particle->getCTFStats($fields,$expId,$aceinfo[0]['DEF_id']);
				$dstats = $astats['defocus1'][0];
				$c1stats = $astats['confidence'][0];
				$c2stats = $astats['confidence_d'][0];
				$mind = format_sci_number($dstats['min']*1e6,4);
				$maxd = format_sci_number($dstats['max']*1e6,4);

				$extraKeys['imgs processed']=commafy($dstats['nb']);
				$extraKeys['defocus range']="$mind - $maxd &micro;m";
				$extraKeys['avg confidence1']=format_sci_number($c1stats['avg'],4);
				$extraKeys['avg confidence2']=format_sci_number($c2stats['avg'],4);
			}

			echo apdivtitle("Job: <a href='checkAppionJob.php?expId=$expId&jobId=$jobid'>$name</a> (ID: $jobid)\n");
			echo openRoundBorder();
			echo "<table border='0'>\n";
			foreach ($display_keys as $k=>$v) echo formatHtmlRow($k,$v);
			echo "</table>\n";
			echo closeRoundBorder();
			echo "<a href='checkAppionJob.php?expId=$expId&jobId=$jobid'>[check logfile]</a><br />\n";
			if ($extraKeys) {
				echo "<table border='0'>\n";
				foreach ($extraKeys as $k=>$v) echo formatHtmlRow($k,$v);
				echo "</table>\n";
			}
			echo "<p>\n";
		}
	}
	else echo "No $jobtype jobs running\n";
	processing_footer();
	exit;
}

?>
