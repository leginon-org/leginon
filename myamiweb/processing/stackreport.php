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
$stackid = $_GET['sId'];

processing_header('Particle Stack Report','Particle Stack Report');

$particle = new particledata();

	$s=$particle->getStackParams($stackid);
	# get list of stack parameters from database
	$nump=commafy($particle->getNumStackParticles($stackid));
	# get pixel size of stack
	$mpix=($particle->getStackPixelSizeFromStackId($stackid));
	$apix=format_angstrom_number($mpix)."/pixel";
	$s['pixelsize']=$apix;
	$boxsize= $s[boxSize]/$s[bin];
	$s['boxsize']=$boxsize;

	echo apdivtitle("Stack: <FONT class='aptitle'>".$s['shownstackname']
		."</FONT> (ID: <FONT class='aptitle'>".$stackid."</FONT>)");

	echo "<table cellspacing='1' cellpadding='2'><tr><td><span class='datafield0'>Total particles for $runparams[stackRunName]: </span></td><td>$nump</td></tr></table>\n";

	$stackparts = $particle->getStackParticles($stackid);

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
		echo "<a href='stack_mean_stdev.php?sId=$stackid&expId=$expId'>\n";
		echo "<img border='0' src='stack_mean_stdev.php?w=256&sId=$stackid'><br/>\n";
		echo "<i><a href='subStack.php?expId=$expId&sId=$stackid&mean=1'>Filter Stack by Mean & Stdev</a></i>\n";
		echo "</td>\n";
	}
	$montage = $s['path']."/montage$stackid.png";
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

//Report stack run parameters
	$exclude_fields = array('DEF_id','DEF_timestamp','count','REF|ApPathData|path');
	for ($i=1;$i < $s[count]; $i++) $exclude_fields[]=$i;
	$title = "stack parameters";
	$particle->displayParameters($title,$s,$exclude_fields,$expId);

//Report stack run parameters
	echo "<table><tr><td>";
	for ($i=0; $i < $s[count]; $i++) {
		$selectionruninfo=$particle->getStackSelectionRun($s[$i][stackId]);
		$s[$i]['particleSelection']=array('display'=>$selectionruninfo['name'], 'link'=>$selectionruninfo['selectionid']);
		$exclude_fields = array('DEF_id','DEF_timestamp','REF|ApPathData|path');
		$title = "run parameters";
		$particle->displayParameters($title,$s[$i],$exclude_fields,$expId);
		echo "</td><td>";
	}
	echo "</td><tr></table>";

processing_footer();
