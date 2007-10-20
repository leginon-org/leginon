<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

$filename=$_GET['file'];
$expId =$_GET['expId'];
$norefId=$_GET['norefId'];
$norefClassId=$_GET['norefClassId'];
$stackId=$_GET['stackId'];

$updateheader=($_GET['uh']==1) ? 1 : 0;

function getimagicfilenames($file) {
	$file = substr($file, 0, -3);
	$file_hed = $file."hed";
	$file_img = $file."img";
	return array($file_hed, $file_img);
	
}

list($file_hed, $file_img)=getimagicfilenames($filename);

$info=imagicinfo($file_hed);
$n_images=$info['count']+1;


?>
<html>
<head>
<style>
	input, select {
		border: 1px solid #AABDCC;
	}
	img.imgtile {
		border: 1px solid #000000;
	}

	div.scrollpane {
		height: 600px;
		overflow: auto;
		border: 1px solid #666;
		background-color: #ccc;
		padding: 8px;
	}
</style>
<script src="../js/prototype.js"></script>
<script>

var file_hed="<?=$file_hed?>"
var file_img="<?=$file_img?>"
var n_images="<?=$n_images?>"
var updateheader="<?=$updateheader?>"
var expId="<?=$expId?>"
var filename="<?=$filename?>"
var norefId="<?=$norefId?>"
var norefClassId="<?=$norefClassId?>"
var stackId="<?=$stackId?>"

function displaystack(startImg, endImg, force) {
	var wholemap = $('wholemap')
	var i=0
	for(i = startImg; i <= endImg; i++) {
		 var tileId = addTile(wholemap, i, force)
	}
}

function addTile(wholemap, i, force) {
	binning = $('binning').value
	t = $('quality').value
	var tileId = "img"+i
	var filename = 'getstackimg.php?'
				+'hed='+file_hed
				+'&img='+file_img
				+'&n='+i
				+'&t='+t
				+'&b='+binning
				+'&uh='+updateheader

   var img = $(tileId)
   if(!img || force){
      img = document.createElement("img")
      img.src = filename
      img.setAttribute("id", tileId)
      img.setAttribute("class", "imgtile")
      wholemap.appendChild(img)
   }

	return tileId
}

function load() {
	clean()
	startImg=parseInt($('startimg').value)
	endImg=parseInt($('endimg').value)
	if (endImg > n_images-1) {
	  endImg=n_images-1
	}
	force=1
	displaystack(startImg, endImg, force) 
}

function clean() {
	var wholemap = $('wholemap')
  var allTiles = wholemap.getElementsByTagName('img')
	for(i = 0; i < allTiles.length; i++) {
		var id = allTiles[i].getAttribute('id')
		wholemap.removeChild(allTiles[i])
		i-- 
	}
}

function setImage() {
	window.document.myf.submit(); 
}

function upload() {
	var templateId=$('templateId').value
	if (templateId!=""&& templateId <= n_images-1 && templateId >=0 ) { 
		if (stackId!="") {
			window.open("uploadtemplate.php?expId="+expId+"&templateId="+templateId+"&stackId="+stackId+"&file="+filename+"","width=400,height=200")
		}
		if (norefId!="") {
			window.open("uploadtemplate.php?expId="+expId+"&templateId="+templateId+"&norefId="+norefId+"&norefClassId="+norefClassId+"&file="+filename+"","width=400,height=200") 
		}
	}
}
	
</script>
</head>
<body onload='load()'>
<?
echo "stack: $file_hed";
echo "<br \>";
echo "#images: $n_images";
echo "<br \>";
$defendimg = ($_GET['endimg']) ? $_GET['endimg'] : (($n_images > 20) ? 20 : $n_images-1);
$lastimg=($_POST['endimg']) ? $_POST['endimg'] : $defendimg;
?>

from: <input id="startimg" type="text" alt="Start" value="0" size="10">
to: <input id="endimg" type="text" alt="End" value="<?=$lastimg?>" size="10">
binning: <select id="binning">
		<option value="1">1</option>
		<option value="2">2</option>
		<option value="4">4</option>
		<option value="8">8</option>
	</select>
quality: <select id="quality">
		<option value="80">jpeg 80</option>
		<option value="90">jpeg 90</option>
		<option value="png">png</option>
	</select>
<input id="loadbutton" type="button" alt="Load" value="Load" onclick="load();"> <br />

Upload as Template:<input id="templateId" type="text" alt="Start" value="" size="5">
<input id="uploadbutton" type="button" alt="upload" value="upload" onclick="upload();">

<br />
<br />
<div class="scrollpane">
   <div id="wholemap">
   </div>
</div>
</body>
</html>
