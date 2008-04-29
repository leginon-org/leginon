<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see	http://ami.scripps.edu/software/leginon-license
 *
 *	List of the reference-based alignment runs
 */

require "inc/particledata.inc";
require "inc/processing.inc";
require "inc/viewer.inc";
require "inc/leginon.inc";
require "inc/project.inc";
	
// check if refinement run is specified
$refaliId = $_GET['refaliId'];
if ($refaliId) {
	displayIterations($refaliId);
}
else {
	echo "no reference-based alignment runid specified<BR>\n";
	exit;
}

function displayIterations($refaliId) {
	writeTop("Reference-Based Alignment Iteration Summary","Reference-Based Alignment Iteration Summary", $javascript);

	// --- Get Iterations Data
	$particle = new particledata();
	$iters = $particle->getRefAliIters($refaliId);

	// --- Get Refali Data
	$r = $particle->getRefInfoFromId($refaliId);
	$p = $particle->getRefAliParams($refaliId);
	$ts = $particle->getRefTemplatesFromId($refaliId);
//	$s = $particle->getStackParams($p['REF|ApStackData|stack']);
	//$t = $particle->getTemplatesFromId($refaliId['REF|ApTemplateImageData|refTemplate']);
	if ($p['csym']>1) $csym=$p['csym'];

	echo divtitle("Original templates");
	echo "<TABLE BORDER='0'><TR>\n";
	foreach ($ts as $t) {
		echo "<TD>\n";
		echo "<IMG WIDTH='200' SRC='loadimg.php?filename="
			.$t['path']."/".$t['templatename']."'><BR/>\n";
			//$p[path]/$p[name]/reference001.mrc'><BR>\n";
		echo "</TD>\n";
	}
	echo"</TR></TABLE>\n";
	echo"<P>\n";

	foreach ($iters as $i) {
		echo divtitle("Iteration $i[iteration]");
		echo "<TABLE CLASS='tableborder' BORDER='0'><TR>\n";
		$count = 0;
		foreach ($ts as $t) {
			$count ++;
			$numstr = (string) $count;
			echo "<TD>\n";
			if ($csym) {
				echo "<A HREF='loadimg.php?filename=$p[path]/$r[name]/$i[name]/refali00".$numstr."_nosym.mrc'>\n";
				echo "<IMG WIDTH='200' SRC='loadimg.php?filename=$p[path]/$r[name]/$i[name]/refali00".$numstr."_nosym.mrc'></A>\n";
				echo "with $csym-fold symmetry:<BR>\n";
			}
			echo "<A HREF='loadimg.php?filename=$p[path]/$r[name]/$i[name]/refali00".$numstr.".mrc'>\n";
			echo "<IMG WIDTH='200' SRC='loadimg.php?filename=$p[path]/$r[name]/$i[name]/refali00".$numstr.".mrc'></A>\n";
			echo "</TD>\n";
		}
		echo "</TR><TR>\n";
		$count = 0;
		foreach ($ts as $t) {
			$count ++;
			echo "<TD>\n";
			if ($csym) {
				echo "<A HREF='loadimg.php?filename=$p[path]/$r[name]/$i[name]/varali00".$numstr."_nosym.mrc'>\n";
				echo "<IMG WIDTH='200' SRC='loadimg.php?filename=$p[path]/$r[name]/$i[name]/varali00".$numstr."_nosym.mrc'></A><BR>\n";
				echo "with $csym-fold symmetry:<BR>\n";
			}
			echo "<A HREF='loadimg.php?filename=$p[path]/$r[name]/$i[name]/varali00".$numstr.".mrc'>\n";
			echo "<IMG WIDTH='200' SRC='loadimg.php?filename=$p[path]/$r[name]/$i[name]/varali00".$numstr.".mrc'></A><BR>\n";
			echo "</TD>\n";
		}
		echo"</TR></TABLE>\n";
		echo"<P>\n";
	}
}
writeBottom();
?>
