<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');

if(!$imgId=$_GET[id]) {
	// --- if Id is not set, get the last acquired image from db
	$sessionId = $leginondata->getLastSessionId();
	$imgId = $leginondata->getLastFilenameId($sessionId);
}

$preset=$_GET[preset];

// --- find image
$newimage = $leginondata->findImage($imgId, $preset);
$imgId = $newimage[id];

function formatHtmlRow($k, $v) {
	return '<tr><td><span class="datafield0">'
		.$k.':</span></td><td>'
		.$v.'</td></tr>'."\n";
}

$imageinfo = $leginondata->getImageInfo($imgId);
$sessionId = $imageinfo[sessionId];
$path = $leginondata->getImagePath($sessionId);
$filename = $leginondata->getFilename($imgId);
$filesize = getFileSize($path.$filename, 2 );
$fileinfo = imagemrcinfo($path.$filename);
$sessioninfo = $leginondata->getSessionInfo($sessionId);
$presets = $leginondata->getPresets($imgId);

?>
<html>
<head>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
<title>Image Report: <?=$filename?></title>
<script>
function init() {
	this.focus();
}
</script>
</head>
<body onload="init()">
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
		'gridNb',
		'trayId'
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
echo formatHtmlRow('Instrument', "$sessioninfo[Instrument] - $sessioninfo[Instrument description]");
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
		if (!empty($imageinfo[$k]))
			echo formatHtmlRow($k,$imageinfo[$k]);

	foreach($presets as $k=>$v) {
		if ($k=='defocus')
			echo formatHtmlRow($k, $leginondata->formatDefocus($v));
		else if ($k=='pixelsize')
			echo formatHtmlRow($k, $leginondata->formatPixelsize($v));
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
			.$PHP_SELF.'?id='.$id.'&preset='.$imageinfo[parentpreset].'">'
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
			$relfilename = $leginondata->getFilename($relId);
			echo formatHtmlRow($rel[preset], '<a class="header" href="'
                                .$PHP_SELF.'?id='.$relId.'&preset='.$rel[preset].'">'
                                .$relfilename.'</a>');
		} else break;
	}
	echo formatHtmlRow('last', '<a class="header" href="javascript:history.back()">&laquo; back</a>');
echo "</table>";
?>
	</td>
</tr>
</table>
</body>
</html>
