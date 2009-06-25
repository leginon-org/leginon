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
if (!$avgid = $_GET['avgId'])
	$avgid=false;
$expId = $_GET['expId'];

processing_header("Averaged Tomogram Report","Avergaged Tomogram Report Page", $javascript);
if (!$avgid) {
	processing_footer();
	exit;
}

// --- Get Reconstruction Data
$particle = new particledata();
$avginfo = $particle->getAveragedTomogramInfo($avgid);
// get pixel size
$html .= "<br>\n<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
$title = "tomogram average info";
$stackid = $avginfo[0]['stackid'];
$stackparams = $particle->getStackParams($stackid);
$stackname = $stackparams['shownstackname'];
$alignruninfo = $particle->getAlignStackParams($stackparams['alignstackid']);
$clusternums = $particle->getClusterRefNumsFromSubStack ($stackid,$stackparams['clusterstackid']);
$clusternums_array = array();
if ($clusternums && count($clusternums)) 
	foreach ($clusternums as $c) $clusternums_array[] = $c['classnum'];

$avgruninfo = array(
	'id'=>$avginfo[0]['avgid'],
	'name'=>$avginfo[0]['runname'],
	'description'=>$avginfo[0]['description'],
	'path'=>$avginfo[0]['path'],
	'stackId'=>$avginfo[0]['stackid'],
	'stackname'=>$stackparams['shownstackname'],
	'stack alignment run id: name (package)'=>$stackparams['alignrunid'].": ".$alignruninfo['runname']." (".$alignruninfo['package'].")",
	'included cluster classes'=>implode(',',$clusternums_array),
	'subtomo run id'=>$avginfo[0]['subtomorunid'],
	'number of subvolumes averaged'=>count($avginfo),
);
echo "<table><tr><td colspan=2>\n";
$particle->displayParameters($title,$avgruninfo,array(),$expId);
echo "</td></tr>";
echo "<tr>";
echo "</td></tr>";
echo "<tr>";
// --- SnapShot --- //
$snapshotfile = $avgruninfo['path']."/snapshot.png";
if (file_exists($snapshotfile)) {
	echo "<td>";
	echo "<a href='loadimg.php?filename=$snapshotfile' target='snapshotfile'>"
		."<img src='loadimg.php?filename=$snapshotfile&s=180' height='180'><br/>\nSnap Shot</a>";
	echo "</td>";
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
$axes = array(0=>'a',1=>'b');
$projnames = array('a'=>'Top','b'=>'Side');
$tomogram = $avgruninfo;
foreach ($axes as $axis) {
	$flvfile = $tomogram['path']."/minitomo".$axes[0].".flv";
	if (file_exists($flvfile)) {
		echo "<table><tr><td>".$projnames[$axis]." Projection</td><td>Slicing Through</td></tr>";
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
					loop: false, 
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
echo "</tr></table>\n";
echo "</tr></table>\n";
$tomograms = array();
foreach ($avginfo as $info) {
	$tomoinfo = array();
	$tomoinfo['DEF_id'] = $info['subtomoid'];
	$tomograms[] = $tomoinfo;
}
if ($tomograms) {
	$html = "<h4>Included Subvolume tomograms</h4>";
	$html .= "<table class='tableborder' border='1' cellspacing='1' cellpadding='5'>\n";
	$html .= "<TR>\n";
	$display_keys = array ( 'tiltseries','full','particle alignment<br/>(xyshift) zshift<br/>rotation,mirror','volume<br/>xycenter,zoffset<br/>dimension','snapshot','z density<vr/>profile');
	foreach($display_keys as $key) {
		$html .= "<td><span class='datafield0'>".$key."</span> </TD> ";
	}
	foreach ($tomograms as $tomo) {
		$tomogramid = $tomo['DEF_id'];
		$tomogram = $particle->getTomogramInfo($tomogramid);
		$dzprint = ($tomogram['dz'])?$tomogram['dz']:'?';
		$dimprint = '('.$tomogram['dx'].','.$tomogram['dy'].','.$dzprint.')';
		if ($tomogram['prtlimage']) {
			$number = $tomogram['number'];
			$center0 = $particle->getTomoCenter($tomogram['centerx'],
					$tomogram['centery'],$tomogram['prtlimage'],$tomogram['tiltseries']);
			$center0['x'] = floor($center0['x']);
			$center0['y'] = floor($center0['y']);
			$offsetz = floor($tomogram['offsetz']);
		} else {
			if ($tomogram['full']) {
				$number = $tomogram['number'];
				$center0 = array('x'=>'?','y'=>'?');
				$offsetz = '?';
			} else {
				$number = '';
				$center0 = Null;
				$offsetz = 0;
			}
		}
		$centerprint = ($tomogram['full']) ? '('.$center0['x'].','.$center0['y'].')' : 'Full';
		$offsetprint = $offsetz;
		$tiltseriesnumber = $tomogram['tiltnumber'];
		$alignpinfo = $particle->getTomoAlignedParticleInfo($avgid,$tomogramid);
		if (!$alignpackage)
			$alignstackinfo = $particle->getAlignStackParams($alignpinfo['alignstack']);
			$alignpackage = $alignstackinfo['package'];
		$alignpshiftprint = "(".$alignpinfo['xshift'].",".$alignpinfo['yshift'].") ".sprintf('%5.1f',$alignpinfo['zshift']);
		$alignprmprint = $alignpinfo['rotation']." mirror=".$alignpinfo['mirror'];
		// PRINT INFO
		$html .= "<TR>\n";
		$html .= "<td>$alignpackage.$tiltseriesnumber</TD>\n";
		$html .= "<td>".$tomogram['full']."</TD>\n";
		$html .= "<td>".$alignpshiftprint."<br/>".$alignprmprint."</TD>\n";
		$html .= "<td><A HREF='tomoreport.php?expId=$expId&tomoId=$tomogramid'>$number<br/>$centerprint,$offsetprint<br/>$dimprint</A></TD>\n";
		$html .= "<td>";
    $snapfile = $tomogram['path'].'/snapshot.png';
		if (!file_exists($snapfile)) 
			$snapfile = $tomogram['path'].'/projectiona.jpg';
		$maxheight = 80;
		$maxwidth = 400;
		$imgsize = array(10,10);
		if (file_exists($snapfile)) 
			$imgsize = getimagesize($snapfile);
		if ($imgsize[1] < $maxheight) {
			$imglimit = "WIDTH='".min($imgsize[0],$maxwidth)."'";
		} else {
			$imglimit = "HEIGHT='".$maxheight."'";
		}
    $html .= "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'><img src='loadimg.php?filename=$snapfile' ".$imglimit." >\n";
		$html .= "</td>\n";
		$html .= "<td>";
		$zfile = sprintf('%s/profile_%05d.txt',$avgruninfo['path'],$tomogramid);
		$zshift = $alignpinfo['zshift'] * (($alignpinfo['mirror'])? -1:1);
    $html .= "<A HREF='tomozprofilegraph.php?file=$zfile&center=$zshift' target='snapshot'>
<img border='0' width='100' src='tomozprofilegraph.php?w=100&hg=0&file=$zfile&center=$zshift'></a>\n";
		$html .= "</td>\n";
		$html .= "</tr>\n";
	}
	$html .= "</table>\n";
	echo $html;
} else {
	echo "no subvolume tomograms available";
}


processing_footer();
?>
