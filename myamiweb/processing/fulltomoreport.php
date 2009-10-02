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

// check if reconstruction is specified
if (!$tomoId = $_GET['tomoId'])
	$tomoId=false;
$expId = $_GET['expId'];

$formAction=$_SERVER['PHP_SELF']."?expId=$expId&tomoId=$tomoId";
$javascript="<script src='../js/viewer.js'></script>\n";
$javascript.= editTextJava();


processing_header("Full Tomogram Report","Full Tomogram Report Page", $javascript);
if (!$tomoId) {
	processing_footer();
	exit;
}
// edit description form
echo "<form name='templateform' method='post' action='$formAction'>\n";
// --- Get Reconstruction Data
$particle = new particledata();
if ($_POST) {
	$particle->updateTableDescriptionAndHiding($_POST,'ApFullTomogramData',$tomoId);
}
$tomogram = $particle->getFullTomogramInfo($tomoId);
$alignment = $particle->getTomoAlignmentInfo($tomogram['alignment']);
// get pixel size
#$html .= "<br>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
$title = "tomogram processing info";
$tomogram['tomogram path'] = $tomogram['path'];
$alignment['align path'] = $alignment['path'];
$tomograminfo = array_merge($tomogram,$alignment);
$tomograminfo['hidden'] = $tomogram['hidden'];
$excluded_keys = array('alignment','path','tilt number');
echo "<table><tr><td colspan=2>\n";
$particle->displayParameters($title,$tomograminfo,$excluded_keys,$expId,'',True);
echo "</form>";
echo "</td></tr>";
echo "<tr>";
// --- SnapShot --- //
$snapshotfile = $tomogram['path']."/snapshot.png";
if (file_exists($snapshotfile)) {
	echo "<td>";
	echo "<a href='loadimg.php?filename=$snapshotfile' target='snapshotfile'>"
		."<img src='loadimg.php?filename=$snapshotfile&s=180' height='180'><br/>\nSnap Shot</a>";
	echo "</td>";
}
echo "<td>";
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
$axes = array(0=>'a',1=>'b');
foreach ($axes as $axis) {
	$flvfile = $tomogram['path']."/minitomo".$axes[0].".flv";
	if (file_exists($flvfile)) {
		echo "<table><tr><td>Projection</td><td>Slicing Through</td></tr>";
			$flvfile = $tomogram['path']."/minitomo".$axis.".flv";
			$projfile = $tomogram['path']."/projection".$axis.".jpg";
			if (file_exists($flvfile)) {
				if ($size=getflvsize($flvfile)) {
					list($flvwidth, $flvheight)=$size;
				}
				$maxcolwidth = 400;
				echo "<tr><td>";
				$imagesizes = getimagesize($projfile);
				$colwidth = ($maxcolwidth < $flvwidth) ? $maxcolwidth : $flvwidth;
				$rowheight = $colwidth * $flvheight / $flvwidth;
				echo "<img src='loadimg.php?filename=$projfile&width=".$colwidth."' width='".$colwidth."'>";
				echo "</td><td>";
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
		}
	}
	echo "</table>";
}
echo "</td>";
echo "</tr>";
echo "</table>";
echo $html;

processing_footer();
?>
