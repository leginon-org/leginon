<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see	http://ami.scripps.edu/software/leginon-license
 *
 *	List of the reference-based alignment runs
 */

require ('inc/leginon.inc');
require ('inc/particledata.inc');
require ('inc/project.inc');
require ('inc/viewer.inc');
require ('inc/processing.inc');
	
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
	$s = $particle->getStackParams($p['REF|ApStackData|stack']);
	$t = $particle->getTemplatesFromId($refaliId['REF|ApTemplateImageData|refTemplate']);
	if ($p['csym']>1) $csym=$p['csym'];

	echo divtitle("Iteration 0");
	echo "<TABLE BORDER='0'>\n";
	echo "<IMG WIDTH='200' SRC='loadimg.php?filename=$p[path]/$p[name]/reference.mrc'><BR>\n";
	echo"</TABLE>\n";
	echo"<P>\n";

	foreach ($iters as $i) {
		echo divtitle("Iteration $i[iteration]");
		echo "<TABLE BORDER='0'>\n";
		if ($csym) {
			echo "<A HREF='loadimg.php?filename=$p[path]/$r[name]/$i[name]/refali001_nosym.mrc'>\n";
			echo "<IMG WIDTH='200' SRC='loadimg.php?filename=$p[path]/$r[name]/$i[name]/refali001_nosym.mrc'></A>\n";
			echo "<A HREF='loadimg.php?filename=$p[path]/$r[name]/$i[name]/varali001_nosym.mrc'>\n";
			echo "<IMG WIDTH='200' SRC='loadimg.php?filename=$p[path]/$r[name]/$i[name]/varali001_nosym.mrc'></A><BR>\n";
			echo "with $csym-fold symmetry:<BR>\n";
		}
		echo "<A HREF='loadimg.php?filename=$p[path]/$r[name]/$i[name]/refali001.mrc'>\n";
		echo "<IMG WIDTH='200' SRC='loadimg.php?filename=$p[path]/$r[name]/$i[name]/refali001.mrc'></A>\n";
		echo "<A HREF='loadimg.php?filename=$p[path]/$r[name]/$i[name]/varali001.mrc'>\n";
		echo "<IMG WIDTH='200' SRC='loadimg.php?filename=$p[path]/$r[name]/$i[name]/varali001.mrc'></A><BR>\n";
		echo"</TABLE>\n";
		echo"<P>\n";

	}
}
writeBottom();
?>
