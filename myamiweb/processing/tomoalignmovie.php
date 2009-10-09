<?php
/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 *
 *	Display results for each iteration of a refinement
 */

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";
require "inc/viewer.inc";
require "inc/processing.inc";
require "inc/summarytables.inc";

define (PARTICLE_DB, $_SESSION['processingdb']);

$alignerid = ($_GET['aId']);

$particle = new particledata();
$refinedata = $particle->getProtomoAlignmentInfo($alignerid);
$cycle = $refinedata[0]['cycle'];
$javascript="<script src='../js/viewer.js'></script>\n";

processing_header("Tomogram Report","Tomogram Report Page", $javascript);
if (!$alignerid) {
	processing_footer();
	exit;
}

// --- Display Flash Movie from flv --- //
@require_once('getid3/getid3.php');
function getflvsize($filename) {
	if (!class_exists('getID3')) {
		return false;
	}
	$getID3 = new getID3;
	$i = $getID3->analyze($filename);
	$w = $i['meta']['onMetaData']['width'];
	$h = $i['meta']['onMetaData']['height'];
	return array($w, $h);
}

if (!defined('FLASHPLAYER_URL')) {
	echo "<p style='color: #FF0000'>FLASHPLAYER_URL is not defined in config.php</p>";
}
$swfstyle=FLASHPLAYER_URL . 'FlowPlayer.swf';
if (!is_null($cycle)) {
	$flvfile = $refinedata[0]['path']."/align/minialign".sprintf('%02d',$cycle).".flv";
} else {
	$flvfile = $refinedata[0]['path']."/minialign.flv";
}
if (file_exists($flvfile)) {
	echo "<table><tr><td>Alignment Stack:</td></tr>\n";
	echo "<tr><td>".$flvfile."</td></tr>\n";
	if ($size=getflvsize($flvfile)) {
		list($flvwidth, $flvheight)=$size;
	}
	$maxcolwidth = 400;
	echo "<tr><td>";
	$colwidth = $flvwidth;
	$rowheight = $colwidth * $flvheight / $flvwidth;
	echo '<object type="application/x-shockwave-flash" data="'
		.$swfstyle.'" width="'.$colwidth.'" height="'.$rowheight.'" >
	<param name="allowScriptAccess" value="sameDomain" />
	<param name="movie" value="'.$swfstyle.'" />
	<param name="quality" value="high" />
	<param name="scale" value="noScale" />
	<param name="wmode" value="transparent" />
	<param name="allowNetworking" value="all" />
	<param name="flashvars" value="config={ 
		autoPlay: true, 
		loop: true, 
		initialScale: \'orig\',
		videoFile: \'getflv.php?file='.$flvfile.'\',
		hideControls: true,
		showPlayList: false,
		showPlayListButtons: false,
		}" />
	</object>';
	echo "</td></tr>";	
	echo "</table>";
}
echo $html;

processing_footer();
?>
