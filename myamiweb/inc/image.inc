<?php
/**
 *	@version $Revision: 1.38 $
 *	@version $Id: image.inc,v 1.38 2008-01-03 23:33:49 dfellman Exp $
 */
/**
 *	Tools to display images / mosaic
 *	
 */

require_once "config.php";
require_once "inc/util.inc";
require_once "inc/filter.inc";
require_once "inc/graphutil.inc";
require_once "inc/scalebar.inc";
require_once "inc/cachedb.inc";



function getImage($sessionId, $imageId, $preset, $params = array()) {

	$p = array (
		'size'=> '',
		'minpix' => 0,
		'maxpix' => 255,
		'filter' => 'default',
		'fft' => false,
		'gradient' => false,
		'binning' => 'auto',
		'scalebar' => true,
		'displaytargets' => true,
		'loadtime' => false,
		'ptlc' => false,
		'newptcl' => false,
		'autoscale' => false,
		'targettype' => false,
		'loadjpg' => false,
		'mrc' => false
	);

	if (is_array($params))
		foreach ($params as $k=>$v)
			$p[$k] = $v;

	$size = $p['size'];
	$binning = $p['binning'];
	$loadjpg = $p['loadjpg'];

	$leginondata = new leginondata();
	// --- get image path
	$path = $leginondata->getImagePathFromImageId($imageId);

	// --- find image
	$newimage = $leginondata->findImage($imageId, $preset);
	$imageId = $newimage['id'];
	$parent = $leginondata->getImageInfo($newimage['childid']);

	// --- get filename
	if ($p['fft']) {
		$p['displaytargets']=false;
		$p['scalebar']=false;
		$fft = $leginondata->getImageFFT($imageId);
		if (!$filename = $fft['fftimage']);
			$filename = $leginondata->getFilenameFromId($imageId);
	} else {
		$filename = $leginondata->getFilenameFromId($imageId);
	}

	$pic = $path.$filename;
	if (@is_file($pic)) {
		$imginfo = $leginondata->getImageInfo($imageId);
		$dimx = $imginfo['dimx'];
		if ($binning=='auto') {
			$binning = ($dimx > 1024) ? (($dimx > 2048) ? 4 : 2 ) : 1;
		}

		if ($p['loadjpg'] && !$p['fft']) {
			$sessioninfo=$leginondata->getSessionInfo($sessionId);
      $session=$sessioninfo['Name'];
			$jpgfilename = ereg_replace('mrc$', 'jpg', $filename);
			$jpgpath = CACHE_PATH.$session."/";
			$jpgpic = $jpgpath.$jpgfilename;
		}
		if (@is_file($jpgpic)) {
			$img = imagecreatefromjpeg($jpgpic);
			$binning=$dimx/imagesx($img);
		} else {
		if ($p['autoscale']) {
			list($type,$arg1, $arg2)=explode(";", $p['autoscale']);
			
			$densitymax = MAX_PIXEL_VAL;
			if ($type=="c") {
				$mrcimg = mrcread($pic);
				mrcupdateheader($mrcimg);
				list($p['minpix'], $p['maxpix'])=mrccdfscale($mrcimg, $arg1, $arg2);
				mrcdestroy($mrcimg);
				
			} else {
			
			list($info) = $leginondata->getImageStat($id);
			if ($info) {
				$minval = $info['min'];
				$maxval = $info['max'];
				$meanval = $info['mean'];
				$stdev = $info['stdev'];
			} else {
				$mrcimg = mrcread($pic);
				mrcupdateheader($mrcimg);
				$info = mrcgetinfo($mrcimg);
				mrcdestroy($mrcimg);
				$minval = $info['amin'];
				$minval = $info['amin'];
				$maxval = $info['amax'];
				$meanval = $info['amean'];
				$stdev = $info['rms'];
			}
			if ($meanval && $stdev && $maxval-$minval) {
				$nstdev=($arg1>=1) ? $arg1 : 3;
				$p['minpix'] = (($meanval - $nstdev*$stdev)-$minval)*$densitymax/($maxval-$minval);
				$p['maxpix'] = (($meanval + $nstdev*$stdev)-$minval)*$densitymax/($maxval-$minval);
			}
			}
		}
				
		if ($p['loadtime'])
			$begin=getmicrotime();

		if ($p['mrc']) {
			$imgmrc = mrcread($pic);
			mrcbinning($imgmrc, $binning);
			return $imgmrc;
		}
		if ($p['fft']) {
			$img = getfft($pic, $p['minpix'], $p['maxpix'], $binning, $p['autoscale']);
		}

		else if (function_exists($p['filter']))
			$img = $p['filter']($pic, $p['minpix'], $p['maxpix'], $binning);

		else
			$img = getdefault($pic, $p['minpix'], $p['maxpix'], $binning);

		}

		$scalefactor=1;
		if ($size) {
			$scalefactor = (imagesx($img)) ? $size/imagesx($img) : 1;
			myimagescale($img, $scalefactor);
		}
		if ($p['gradient']) {
			require "inc/gradient.php";
			if ($gradient=getGradient($p['gradient'])) {
				imagegradient($img, $gradient);
			}
		}

		if ($p['loadtime'])
			$end=getmicrotime();

		$white = imagecolorallocate($img, 255, 255, 255);
		$blue = imagecolorallocate($img, 0, 255, 255);
		$yellow= imagecolorallocate($img, 255, 255, 0);
		if ($p['displaytargets']) {
		    $targets = $leginondata->getImageTargets($imageId);
		    if ($targets = $leginondata->matchVersionTargets($targets))
		    foreach ($targets as $target) {
			$tId=$target['childId'];
			$targetinfo = $leginondata->getImageInfo($tId);
			// --- use "stage position" or "image shift" based on magnification
			$type = "image shift" ;
			$type = "stage position";
			$type = ($targetinfo['magnification']>2500 && $imginfo['magnification']>2500) ? "image shift" : "stage position";

			$targetcal = $leginondata->getImageMatrixCalibration($tId, $type);
			$parentcal = $leginondata->getImageMatrixCalibration($imageId, $type);

			$truediam=$targetinfo['targetdiam'];
			$truedim=$targetinfo['targetdim'];
			if (abs($target[x]-$parent['targetx'])<5
				&& abs($target[y]-$parent['targety'])<5 ){
				$col = $blue;
				$crosscol = $yellow;
			} else {
				$col = $white;
				$crosscol = $white;
			}
//			if (!$target['x'] || !$target['y'] || !$target['dimx'] || !$target['dimy'] )
//				continue;
			$tn = $target['tnumber'];
			$ratioX = ($size) ? $size/$target['dimx'] : (($binning) ? 1/$binning : 1);
			$ratioY = ($size) ? $size/$target['dimy'] : (($binning) ? 1/$binning : 1);
			$cx = $target['x']*$ratioX;
			$cy = $target['y']*$ratioY;

			if ($tId) {
				if ($p['targettype']) {
					$crosscol = imagecolorallocate($img, 255,0,0);
					$crosssize=20;
					drawcross($img, $cx, $cy, $crosssize*$ratioX, $crosscol, false);
				} else {
					$angle = $targetcal['angle']-$parentcal['angle'];
					$squarepoints = getsquarepoints($cx, $cy, $angle, $truedim*$ratioX);
					drawsquare($img, $squarepoints, $crosscol);
				}
				$ctx = $squarepoints[0]+1;
				$cty = $squarepoints[1]+1;
			} else {
				$crosssize=20;
				$ctx = $cx+$crosssize/2;
				$cty = $cy;
				// drawcross($img, $cx, $cy, $crosssize*$ratioX, $crosscol);
				//drawcircle($img, $cx, $cy, 2, $crosscol);
			}
			// imagestringshadow($img, 4, $ctx, $cty, $tn, $col);
			
		    }
		    if ($targets = $leginondata->getImageFocusTargets($imageId)) 
		    foreach ($targets as $target) {
			$tgn=$target['tversion'];
			$tn='focus';
			if (abs($target['x']-$parent['targetx'])<5
				&& abs($target['y']-$parent['targety'])<5 ){
				$col = $blue;
				$crosscol = $yellow;
			} else {
				$col = $white;
				$crosscol = $white;
			}
			$ratioX = ($size) ? $size/$target['dimx'] : (($binning) ? 1/$binning : 1);
			$ratioY = ($size) ? $size/$target['dimy'] : (($binning) ? 1/$binning : 1);
			$cx = $target['x']*$ratioX;
			$cy = $target['y']*$ratioY;

			$crosssize=20;
			$ctx = $cx+$crosssize/2;
			$cty = $cy;
			drawcross($img, $cx, $cy, $crosssize*$ratioX, $crosscol);
			imagestringshadow($img, 4, $ctx, $cty, $tn, $col);
		    }
		}
		if ($p['displayicethicktarget']) {
			$r = $leginondata->getIceThicknessFromImage($imageId);
			$imageinfo = $leginondata->getImageInfo($imageId);
			$ratioX = ($size) ? $size/$imageinfo['dimx'] : (($binning) ? 1/$binning : 1);
			$ratioY = ($size) ? $size/$imageinfo['dimy'] : (($binning) ? 1/$binning : 1);
			$crosssize=20;
			$crosscol = $yellow;
			$col = $white;
			foreach($r as $data) {
				$cx = ($data['column']+$imageinfo['dimx']/2)*$ratioX;
				$cy = ($data['row']+$imageinfo['dimy']/2)*$ratioY;
				$cx = ($data['column'])*$ratioX;
				$cy = ($data['row'])*$ratioY;
				$tn = $data['column']." ".$data['row'];
				$ctx = $cx+$crosssize/2;
				$cty = $cy;
				drawcross($img, $cx, $cy, $crosssize*$ratioX, $crosscol);
				imagestringshadow($img, 4, $ctx, $cty, $tn, $col);
			}
		}
		if ($driftdirection=0) {
		    if ($targets = $leginondata->getImageFocusTargets($imageId, true)) {

			$ratioX = ($size) ? $size/$target['dimx'] : (($binning) ? 1/$binning : 1);
			$ratioY = ($size) ? $size/$target['dimy'] : (($binning) ? 1/$binning : 1);
			$vert = imagecolorallocate($img, 0, 255,0);
			$rouge= imagecolorallocate($img, 255,0,0);

		    foreach ($targets as $target) {
			$tgn=$target['tversion'];
			$cx = $target['x']*$ratioX;
			$cy = $target['y']*$ratioY;
			$d[$tgn][] = array('x'=>$cx,'y'=>$cy);
		}
			foreach($d as $point) {
			/*
				$li = count($d[$n])-1;
				$cx1 = $d[$n][0]['x'];
				$cy1 = $d[$n][0]['y'];
				$cx = $d[$n][$li]['x'];
				$cy = $d[$n][$li]['y'];
			*/
				$li = count($point)-1;
				$cx1 = $point[0]['x'];
				$cy1 = $point[0]['y'];
				$cx = $point[$li]['x'];
				$cy = $point[$li]['y'];
				$arrow = new arrow ($img, $cx1,$cy1, $cx, $cy, $vert);
				$arrow->draw();
			}

			if (is_Array($d))
				foreach($d as $k=>$point) {
					foreach ($point as $p) 
						imageline ( $img, $p['x'], $p['y'], $p['x'], $p['y'], $rouge);
				}



			}
		}

		/* diplay loading time */
		if ($p['loadtime'])
			imagestringshadow($img, 4, 10, 10, "load time: ".($end-$begin), $blue);

		/* display scale bar */
		if ($p['scalebar']) {
		    if ($imginfo) {
			$size = ($size) ? $size : (($binning) ? $imginfo['dimx']/$binning : $imginfo['dimx']);
			if (!$size)
				$size=1;
			$ratio = $imginfo['dimx']/$size ;
			$value = $imginfo['pixelsize']*$imginfo['binning']*$ratio;
			$scalebar = new ScaleBar($img, $size, $value);
			$scalebar->display();
		    }
		}
		/* display particles */
		if ($p['ptcl']) {
			$selectioninfo = string2selections($p['ptcl']);
			foreach ($selectioninfo as $sel) {
				$selectionId = $sel[0];
				if (!$selectionId)
					continue;
				$selcolor = $sel[1];
				$seltarget = $sel[2];
				$col = imagecolorallocatehex($img,$selcolor);
				$dbp = new particledata();
				$particles = $dbp->getParticlesFromSelectionId($selectionId, $filename);
				foreach ($particles as $particle) {
					$tsize = 100*$scalefactor/$binning;
					$cx = $particle['Xcoord']/$binning*$scalefactor;
					$cy = $particle['Ycoord']/$binning*$scalefactor;
					if (!$boxsize = $particle['Boxsize']/$binning*$scalefactor)
						$boxsize = $tsize;
				
					if ($seltarget=='cir1')
						drawcircle($img, $cx, $cy, $tsize, $col, true);
					if ($seltarget=='cross1')
						drawcross ($img, $cx, $cy, $tsize, $col, false, 45, true);
					if ($seltarget=='cross2')
						drawcross ($img, $cx, $cy, $tsize, $col, false, 0, true);
					if ($seltarget=='box1') {
						drawbox ($img, $cx, $cy, $boxsize, $col, 0, true);
				}

				}
			}
		
		}
		if ($p['newptcl'] && defined('PROCESSING')) {
				list($pon, $diam)=explode(";", $p['newptcl']['info']);
				require "inc/particledata.inc";
				require "inc/histogram.inc";
				$particle = new particledata();
				$particlerun=$particle->getLastParticleRun($sessionId);
				if ($p['ptclsel']) {
					$particleruns=$particle->getParticleRunIds($sessionId);
					foreach ($particleruns as $prun) {
							$particlerun=$prun['DEF_id'];
							if($p['ptclsel']==$particlerun)
								break;
					}
				}
				$particledata=$particle->getParticlesFromImageId($particlerun, $imageId);
				list($selectionparams)=$particle->getSelectionParams($particlerun);
				if (!$diam) {
					$diam = $selectionparams['diam'];
				}
				$d=array_map('getdiam', $particledata);
				$d=array_unique($d);
				$groupcolors=array();
				$index=0;
				foreach ((array)$d as $val) {
					$groupcolors[(int)$val]=getParticleColor($img, $index);
					$index++;
				}
				$col = imagecolorallocate($img, 255,255,255);
				$apix = $imginfo['pixelsize']*1e10;
				$diam = $diam*$scalefactor/$binning/$apix/$imginfo['binning'];
				$correlationmin=$p['newptcl']['cm'];
				$correlationmax=$p['newptcl']['cx'];
				$tresh = (is_numeric($correlationmin) && is_numeric($correlationmax)) ? true : false;
				foreach ((array)$particledata as $particle) {
					if ($tresh && ($particle['correlation']<$correlationmin || $particle['correlation']>$correlationmax)) {
						continue;
					}
					$cx = $particle['xcoord']/$binning*$scalefactor;
					$cy = $particle['ycoord']/$binning*$scalefactor;
					$col=$groupcolors[(int)$particle['diameter']];
					if (!$col) {
						$col = imagecolorallocate($img, 255,255,255);
					}
					drawcircle($img, $cx, $cy, $diam, $col, true);
				}
		}

	} else {
		//$img = blankimage();
		//instead to create a blankimge(). We need to return false.
		return false;
	}
	return $img;

}

function getImageXML($xmlfile, $imageId, $preset, $params = array()) {

	$p = array (
		'size'=> '',
		'minpix' => 0,
		'maxpix' => 255,
		'filter' => 'default',
		'fft' => false,
		'binning' => 'auto',
		'scalebar' => true,
		'displaytargets' => true,
		'loadtime' => false,
		'ptlc' => false,
		'autoscale' => false,
		'mrc' => false
	);

	if (is_array($params))
		foreach ($params as $k=>$v)
			$p[$k] = $v;

	$size = $p['size'];
	$binning = $p['binning'];

	$xmldata = new xmldata($xmlfile);
	// --- get image path
	$path = $xmldata->getImagePath();

	// --- get filename
	if ($p['fft']) {
		$p['displaytargets']=false;
		$p['scalebar']=false;
	}
	$filename = $xmldata->getFilenameFromId($imageId);

	$pic = $path.$filename;
	if (@is_file($pic)) {
		$imginfo = $xmldata->getImageInfo($imageId);
		$dimx = $imginfo['dimx'];
		if ($p['autoscale']) {
			list($type,$arg1, $arg2)=explode(";", $p['autoscale']);
			
			$densitymax = MAX_PIXEL_VAL;
			if ($type=="c") {
				$mrcimg = mrcread($pic);
				list($p['minpix'], $p['maxpix'])=mrccdfscale($mrcimg, $arg1, $arg2);
				
			} else {

				$info = mrcinfo($pic);
				$mrc = mrcread($pic);
				mrcupdateheader($mrc);
				$fileinfo = mrcgetinfo($mrc);
				mrcdestroy($mrc);
				$minval = $info['amin'];
				$maxval = $info['amax'];
				$meanval = $info['amean'];
				$stdev = $info['rms'];
				if ($meanval && $stdev) {
					$p['minpix'] = (($meanval - 3*$stdev)-$minval)*$densitymax/($maxval-$minval);
					$p['maxpix'] = (($meanval + 3*$stdev)-$minval)*$densitymax/($maxval-$minval);
				}

			}
		}
				
		if ($p['loadtime'])
			$begin=getmicrotime();

		if ($binning=='auto')
			$binning = ($dimx > 1024) ? (($dimx > 2048) ? 4 : 2 ) : 1;

		if ($p['mrc']) {
			$imgmrc = mrcread($pic);
			mrcbinning($imgmrc, $binning);
			return $imgmrc;
		}
		if ($p['fft']) {
			$img = getfft($pic, $p['minpix'], $p['maxpix'], $binning, $p['autoscale']);
		}

		else if (function_exists($p['filter']))
			$img = $p['filter']($pic, $p['minpix'], $p['maxpix'], $binning);

		else
			$img = getdefault($pic, $p['minpix'], $p['maxpix'], $binning);


		$scalefactor=1;
		if ($size) {
			$scalefactor = (imagesx($img)) ? $size/imagesx($img) : 1;
			myimagescale($img, $scalefactor);
		}

		if ($p['loadtime'])
			$end=getmicrotime();

		$white = imagecolorallocate($img, 255, 255, 255);
		$blue = imagecolorallocate($img, 0, 255, 255);
		$yellow= imagecolorallocate($img, 255, 255, 0);

		/* diplay loading time */
		if ($p['loadtime'])
			imagestringshadow($img, 4, 10, 10, "load time: ".($end-$begin), $blue);

		/* display scale bar */
		if ($p['scalebar']) {
		    if ($imginfo) {
			$size = ($size) ? $size : (($binning) ? $imginfo['dimx']/$binning : $imginfo['dimx']);
			if (!$size)
				$size=1;
			$ratio = $imginfo['dimx']/$size ;
			$value = $imginfo['pixelsize']*$imginfo['binning']*$ratio;
			$scalebar = new ScaleBar($img, $size, $value);
			$scalebar->display();
		    }
		}
	} else {
		$img = blankimage();
	}
	return $img;

}


function blankimage($w=256, $h="") {
	if (!$h)
		$h=$w;
	$blkimg = imagecreate($w, $h);
	$w = imagecolorallocate($blkimg, 255, 255, 255);
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

function resample($source, $new_width="", $new_height="") {
	header("Content-type: image/x-png");
	$width = imagesx($source);
	$height = imagesy($source);
	if ($new_width)
		$new_height = ($new_height) ? $new_height : $height / $width * $new_width;
	if ($new_height)
		$new_width = ($new_width) ? $new_width : $width / $height * $new_height;

	if ($new_width && $new_height) {
		$dest = imagecreatetruecolor($new_width,$new_height);
		imagecopyresampled($dest,$source,0,0,0,0,$new_width,$new_height,$width,$height);
		imagepng($dest);
		imagedestroy($dest);
	} else imagepng($source);

	imagedestroy($source);
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
			$min_row = min($drows) - $imageinfo[0]['dimy']/2;
			$max_row = max($drows) + $imageinfo[0]['dimy']/2;
			$min_col = min($dcols) - $imageinfo[0]['dimx']/2;
			$max_col = max($dcols) + $imageinfo[0]['dimx']/2;
		}

		if ($this->size) {
			$max_w = (2*$margin + $max_col - $min_col);
			$ratio = $max_w/$this->size;
		}

		$img_w = (2*$margin + $max_col - $min_col)/$ratio;
		$img_h = (2*$margin + $max_row - $min_row)/$ratio;
		$mrcimg = mrccreate($img_w, $img_h);
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

		$sessionId = $imageinfo[0]['sessionId'];
		$squaresize = $imageinfo[0]['dimx']/$ratio;
		$this->params['mrc'] = 1;
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
			if($dst_x<0)
				$dst_x=0;
			if($dst_y<0)
				$dst_y=0;
			$gimg = getImage($sessionId, $r['imageId'], $preset, $this->params);
			$src_w = mrcsx($gimg);
			$src_h = mrcsy($gimg);
			mrccopy($mrcimg, $gimg, $dst_x, $dst_y, $src_x, $src_y, $src_w, $src_h);
			mrcdestroy($gimg);
		//	$gimg = getImage($sessionId, $r['imageId'], $preset, $this->params);
		//	$src_w = imagesx($gimg);
		//	$src_h = imagesy($gimg);
	//		imagecopy($img, $gimg, $dst_x, $dst_y, $src_x, $src_y, $src_w, $src_h);
	//		imagedestroy($gimg);
			if ($this->displayframe) {
				if ($this->cId==$r['imageId']) {
					$crossquare = $squarepoints;
					$cdx = $dst_x+1;
					$cdy = $dst_y;
					$cnb =$k+1;
				}
			}
		    }
		}
		mrcupdateheader($mrcimg);
		$img = mrctoimage($mrcimg);
		mrcdestroy($mrcimg);
		if ($this->displayframe) {
			drawsquare($img, $crossquare, $mosaicframecol);
			imagestringshadow($img, 4, $cdx, $cdy, $cnb , $mosaicframecol);
		}

		if ($crossquare) {
			$col = $crosscol;
			drawsquare($img, $crossquare, $crosscol);
			imagestringshadow($img, 4, $cdx, $cdy, $cnb, $blue);
		}

		if ($this->displayscalebar) {
			$size = ($max_row - $min_row)/$ratio;
			$value = $imageinfo[0]['pixelsize']*$imageinfo[0]['binning']*$ratio;
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

function myimagescale(&$img, $percent) {
	// Get new sizes
	$source = $img;
	$width = imagesx($source);
	$height = imagesy($source);
	$newwidth = $width * $percent;
	$newheight = $height * $percent;
	$img = imagecreatetruecolor($newwidth, $newheight);
	imagecopyresampled($img, $source, 0, 0, 0, 0, $newwidth, $newheight, $width, $height);
	imagedestroy($source);
}

function getdiam($a) {
	return $a['diameter'];
}

function getParticleColor($img, $index) {
$colors = array ( 
		"#ff4040","#3df23d","#3d3df2", 
		"#f2f23d","#3df2f2","#f23df2", 
		"#f2973d","#3df297","#973df2", 
		"#97f23d","#3d97f2","#f23d97" );
$n=sizeof($colors);
$index=$index%$n;
$hexstr=$colors[$index];
$int = hexdec($hexstr);
  return ImageColorAllocate ($img,
         0xFF & ($int >> 0x10),
         0xFF & ($int >> 0x8),
         0xFF & $int);
}
	
?>
