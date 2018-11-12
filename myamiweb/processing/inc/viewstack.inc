<?php

/**
 *	The Leginon software is Copyright 2006
 *	Apache License, Version 2.0
 *	For terms of the license agreement see
 *	@licence http://leginon.org
 */
/**
 *
 */

function stackViewer($file_hed,$file_img,$n_images,$stackoptions=array()) {
	$optionkeys = array ('updateheader', 'plist', 'stackinfoindex', 'pixelsize');
	$plist=false;
	$updateheader=false;
	$pixelsize=0;
	$stackinfoindex=0;
	foreach ((array)$stackoptions as $k=>$v) {
		if (in_array($k, $optionkeys)) {
			$$k = $v;
		}
	}
	$javascript = "
	<style type='text/css'>
	input, select {
		border: 1px solid #AABDCC;
	}
	img.imgtile {
		border: 1px solid #000000;
	}

	div.stackpane {
		overflow: auto;
		border: 1px solid #666;
		background-color: #ccc;
		padding: 8px;
	}
	</style>
	<script src=\"../js/prototype.js\"></script>
	<script>

	var file_hed=\"$file_hed\"
	var file_img=\"$file_img\"
	var n_images=\"$n_images\"
	var updateheader=\"$updateheader\"
	var pixelsize=\"$pixelsize\"
	var stackinfoindex=\"$stackinfoindex\"
	var excludeimages=Array()
	var selectimages=Array()
	var n_tiles=0
	var lastselectedimage\n";
	if (is_array($plist)) {
		$javascript.="imgArray = new Array()\n";
		foreach ($plist as $p) {
			$javascript.="imgArray.push(\"$p[p]\");";
		}
		$javascript.="
		function displaystack(imgArray, startImg, endImg, force) {
			var wholemap = $('wholemap')
			var i=0
			for(i = startImg; i <= endImg; i++) {
				var tileId = addTile(wholemap, imgArray[i], force)
			}
			n_tiles=i
		}\n";
	}

	else {
		$javascript.="
		function displaystack(startImg, endImg, force) {
			var wholemap = $('wholemap')
			var i=0
			for(i = startImg; i <= endImg; i++) {
				var tileId = addTile(wholemap, i, force)
			}
			n_tiles=i
		}\n";
	}

	$javascript.= "
	function addTile(wholemap, i, force) {
		binning = $('binning').value
		scalebar = ($('scalebar').checked) ? 1 : 0
		info = ($('info').checked) ? 1 : 0
		t = $('quality').value
		var tileId = \"img\"+i
		var filename = 'getstackimg.php?'
				+'hed='+file_hed
				+'&img='+file_img
				+'&n='+i
				+'&t='+t
				+'&b='+binning
				+'&uh='+updateheader
				+'&ps='+pixelsize
				+'&di='+info
				+'&sb='+scalebar

		if (typeof stackinfo == 'object' && stackinfo[i]) {
			filename +='&i='+stackinfo[i]
		}

		if (stackinfoindex) {
			filename +='&k='+stackinfoindex
		}

		var img = $(tileId)
		if(!img || force){
			img = document.createElement(\"img\")
			img.src = filename
			img.setAttribute(\"id\", tileId)
			img.setAttribute(\"class\", \"imgtile\")
			img.setAttribute(\"onclick\", \"setSelection(\"+i+\",'\"+tileId+\"')\")
		wholemap.appendChild(img)
	}

		return tileId
	}

	function setSelection(id, img) {
		var imgelement = document.getElementById(img)
		if (mode=='exclude') {
			c=excludeImage(id)
			if(c!=-1) { 
				imgelement.style.border='1px solid #f00'
				imgelement.style.opacity=0.5
			} else {
				imgelement.style.border=''
				imgelement.style.opacity=''
			}
			if (typeof addexcludefn== 'function') {
				addexcludefn()
			}
		}
		if (mode=='select') {
			c=selectImage(id)
			imgelement.style.border=(c!=-1) ? '1px solid #0f0' : ''
			if (typeof addselectfn== 'function') {
				addselectfn()
			}
		}
		if (o=$('excludedIndex')) {
			o.value=getExcludeImages()
		}
		if (o=$('selectedIndex')) {
			o.value=getSelectImages()
		}
	}

	function selectImage(id) {
		var cindex=selectimages.length
		for(var i=0; i<selectimages.length; i++) {
			if (selectimages[i]==id) {
				cindex=i
				id=-1
				break
			}
		}
		selectimages[cindex]=id
		return id
	}

	function select2exclude() {
		var selected=false
		for(var j=0; j<n_tiles; j++) {
			selected=false
			for(var i=0; i<selectimages.length; i++) {
				if (selectimages[i]==j) {
					selected=true
				}
			}
			excludeimages[j]=(selected) ? -1 : j
		}
	}

	function getSelectImages() {
		var a=Array();
		for(var i=0; i<selectimages.length; i++) {
			if (selectimages[i]!=-1) {
				a[a.length]=selectimages[i]
			}
		}
		if (a.length) {
			lastselectedimage=a[a.length-1]
		}
		return a.toString()
	}

	function getLastSelectedImage() {
		return lastselectedimage
	}

	function getExcludeImages() {
		var a=Array();
		for(var i=0; i<excludeimages.length; i++) {
			if (excludeimages[i]!=-1) {
				a[a.length]=excludeimages[i]
			}
		}
		return a.toString()
	}

	function excludeImage(id) {
		var cindex=excludeimages.length
		for(var i=0; i<excludeimages.length; i++) {
			if (excludeimages[i]==id) {
				cindex=i
				id=-1
				break
			}
		}
		excludeimages[cindex]=id
		return id
	}

	function load() {
		clean()
		startImg=parseInt($('startimg').value)
		endImg=parseInt($('endimg').value)
		if (endImg > n_images-1) {
			endImg=n_images-1
		}
		force=1
		displaystack(\n";
	if (is_array($plist)) $javascript.="imgArray, ";
	$javascript.="startImg, endImg, force)
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

	function resetSelection() {
		selectimages=Array()
		excludeimages=Array()
		for(var id=0; id<n_tiles; id++) {
			var img = $('img'+id)
			if(s=img.style) {
				s.border=''
				s.opacity=''
			}
		}
	}

	var mode='exclude'
	function setMode(){
		resetSelection()
		if (o=$('mode')) {
			if (mode=='select') {
				o.style.border='1px solid #F00'
				mode='exclude'
			} else {
				o.style.border='1px solid #0F0'
				mode='select'
			}
			o.value=mode
		}
	}

	</script>\n";
	return $javascript;
}

?>
	
