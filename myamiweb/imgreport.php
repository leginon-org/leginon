<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');
require ('inc/viewer.inc');

// display data tree ?
$displaytreevalue  = ($_POST) ? (($_POST[datatree]=='on') ? "off" : "on") : "off";
$displaytree = ($displaytreevalue == 'on') ? true : false;

if(!$imgId=$_GET[id]) {
	// --- if Id is not set, get the last acquired image from db
	$sessionId = $leginondata->getLastSessionId();
	$imgId = $leginondata->getLastFilenameId($sessionId);
}

$preset=$_GET[preset];

// --- find image
$newimage = $leginondata->findImage($imgId, $preset);
$imgId = $newimage[id];

$imageinfo = $leginondata->getImageInfo($imgId);
$sessionId = $imageinfo[sessionId];
$path = $leginondata->getImagePath($sessionId);
$filename = $leginondata->getFilenameFromId($imgId);
$filesize = getFileSize($path.$filename, 2 );
$fileinfo = imagemrcinfo($path.$filename);
$sessioninfo = $leginondata->getSessionInfo($sessionId);
$presets = $leginondata->getPresets($imgId);

$viewer = new viewer();
$viewer->setSessionId($sessionId);
$viewer->setImageId($imgId);
$javascript = $viewer->getJavascript();

$view1 = new view('<b>Thumbnail</b>', 'thumb');
$view1->displayCloseIcon(false);
$view1->displayInfoIcon(false);
$view1->displayFilterIcon(false);
$view1->displayFFTIcon(true);
$view1->displayScaleIcon(true);
$view1->displayTargetIcon(true);
$view1->displayAdjustLink(false);
$view1->displayPresets(false);
$view1->setFrameColor('#000000');
$view1->setMenuColor('#ccccff');
$view1->setSize(256);
$viewer->add($view1);

$javascript .= $viewer->getJavascriptInit();

if ($displaytree)
	$jstree = $leginondata->getDataTree('AcquisitionImageData',$imgId);

// --- get Calibrations Data
$types = $leginondata->getMatrixCalibrationTypes();

// --- getCTF Info, if any
$user = "usr_object";
$host = "cronus1";
$db = "processing";
$dbc = new mysql($host, $user, "", $db);
$ctfres = $dbc->SQLQuery('SHOW FIELDS FROM ctf');
while ($row = mysql_fetch_array($ctfres, MYSQL_ASSOC)) 
	$ctffields[$row['Field']] = $row;
$q = 'select `ctf`.*, i.* FROM `ctf` AS `ctf` '
	.' LEFT JOIN image as `i` on (`i`.imageId = `ctf`.imageId) '
	.' where i.`DEF_id` = "'.$imgId.'"';
$ctfdata = $dbc->getSQLResult($q);

$ctf_display_fields = array (
	'defocus1',
	'defocus2',
	'defocusinit',
	'amplitude_constrast',
	'angle_astigmatism',
	'noise1',
	'noise2',
	'noise3',
	'noise4',
	'envelope1',
	'envelope2',
	'envelope3',
	'envelope4',
	'lowercutoff',
	'uppercutoff',
	'snr',
	'confidence',
	'blobgraph1',
	'blobgraph2',
);

?>
<html>
<head>
<title>Image Report: <?=$filename?></title>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
<? if ($displaytree) { ?>
<link rel="StyleSheet" href="css/tree.css" type="text/css">
<script src="js/tree.js"></script>
<? } // --- end if displaytree ?>
<?=$javascript;?>
<script>
function init() {
	this.focus();
}
<?
if ($displaytree)
	echo $jstree;
?>
</script>
</head>
<body onload="init(); initviewer();">
<form name="tf" method="POST" action="<?=$REQUEST_URI?>">
<input type="hidden" name="datatree" value="<?=$displaytreevalue?>">
</form>
<?
//--- define information to display
$fileinfokeys = array (	'nx','ny',
	//	'nz',
		'mode',
	//	'nxstart',
	//	'nystart',
	//	'nzstart',
	//	'mx','my',
	//	'mz',
	//	'x_length',
	//	'y_length',
	//	'z_length',
		'alpha',
		'beta',
		'gamma',
	//	'mapc','mapr','maps',
		'amin','amax','amean',
	//	'ispg','nsymbt','extra[MRC_USER]',
		'xorigin','yorigin',
	//	'nlabl'
	);

$imageinfokeys = array (	
		'imageId',
	//	'filename',
		'preset',
		'dimx','dimy',
		'binning',
	//	'pixelsize',
	//	'magnification',
	//	'defocus',
		'high tension',
		'gridNb',
		'trayId',
		'exposure time'
		);

$parentimageinfokeys = array (	
		'parentId',
		'parentimage',
		'parentpreset',
		'parenttype',
		'parentnumber',
		'targetx',
		'targety',
		'targetdim',
		'targetdiam'
		);

$mrcmode = array (
		0=>'MRC_MODE_BYTE',
		1=>'MRC_MODE_SHORT',
		2=>'MRC_MODE_FLOAT',
		3=>'MRC_MODE_UNSIGNED_SHORT',
		// 3=>'MRC_MODE_SHORT_COMPLEX',
		4=>'MRC_MODE_FLOAT_COMPLEX'
		);
?>
<table border=0>
<tr valign=top>
	<td colspan="2">
<?
echo divtitle("General");
echo "<table border='0'>";
echo formatHtmlRow('Filename', $filename);
echo formatHtmlRow('Size', $filesize);
echo formatHtmlRow('Acquired', $imageinfo[timestamp]);
echo formatHtmlRow('Path', $path);
echo formatHtmlRow('Session', "$sessioninfo[Name] - $sessioninfo[Purpose]");
echo formatHtmlRow('Instrument', $sessioninfo[Instrument].' - '.$sessioninfo['Instrument description']);
echo "</table>";
?>
	</td>
</tr>
<tr valign=top>
	<td>
<?
if (is_array($imageinfo)) {
	echo divtitle("Image Information");
	echo "<table border='0'>";
	foreach($imageinfokeys as $k)
		if (!empty($imageinfo[$k])) {
			$v = $imageinfo[$k];
			if ($k=='high tension')
				$v = $leginondata->formatHighTension($v);
			echo formatHtmlRow($k,$v);
		}

	foreach($presets as $k=>$v) {
		if ($k=='defocus')
			echo formatHtmlRow($k, $leginondata->formatDefocus($v));
		else if ($k=='pixelsize') {
			$v *= $imageinfo['binning'];
			echo formatHtmlRow($k, $leginondata->formatPixelsize($v));
		}
		else if ($k=='dose') {
			if (!empty($v))
				echo formatHtmlRow($k, $leginondata->formatDose($v));
		}
		else
			echo formatHtmlRow($k, $v);
	}
	echo "</table>";
}
?>
	</td>
	<td>
<?
if (is_array($fileinfo)) {
	echo divtitle("Mrc Header Information");
	echo "<table border='0'>";
	foreach($fileinfokeys as $k) {
		$v = ($k=="mode") ? $mrcmode[$fileinfo[$k]] : $fileinfo[$k];
		echo formatHtmlRow($k, $v);
	}
	echo "</table>";
}
?>
	</td>
</tr>
<tr valign=top>
	<td>

<?
if (is_array($imageinfo) && $id=$imageinfo[parentId]) {
	$parentlinks = array ('parentId', 'parentimage');
	echo divtitle("Parent Image Information");
	echo "<table border='0'>";
	foreach($parentimageinfokeys as $k) {
		if (in_array($k, $parentlinks))
			$v = '<a class="header" href="'
			.$_SERVER['PHP_SELF'].'?id='.$id.'&preset='.$imageinfo[parentpreset].'">'
			.$imageinfo[$k].'</a>';
		else
			$v = $imageinfo[$k];
		echo formatHtmlRow($k, $v);
	}
	echo "</table>";
}
?>
	</td>
	<td>
<?
echo divtitle("Image Relations");
$datatypes = $leginondata->getDatatypes($sessionId);
echo "<table border='0'>";
if (is_array($datatypes))
	foreach ($datatypes as $datatype) {
		if ($imageinfo[preset]==$datatype)
			continue;
		$rel = $leginondata->findImage($imgId, $datatype);
		if ($rel) {
			$relId = $rel[id];
			$relfilename = $leginondata->getFilenameFromId($relId);
			echo formatHtmlRow($rel[preset], '<a class="header" href="'
                                .$_SERVER['PHP_SELF'].'?id='.$relId.'&preset='.$rel[preset].'">'
                                .$relfilename.'</a>');
		} else break;
	}
	echo formatHtmlRow('last', '<a class="header" href="javascript:history.back()">&laquo; back</a>');
echo "</table>";
?>
	</td>
</tr>
</table>
<table border="0">
<tr valign=top>
<td width=300>
<div style="border: 1px solid #000000; height:290; width:270; margin: 0px;padding:0px;  background-color: #CCCCFF">
<?$viewer->display();?>
</div>
</td>
<td>
<div style="border: 1px solid #000000; height:290; width:270; margin: 0px;padding:0px;  background-color: #CCCCFF">
<table align="center" >
<tr>
<td>
<img src="imagehistogram.php?tf=1&rp=1&id=<?=$imgId?>">
</td>
</tr>
</table>
</div>
</td>
<td>
<?
$link = ($displaytree) ? "hide" : "view";
$url = "<a href='#' class='header' onclick='javascript:document.tf.submit()'>".$link." &raquo;</a>"; 
echo divtitle("Data Tree ".$url);

if ($displaytree) {
?>
<br>
<div id="tree" style="position:absolute">
<script>
<!--
createTree(Tree,0, new Array());
//-->
</script>
</div>
<? } // --- end if displaytree ?>
</td>
</tr>
<tr valign=top>
	<td colspan="2">
<?
echo divtitle("CTF");

if (!empty($ctfdata)) {
	echo "<table border='0'>";
	foreach($ctfdata as $r) {
	$f++;
	$blobs = array();
	foreach($r as $k=>$v) {
		if (!in_array($k, $ctf_display_fields))
			continue;	
		$type = $ctffields[$k]['Type'];
		if (eregi('defocus', $k))
			$display = format_micro_number($v);
		else if (eregi("blob", $type)) {
			$blobs[] = "<a href=blob2img.php?id=".$r['ctfId']."&f=".$k.">"
				."<img border=0 src=blob2img.php?w=280&id=".$r['ctfId']."&f=".$k.">"
				."</a>";
			$k="";
			continue;
		}
		else if ($v-floor($v)) 
			$display = format_sci_number($v,4,2);
		else
			$display = $v;
		echo formatHtmlRow($k,$display);
	}
		echo "<tr>";
	foreach ($blobs as $blob) {
		echo "<td>";
		echo $blob;
		echo "</td>";
	}
		echo "</tr>";
	echo "<tr><td colspan=2><hr></td></tr>";	
	}
	echo "</table>";
	
} else {
	echo "No CTF data for this image";
}
echo divtitle("Calibrations");
?>
	</td>
</tr>
</table>
<?
foreach ($types as $type) {
	$t = $type['type'];
	$m = $leginondata->getImageMatrixCalibration($imgId, $t);
	if (!$m) continue;
	$matrix = displayMatrix(matrix(
			$leginondata->formatMatrixValue($m[a11]),
			$leginondata->formatMatrixValue($m[a12]),
			$leginondata->formatMatrixValue($m[a21]),
			$leginondata->formatMatrixValue($m[a22]))
		);
	echo "<span class='datafield0'>$t</span><br> $matrix";
}
?>
</body>
</html>
