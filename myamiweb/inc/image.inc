<?
/**
 *	@version $Revision: 1.7 $
 *	@version $Id: image.inc,v 1.7 2004-10-04 19:06:47 dfellman Exp $
 */
/**
 *	Tools to display images / mosaic
 *	
 */

require_once("config.php");
require_once("inc/util.inc");
require_once('inc/filter.inc');
require_once('inc/graphutil.inc');
require_once('inc/scalebar.inc');

function getImage($sessionId, $imageId, $preset, $params = array()) {

	$p = array (
		'size'=> '',
		'minpix' => 0,
		'maxpix' => 255,
		'filter' => 'default',
		'fft' => false,
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
	if ($p[fft]) {
		$p[displaytargets]=false;
		$p[scalebar]=false;
		$fft = $leginondata->getImageFFT($imageId);
		$filename = $fft[fftimage];
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
				drawsquare($img, $squarepoints, $crosscol);
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
		    $targets = $leginondata->getImageFocusTargets($imageId);
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
	} else {
		$img = blankimage();
	}
	return $img;

}

function blankimage() {
	$blkimg = imagecreate(256,256);
	imagecolorallocate($blkimg, 255, 255, 255);
	return $blkimg;
}

function createAltMessage($text, $fontsize=2, $margin=6) {
	$width = 2*$margin + strlen($text)*($fontsize+4);
	$height = 2*$margin + $fontsize+12; 
	$img = imagecreate($width, $height);
	imagecolorallocate($img, 255, 255, 200);
	$black = imagecolorallocate($img, 0, 0, 0);
	$textcolor = $black;
	imagerectangle($img, 0,0, $width-1, $height-1, $black);
	imagestring($img, $fontsize, $margin, $margin, $text, $textcolor);
	return ($img);
}

class Mosaic {

	var $imageIds = array();
	var $ratio  = 4;
	var $margin = 50;
	var $displayframe = true;
	var $displayscalebar = true;
	var $loadtime = false;
	var $framecolor = 0x00FF00;
	var $params = array('scalebar'=>false);

	function Mosaic() {
		
	}

	function setImageIds($imageIds) {
		$this->imageIds = $imageIds;
	}

	function setCurrentImageId($cId) {
		$this->cId = $cId;
	}

	function displayFrame($bool) {
		$this->displayframe = $bool;
	}

	function displayScalebar($bool) {
		$this->displayscalebar = $bool;
	}

	function displayLoadtime($bool) {
		$this->loadtime = $bool;
	}

	function setFrameColor($r, $g, $b) {
		$this->framecolor = (($r << 16) + ($g << 8) + $b);
	}

	function setRatio($ratio) {
		$this->ratio = $ratio;
	}
	
	function setSize($size) {
		$this->size = $size;
	}
	
	function setMargin($margin) {
		$this->margin = $margin;
	}

	function setImageParams($params) {
		if (is_array($params))
			$this->params = $params;
	}

	function getMosaic($fromImg="") {
		if (!$this->imageIds)
			return blankimage();
		if ($this->loadtime) 
			$begin=getmicrotime();
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

		foreach($this->imageIds as $k=>$v) {
			$curimageinfo = $leginondata->getImageInfo($v);
			$dr = $curimageinfo['delta row'];
			$dc = $curimageinfo['delta column'];
			if (is_null($dr) || is_null($dc))
				continue;
			$imageinfo[] = $curimageinfo;
			$drows[] = $dr;
			$dcols[] = $dc;
		}

		if ($drows && $dcols) {
			$min_row = min($drows) - $imageinfo[0][dimy]/2;
			$max_row = max($drows) + $imageinfo[0][dimy]/2;
			$min_col = min($dcols) - $imageinfo[0][dimx]/2;
			$max_col = max($dcols) + $imageinfo[0][dimx]/2;
		}

		if ($this->size) {
			$max_w = (2*$margin + $max_col - $min_col);
			$ratio = $max_w/$this->size;
		}

		$img_w = (2*$margin + $max_col - $min_col)/$ratio;
		$img_h = (2*$margin + $max_row - $min_row)/$ratio;
		$img = imagecreatetruecolor($img_w, $img_h);
		$background = imagecolorallocate($img, 0, 0, 0);
		$crosscol = imagecolorallocate($img, 255, 255, 0);
		$blue = imagecolorallocate($img, 0, 255, 255);
		if ($this->displayframe)
			$mosaicframecol = imagecolorallocate($img,
						($this->framecolor >> 16) & 0xFF,
						($this->framecolor >> 8) & 0xFF,
						$this->framecolor & 0xFF
						);

		$sessionId = $imageinfo[0][sessionId];
		$squaresize = $imageinfo[0][dimx]/$ratio;
		$this->params['size'] = $squaresize;
		$this->params['binning'] = ($ratio<1) ? 1 : $ratio;

		if ($fromImg)
			$img = $fromImg;
		else {
		    foreach ($imageinfo as $k=>$r) {
			$cx = ($margin + $dcols[$k] - $min_col)/$ratio; 
			$cy = ($margin + $drows[$k] + $max_row)/$ratio;
			$squarepoints = getsquarepoints($cx, $cy, $angle, $squaresize);
			$dst_x = $squarepoints[0];
			$dst_y = $squarepoints[1];
			$gimg = getImage($sessionId, $r[imageId], $preset, $this->params);
			$src_w = imagesx($gimg);
			$src_h = imagesy($gimg);
			imagecopy($img, $gimg, $dst_x, $dst_y, $src_x, $src_y, $src_w, $src_h);
			imagedestroy($gimg);
			if ($this->displayframe) {
				if ($this->cId==$r[imageId]) {
					$crossquare = $squarepoints;
					$cdx = $dst_x+1;
					$cdy = $dst_y;
					$cnb =$k+1;
				}
				drawsquare($img, $squarepoints, $mosaicframecol);
				imagestringshadow($img, 4, $dst_x+1, $dst_y, $k+1, $mosaicframecol);
			}
		    }
		}

		if ($crossquare) {
			$col = $crosscol;
			drawsquare($img, $crossquare, $crosscol);
			imagestringshadow($img, 4, $cdx, $cdy, $cnb, $blue);
		}

		/*
		if ($this->displayscalebar) {
			$size = $squaresize;
			$value = $imageinfo[0][pixelsize]*$imageinfo[0][binning]*$ratio;
			$scalebar = new ScaleBar($img, $size, $value);
			$scalebar->display($img_h-20);
		}
		*/
		if ($this->displayscalebar) {
			$size = ($max_row - $min_row)/$ratio;
			$value = $imageinfo[0][pixelsize]*$imageinfo[0][binning]*$ratio;
			$scalebar = new ScaleBar($img, $size, $value);
			$scalebar->display($img_h);
		}
		if ($this->loadtime) {
			$end=getmicrotime();
			imagestringshadow($img, 4, 10/$ratio, 10/$ratio, "load time: ".($end-$begin), $mosaicframecol);
		}
		return $img;
	}
}
?>
