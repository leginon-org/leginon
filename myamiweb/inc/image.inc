<?
require_once('inc/filter.inc');
require_once('inc/graphutil.inc');
require_once('inc/scalebar.inc');

function getImage($sessionId, $imageId, $preset, $params = array()) {

	$p = array (
		'size'=> '',
		'minpix' => 0,
		'maxpix' => 255,
		'filter' => 'default',
		'binning' => 'auto',
		'scalebar' => true,
		'displaytargets' => true,
		'loadtime' => false
	);
	if (is_array($params))
		foreach ($params as $k=>$v)
			$p[$k] = $v;

	$size = $p[size];
	$binning = $p[binning];

	$leginondata = new leginondata();
	// --- get image path
	$path = $leginondata->getImagePath($sessionId);

	// --- find image
	$newimage = $leginondata->findImage($imageId, $preset);
	$imageId = $newimage[id];
	$parent = $leginondata->getImageInfo($newimage[childid]);

	// --- get filename
	if ($fft) {
		$p[displaytargets]=false;
		$p[scalebar]=false;
		$fft = $leginondata->getImageFFT($imageId);
		$filename = $fft[fftimage];
	} else if ($preset=='atlas') {
		$p[displaytargets]=false;
		$p[scalebar]=false;
		$filename = $leginondata->getImageAtlas($sessionId);
	} else {
		$filename = $leginondata->getFilename($imageId);
	}

	$pic = $path.$filename;
	if (is_file($pic)) {
		$imginfo = $leginondata->getImageInfo($imageId);
		$dimx = $imginfo[dimx];

		if ($p[loadtime])
			$begin=getmicrotime();

		if (READ_MRC == "mrcmod") {
			if ($binning=='auto')
				$binning = ($dimx > 1024) ? (($dimx > 2048) ? 4 : 2 ) : 1;
			$filterdata = new filter($pic, $p[minpix], $p[maxpix], $binning);
			$img = $filterdata->getFilter($p[filter]);
			if ($size) {
				$scalefactor = (imagesx($img)) ? $size/imagesx($img) : 1;
				imagescale($img, $scalefactor);
			}
		} else {
			require_once('inc/mrc.inc');
			$mrc = new mrc;
			$img = $mrc->imagecreatefromMRC($pic, $size, $size, $p[minpix], $p[maxpix], $p[quality]);
		}
		if ($p[loadtime])
			$end=getmicrotime();

		$white = imagecolorallocate($img, 255, 255, 255);
		$blue = imagecolorallocate($img, 0, 255, 255);
		$yellow= imagecolorallocate($img, 255, 255, 0);
		if ($p[displaytargets]) {
		    $targets = $leginondata->getImageTargets($imageId);
		    $targets = $leginondata->matchVersionTargets($targets);
		    foreach ($targets as $target) {
			$tId=$target[childId];
			$targetinfo = $leginondata->getImageInfo($tId);
			$targetcal = $leginondata->getImageMatrixCalibration($tId);
			$parentcal = $leginondata->getImageMatrixCalibration($imageId);
			$truediam=$targetinfo[targetdiam];
			$truedim=$targetinfo[targetdim];
			if (abs($target[x]-$parent[targetx])<5
				&& abs($target[y]-$parent[targety])<5 ){
				$col = $blue;
				$crosscol = $yellow;
			} else {
				$col = $white;
				$crosscol = $white;
			}
			$tn = $target[tnumber];
			$ratioX = ($size) ? $size/$target[dimx] : (($binning) ? 1/$binning : 1);
			$ratioY = ($size) ? $size/$target[dimy] : (($binning) ? 1/$binning : 1);
			$cx = $target[x]*$ratioX;
			$cy = $target[y]*$ratioY;

			if ($tId) {
				$angle = $targetcal['angle']-$parentcal['angle'];
				$squarepoints = getsquarepoints($cx, $cy, $angle, $truedim*$ratioX);
				drawsquare($img, $squarepoints, $col);
				$ctx = $squarepoints[0]+1;
				$cty = $squarepoints[1]+1;
			} else {
				$crosssize=20;
				$ctx = $cx+$crosssize/2;
				$cty = $cy;
				drawcross($img, $cx, $cy, $crosssize*$ratioX, $crosscol);
			}
			imagestringshadow($img, 4, $ctx, $cty, $tn, $col);
			
		    }
		    $targets = $leginondata->getImageFocusTargets($id);
		    foreach ($targets as $target) {
			$tgn=$target[tnumber];
			$tn='focus'."  ".$tgn;
			if (abs($target[x]-$parent[targetx])<5
				&& abs($target[y]-$parent[targety])<5 ){
				$col = $blue;
				$crosscol = $yellow;
			} else {
				$col = $white;
				$crosscol = $white;
			}
			$ratioX = ($size) ? $size/$target[dimx] : (($binning) ? 1/$binning : 1);
			$ratioY = ($size) ? $size/$target[dimy] : (($binning) ? 1/$binning : 1);
			$cx = $target[x]*$ratioX;
			$cy = $target[y]*$ratioY;

			$crosssize=20;
			$ctx = $cx+$crosssize/2;
			$cty = $cy;
			drawcross($img, $cx, $cy, $crosssize*$ratioX, $crosscol);
			imagestringshadow($img, 4, $ctx, $cty, $tn, $col);
		    }
		}

		/* diplay loading time */
		if ($p[loadtime])
			imagestringshadow($img, 4, 10, 10, "load time: ".($end-$begin), $blue);

		/* display scale bar */
		if ($p[scalebar]) {
		    if ($imginfo) {
			$size = ($size) ? $size : (($binning) ? $imginfo[dimx]/$binning : $imginfo[dimx]);
			$ratio = $imginfo[dimx]/$size ;
			$value = $imginfo[pixelsize]*$imginfo[binning]*$ratio;
			$scalebar = new ScaleBar($img, $size, $value);
			$scalebar->display();
		    }
		}
		return $img;
	}

}

class Mosaic {

	var $gridIds = array();
	var $ratio  = 4;
	var $margin = 5;
	var $displayframe = true;
	var $displayscalebar = true;
	var $framecolor = 0x00FF00;
	var $params = array('scalebar'=>false);

	function Mosaic() {
		
	}

	function setGridIds($gridIds) {
		$this->gridIds = $gridIds;
	}

	function displayFrame($bool) {
		$this->displayframe = $bool;
	}

	function displayScalebar($bool) {
		$this->displayscalebar = $bool;
	}

	function setFrameColor($hexcol) {
		$this->framecolor = $hexcol;
	}

	function setRatio($ratio) {
		$this->ratio = $ratio;
	}
	
	function setMargin($margin) {
		$this->margin = $margin;
	}

	function setGridImageParams($params) {
		if (is_array($params))
			$this->params = $params;
	}

	function getMosaic() {
		$leginondata = new leginondata();
		$imageinfo = array();
		$drows = array();
		$dcols = array();
		$dst_x = 0;
		$dst_y = 0;
		$src_x = 0;
		$src_y = 0;
		$angle = 0;

		$ratio = ($this->ratio) ? $this->ratio : 1;
		$margin = $this->margin;

		foreach($this->gridIds as $k=>$gridId) {
			$imageinfo[$k] = $leginondata->getImageInfo($gridId);
			$drows[$k] = $imageinfo[$k]['delta row'];
			$dcols[$k] = $imageinfo[$k]['delta column'];
		}

		$min_row = min($drows) - $imageinfo[0][dimy]/2;
		$max_row = max($drows) + $imageinfo[0][dimy]/2;
		$min_col = min($dcols) - $imageinfo[0][dimx]/2;
		$max_col = max($dcols) + $imageinfo[0][dimx]/2;

		$img_w = 2*$margin + ($max_col - $min_col)/$ratio;
		$img_h = 2*$margin + ($max_row - $min_row)/$ratio;
		$img = imagecreatetruecolor($img_w, $img_h);
		$background = imagecolorallocate($img, 0, 0, 0);
		if ($this->displayframe)
			$mosaicframecol = imagecolorallocate($img,
						($this->framecolor >> 16) & 0xFF,
						($this->framecolor >> 8) & 0xFF,
						$this->framecolor & 0xFF
					);

		$sessionId = $imageinfo[0][sessionId];
		$squaresize = $imageinfo[0][dimx]/$ratio;
		$this->params['size'] = $squaresize;
		$preset = 'grid';

		foreach ($imageinfo as $k=>$r) {
			$cx = $margin + ($dcols[$k] - $min_col)/$ratio; 
			$cy = $margin + ($drows[$k] + $max_row)/$ratio;
			$squarepoints = getsquarepoints($cx, $cy, $angle, $squaresize);
			$dst_x = $squarepoints[0];
			$dst_y = $squarepoints[1];
			$gimg = getImage($sessionId, $r[imageId], $preset, $this->params);
			$src_w = imagesx($gimg);
			$src_h = imagesy($gimg);
			imagecopy($img, $gimg, $dst_x, $dst_y, $src_x, $src_y, $src_w, $src_h);
			imagedestroy($gimg);
			if ($this->displayframe) {
				drawsquare($img, $squarepoints, $mosaicframecol);
				imagestringshadow($img, 4, $dst_x+1, $dst_y, $k+1, $mosaicframecol);
			}
		}

		if ($this->displayscalebar) {
			$size = $squaresize;
			$value = $imageinfo[0][pixelsize]*$imageinfo[0][binning]*$ratio;
			$scalebar = new ScaleBar($img, $size, $value);
			$scalebar->display($img_h);
		}
		return $img;
	}
}
?>
