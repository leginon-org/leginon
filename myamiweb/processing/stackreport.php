<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Simple viewer to view a image using mrcmodule
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";

$expId = $_GET['expId'];
$sessionId= $_GET['Id'];
$stackId = $_GET['sId'];

processing_header('Particle Stack Report','Particle Stack Report');

$particle = new particledata();
	echo $stackId;
	$s=$particle->getStackParams($stackId);
	# get list of stack parameters from database
	$nump=commafy($particle->getNumStackParticles($stackId));
	# get pixel size of stack
	$mpix=($particle->getStackPixelSizeFromStackId($stackId));
	$apix=format_angstrom_number($mpix)."/pixel";
	$s['pixelsize']=$apix;
	$boxsize= $s[boxSize]/$s[bin];
	$s['boxsize']=$boxsize;

	echo apdivtitle("Stack: <FONT class='aptitle'>".$s['shownstackname']
		."</FONT> (ID: <FONT class='aptitle'>".$stackId."</FONT>)");

	echo "<table cellspacing='1' cellpadding='2'><tr><td><span class='datafield0'>Total particles for $runparams[stackRunName]: </span></td><td>$nump</td></tr></table>\n";

	$stackparts = $particle->getStackParticles($stackId);

	echo "<table border='0'><tr>\n";
	$stackavg = $s['path']."/average.mrc";
	if (file_exists($stackavg)) {
		echo "<td align='center'>\n";
		echo "<img src='loadimg.php?filename=$stackavg&s=150' height='150'><br/>\n";
		echo "<i>averaged stack image</i>\n";
		echo "</td>\n";
	}	
	if (!is_null($stackparts[0]['mean'])) {
		echo "<td align='center'>\n";
		echo "<a href='stack_mean_stdev.php?sId=$stackId&expId=$expId'>\n";
		echo "<img border='0' src='stack_mean_stdev.php?w=256&sId=$stackId'><br/>\n";
		echo "<i><a href='subStack.php?expId=$expId&sId=$stackId&mean=1'>Filter Stack by Mean & Stdev</a></i>\n";
		echo "</td>\n";
	}
	$montage = $s['path']."/montage$stackId.png";
	if (file_exists($montage)) {
		echo "<td align='center'>\n";
		echo "<a href='loadimg.php?filename=$montage'>";
		echo "<img border='0' src='loadimg.php?filename=$montage&s=150' height='150'></a><br/>\n";
		echo "<i>Mean & Stdev Montage</i>\n";
		echo "</td>\n";
	}
	echo"</tr></table>\n\n";

	$stackfile=$s['path']."/".$s['name'];
	echo "View Stack: <A TARGET='stackview' HREF='viewstack.php?stackId=$stackId&file=$stackfile'>$s[name]</A><br>\n";

//Report stack parameters
	$exclude_fields = array('DEF_id','DEF_timestamp','count','REF|ApPathData|path','boxSize','selectionstacks');
	for ($i=1;$i < $s[count]; $i++) $exclude_fields[]=$i;
	$title = "stack parameters";
	$particle->displayParameters($title,$s,$exclude_fields,$expId);

//Report parent (old) stack run parameters if a substack
	while ($s['REF|ApStackData|oldstack']) {
		$s0 = $s;
		$stackId = $s['REF|ApStackData|oldstack'];
		$s=$particle->getStackParams($stackId);
		#for ($i=1;$i < $s[count]; $i++) $exclude_fields[]=$i;
		$title = "parent stack parameters";
		$particle->displayParameters($title,$s,$exclude_fields,$expId);
	}
//Report individual stack run parameters if combined
//This need rework along with getStackParams to handle multiple layers----AC
	if ($s['count'] > 1) {
		for ($i=0; $i < $s[count]; $i++) {
			$selectionstackId = $s['selectionstacks'][$i];
			$sr=$particle->getStackParams($selectionstackId);
			#for ($i=1;$i < $sr[count]; $i++) $exclude_fields[]=$i;
			$title = "combining stack run parameters";
			$particle->displayParameters($title,$sr,$exclude_fields,$expId);
		}
	}
//Report stack run particle picking parameters
	echo "<table><tr><td>";
	for ($i=0; $i < $s[count]; $i++) {
		$selectionstackId = $s['selectionstacks'][$i];
		$selectionruninfo=$particle->getStackSelectionRun($selectionstackId);
		$a = array('stackId'=>$selectionstackId);
		$a = array_merge($a,$selectionruninfo);
		$a['particleSelection']=array('display'=>$selectionruninfo['name'], 'link'=>$selectionruninfo['selectionid']);
		$exclude_fields = array('DEF_id','DEF_timestamp','REF|ApPathData|path','name');
		$title = "particle selection";
		$particle->displayParameters($title,$a,$exclude_fields,$a['sessionId']);
		echo "</td><td>";
	}
	echo "</td><tr></table>";

processing_footer();
