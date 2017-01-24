<?php
/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 *	Display results for each iteration of a refinement
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";
require_once "inc/viewer.inc";
require_once "inc/processing.inc";
require_once "inc/summarytables.inc";

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
// alignrunid is obtained from aligner
$refinedata = $particle->getAlignerInfo($tomogram['aligner']);
$alignment = $particle->getTomoAlignmentInfo($refinedata[0]['alignrunid']);
$title = "tomogram processing info";
$tomograminfo = $tomogram;
$stripstr = array('L'=>'','['=>'',']'=>'');
$tomograminfo['excluded imageIds'] = strtr($tomograminfo['excluded imageIds'],$stripstr);
$tomograminfo['align method'] = $alignment['method'];
$tomograminfo['bad align'] = $alignment['badAlign'];
$tomograminfo['tomogram path'] = $tomogram['path'];
$tomograminfo['hidden'] = $tomogram['hidden'];
$tomograminfo['zprojection image'] = $tomogram['zproj_id'];
$excluded_keys = array('path','tilt number','zproj_id');
echo "<table><tr><td colspan=2>\n";
$particle->displayParameters($title,$tomograminfo,$excluded_keys,$expId,'',True);
echo "</form>";
echo "</td></tr>";
echo "<tr>";
echo "<td>";
echo "<h4> Full tomogram is too large to be manipulated through web browser. Please use off-line tools such as 3dmod </h4>";
echo "<h5> You will find the tomogram in mrc format as:<br> \n";
echo $tomogram['path'].'/'.$tomogram['tomofilename'].".rec </h5>";
echo "</td></tr>";
echo "<tr>";
// ---Zprojection --- //
if ($tomograminfo['zproj_id']) {
	echo "<td>";
	echo "Projection to xy plane:<br>";
	echo "
<img src=../getimg.php?preset=all&session=".$expId."&id=".$tomograminfo['zproj_id']."&s=400&t=80&tg=1&sb=1&flt=default&fftbin=b&binning=auto&autoscale=s;3&df=3&lj=1&g=1&opt=2'>
";
	echo "</td></tr>";
	echo "<tr>";
}

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
