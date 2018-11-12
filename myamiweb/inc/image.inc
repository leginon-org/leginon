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
require_once "inc/overlay.inc";
require_once "inc/cachedb.inc";
require_once "inc/imageutil.inc";
require_once "inc/imagerequest.inc";
require_once "inc/path.inc";
require_once "inc/fileutil.inc";

function getImageFile($leginondata,$imageId,$preset='all',$loadjpg=false,$is_fft=false,$cacheonly=false) {
	$newimageId = getImageIdFromPreset($leginondata,$imageId,$preset);
	return __getImageFile($leginondata,$newimageId,$loadjpg,$is_fft,$cacheonly);
}

function getImageIdFromPreset($leginondata,$imageId,$preset='all') {
	$newimage = $leginondata->findImage($imageId, $preset);
	$imageId = $newimage['id'];
	return $imageId;
}

function __getImageFile($leginondata,$imageId,$loadjpg=false,$is_fft=false,$cacheonly=false) {
	//get image file with full path
	$path = $leginondata->getImagePathFromImageId($imageId);

	// --- find image
	if ($is_fft) {
		$fftinfo = $leginondata->getImageFFT($imageId);
		if (!$filename = $fftinfo['fftimage']);
			$filename = $leginondata->getFilenameFromId($imageId);
	} else {
		$filename = $leginondata->getFilenameFromId($imageId);
	}
	$pic = $path.$filename;
	if (!$pic) return false;

	// Use Cached jpeg image if available
	if ($loadjpg && ENABLE_CACHE) {
		$sessioninfo=$leginondata->getSessionInfoFromImage($imageId);
		$session=$sessioninfo['name'];
		$pic = useCache($pic,$session,$is_fft,$cacheonly);
	}
	return $pic;
}

function getImage($sessionId, $imageId, $preset, $params = array()) {
	// autoscale => $scaleMin, $scaleMax, $scaleType
	$p = array (
		'size'=> '',
		'minpix' => 0,
		'maxpix' => 255,
		'filter' => 'default',
		'fft' => false,
		'fftbin' => 'a',
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
		'cacheonly' => false,
		'mrc' => false
	);

	if (is_array($params))
		foreach ($params as $k=>$v)
			$p[$k] = $v;

	$leginondata = new leginondata();
	// --- get filename
	if ($p['fft']) {
		$p['displaytargets']=false;
		$p['newptcl']=false;
	}

	$parentId = getImageIdFromPreset($leginondata,$imageId,$preset);
	$pic = __getImageFile($leginondata,$parentId,$p['loadjpg'],$p['fft'],$p['cacheonly']);

// 	if (!$pic || !is_file($pic)) {
// 		$messages = array('File not found: ');
// 		if ($p['cacheonly'] && $p['loadjpg']) {
// 			$messages[] = 'Cached Image Not Ready.';
// 		}
// 		$messages[] = $pic;
// 		return makeBlankImageWithErrorMessage($messages);
// 	}
	// pass on whether the image is from cache
	$p['iscache']= (strpos($pic,'jpg'))? true:false;

	$childimginfo = $leginondata->getImageInfo($imageId);

	$shownimginfo = $leginondata->getImageInfo($parentId);
	$img =  getImageFromRequester($pic,$shownimginfo,$p);
	return addAppionOverlays($leginondata,$img,$childimginfo,$shownimginfo,$p);
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
		'newptlc' => false,
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
	$path = str_replace('./',Path::formatPath(WEB_ROOT),$path);
	// --- get filename
	if ($p['fft']) {
		$p['displaytargets']=false;
		$p['newptcl']=false;
	}
	$filename = $xmldata->getFilenameFromId($imageId);

	$pic = $path.$filename;
	if (@is_file($pic)) {
		$imginfo = $xmldata->getImageInfo($imageId);
		return getImageFromRequester($pic,$imginfo,$p);
	}
}	

function makeBlankImageWithErrorMessage($error_text) {
	$image_util = new imageUtil();
	$img = $image_util->makeBlankImageWithErrorMessage($error_text);
	return $img;
	
}

function getImageFromRequester($pic,$imginfo,$p) {
	/* This function get image in the required dimension, 
			format, and pixel processing. Scale bar and ring
			are added if asked.  It is called by both
			getImg and getImageXML and does not use database.
	*/
	// create imageRequester and imageUtil instances to begin.
	$imagerequest = new imageRequester();
	$imageUtil = new imageUtil();

	//dimx,dimy are image size in the database
	$dimx = $imginfo['dimx'];
	$dimy = $imginfo['dimy'];
	//size is the frame size
	$frame_size = $p['size'];
	// binning is the scaled and loaded image size before fitting into the frame
	$binning = $p['binning'];
	$loadjpg = $p['loadjpg'];
	// find out the proper x, y for display
	$default_size = $imageUtil->getDefaultImageSize($p['fft']);
	if ($frame_size)
		$xyDim = $imageUtil->imageFitIn($dimx, $dimy, $frame_size);
	else
		$xyDim = $imageUtil->imageBinning($dimx, $dimy, $binning, $default_size);
	//Default prefftDim
	$prefftDim = $xyDim;
	//
	$imgheaderinfo = $imagerequest->requestInfo($pic);
	$iscalearray = getIntensityScale($p,$imgheaderinfo);
	$scaletype = $iscalearray[0];
	$arg1 = $iscalearray[1];
	$arg2 = $iscalearray[2];
	//filtering
	if (function_exists($p['filter']))
		$lpf_sigma = $p['filter']() * $xyDim[0] / $dimx;

	if (!$p['fft']) {
		$imgstr = $imagerequest->requestImage($pic,'JPEG',$xyDim,$scaletype,$arg1,$arg2,$lpf_sigma,false,(bool)$p['fft'],false);
	} else {
		if ($p['iscache']) {
			//cached power spectrum image does not need further transform
			$imgstr = $imagerequest->requestImage($pic,'JPEG',$xyDim,$scaletype,$arg1,$arg2,$lpf_sigma,false,false,false);
			$prefftDim = $imageUtil->imageBinning($dimx, $dimy, $binning, $default_size);
		} else {
			// fft
			if (isBinBeforeFFT($p)) 
				$prefftDim = getImageXYDimFromBinningParams($imginfo,$p);
			$imgstr = $imagerequest->requestImage($pic,'JPEG',$xyDim,$scaletype,$arg1,$arg2,$lpf_sigma,false,(bool)$p['fft'],false);
		}
	}
	if (!$imgstr) {
		return makeBlankImageWithErrorMessage('redux failed to return anything');
	}
	if (substr($imgstr,0,11) === 'REDUX ERROR') {
		return makeBlankImageWithErrorMessage($imgstr);
	}
	if (!$p['iscache'] && isBinBeforeFFT($p)) {
		//Fake prefft binning by resample
		$src_coords = $imageUtil->getResampleCoordinates($dimx,$dimy,$xyDim, $binning, $default_size);
		$tmpimg = imagecreatefromstring($imgstr);
		$img = imagecreatetruecolor($xyDim[0],$xyDim[1]);
		imagecopyresampled($img,$tmpimg,0,0,$src_coords[0],$src_coords[1],$xyDim[0],$xyDim[1],$src_coords[2],$src_coords[3]);
		imagedestroy($tmpimg);
	} else {
		$img = imagecreatefromstring($imgstr);
	}
	$display_pixelsize = getDisplayPixelSize($img,$imginfo,$p['fft'],$p['fftbin'],$prefftDim,$p['iscache']);
	if ($p['scalebar']) 
		$img = addScaleBarRingToImage($img,$display_pixelsize,$p['fft'],$p['fftbin']);

	// This is for future implementation of radialplot overlay.
	if (false && $p['fft']) {
		$linedata = array();
		$linedata[] = readRadialPlotValues('corrected');
		$linedata[] = readRadialPlotValues('sample');
		$linedata[] = readRadialPlotValues('background');
		if ($linedata !== false)
			$img = addRadialPlotToImage($img,$linedata,$display_pixelsize,$p['fftbin']);
	}

	// This is a good place to add debug message as a string on the image
	$debug_message .= '';
	imagestring($img, 4, 11, 21, $debug_message, imagecolorallocate($img,0,0,255));
	imagestring($img, 4, 10, 20, $debug_message, imagecolorallocate($img,255,255,255));
	return $img;
}

function isBinBeforeFFT($p) {
	return ($p['fft'] && $p['fftbin'] == 'b');
}

function getDisplayPixelSize($img,$imginfo,$isfft,$fftbintype,$prefftDim,$iscache=false) {
	$imageUtil = new imageUtil();
	$input_dimx = $imginfo['dimx'];
	$input_calpixelsize = $imginfo['pixelsize'];
	$input_cambinning = $imginfo['binning'];
	$display_dimx = imagesx($img);
	$prefft_dimx = $prefftDim[0];
	return $imageUtil->getDisplayPixelSize($input_calpixelsize,$input_cambinning,$input_dimx,$display_dimx,$isfft,$fftbintype,$prefft_dimx,$iscache);
}

function getIntensityScale($p,$imgheaderinfo) {
	$imageUtil = new imageUtil();
	if ($p['autoscale']) 
		if ($p['autoscale']===true) {
			$type = 'stdev';
			$arg1 = 5;
		} else {
			list($type,$arg1, $arg2)=explode(";", $p['autoscale']);
		}
	else $type = '0';
	
	switch($type){
		// when scale type is 'minmax'
		case ('0'):
			$scaletype = "minmax";
			$min = $imgheaderinfo->amin;
			$max = $imgheaderinfo->amax;
			$slope = ($max - $min) / 100.0;
			#$pctminmax = $imageUtil->scaleMinMaxConvert($p['minpix'], $p['maxpix']);
			#$arg1 = $pctminmax['minpix'];
			#$arg1 = $pctminmax['minpix'];
			$arg1 = $p['minpix'] * $slope + $min;
			$arg2 = $p['maxpix'] * $slope + $min;
			break;
		// when scale type is 'cdf'
		case ('c'):
			$scaletype = "cdf";
			break;
		// when scale type is 'stdev'
		default:
			$scaletype = "stdev";
			$arg2=($arg1>=1) ? $arg1 : 5;
			$arg1= -1 * $arg1;
			break;
	}
	return array($scaletype,$arg1,$arg2);
}

function readRadialPlotValues($datatype) {
	$read = new fileDataRead();
	$rtypes = array('radius','corrected','sample','background');
	// Reading from saved CSV file n myamiweb base directory for now.
	$read->setFile('final.csv',',',count($rtypes));
	$index = array_search($datatype,$rtypes);
	if ($index === false) return false;
	return $read->getColumnFromCSV($index);
}

function addRadialPlotToImage($img,$values,$display_pixelsize,$fftbintype) {
	// create image overlay on image object
	$overlay = new imageOverlay($img);
	$xyDim = array(imagesx($img),imagesy($img));
	$scale = 0.0001;
	$overlay->drawRadialPlot($values,$display_pixelsize,$xyDim,$fftbintype,$scale);
	return $img;
}

function addScaleBarRingToImage($img,$display_pixelsize,$isfft,$fftbintype) {
	// create image overlay on image object
	$overlay = new imageOverlay($img);

	$xyDim = array(imagesx($img),imagesy($img));
	// display scale bar //
	if (!$isfft) {
		$overlay->addScaleBar($display_pixelsize,$xyDim);
	} else {
		$overlay->addScaleRing($display_pixelsize,$xyDim,$fftbintype);
	}
	return $img;
}

function getImageXYDimFromBinningParams($imginfo,$p) {
	$imageUtil = new imageUtil();
	$dimx = $imginfo['dimx'];
	$dimy = $imginfo['dimy'];
	$binning = $p['binning'];
	$default_size = $imageUtil->getDefaultImageSize($p['fft']);
	$xyDim = $imageUtil->imageBinning($dimx, $dimy, $binning, $default_size);
	return $xyDim;
}

function addAppionOverlays($leginondata,$img,$childinfo,$imginfo,$p) {
	//$imginfo is the information of the image that the overlay is put on.
	//$childinfo is the information of the original image that getimg is passed in
	// create image overlay on image object
	$overlay = new imageOverlay($img);

	$prefftDim = getImageXYDimFromBinningParams($imginfo,$p);
	$display_pixelsize = getDisplayPixelSize($img,$imginfo,$p['fft'],$p['fftbin'],$prefftDim,$p['iscache']);
	$debug_message = '';
	$sessionId = $imginfo['sessionId'];
	$imageId = $imginfo['imageId'];
	$dimx = $imginfo['dimx'];
	$xyDim = array(imagesx($img),imagesy($img));
	$display_bin = $dimx/$xyDim[0];
	// display targets //
	if ($p['displaytargets']) {
		$acqtargets = $leginondata->getImageTargets($imageId);
		$focustargets = $leginondata->getImageTargets($imageId,'focus');
		$previewtargets = $leginondata->getImageTargets($imageId,'preview');
		foreach (array('acq'=>$acqtargets,'focus'=>$focustargets, 'preview'=>$previewtargets) as $targettype=>$targets) {
			if ($targettype == 'acq'||$targettype == 'preview') $targets = $leginondata->matchVersionTargets($targets);
			if (!empty($targets))
				foreach ($targets as $target) {
					// acquired targets should have childId
					$tId=(int)$target['childId'];
					// show targets before acquiring as as cross, not square
					if ($tId == 0 && $targettype == 'acq') $targettype = 'new';
					if ($tId == 0 && $targettype == 'preview') $targettype = 'new';
					$locationresults = getTargetLocation($leginondata,$imageId,$imginfo,$childinfo,$target,imagesx($img));
					$child_shown = $locationresults[1];
					$square_params = $locationresults[0];
					if ($tId || $targettype != 'acq' || $targettype != 'preview') 
						$overlay->drawTarget($square_params,$child_shown,$targettype);
			}
		}
	}

	// display particles //
	if ($p['newptcl'] && defined('PROCESSING')) {
		// --- extract particle info --- //
		$displaylabel = $p['newptcl']['displaylabel'];
		$colorby = $p['newptcl']['colorby'];
		// --- Color by: l => label; d => diameter --- //
		$colorby = ($colorby=='l') ? 'label' : 'diameter';
		$labeled_particleinfo = getParticles($sessionId,$p['ptclsel'],$p['newptcl'],$imginfo,$display_bin);

		$particleinfo=$labeled_particleinfo[0];
		$selectionparams=$labeled_particleinfo[1];;
		$particlelabels = $labeled_particleinfo[2];
		$labeldata = $labeled_particleinfo[3];
		$particlerun = $selectionparams['runId'];
		$cx = 10;
		$cy = 30;
		$lsize = 10;

		$particlelabelparams = setParticleLabelParams($img,$particlelabels,$labeldata);
		// --- pixelsize in angstrom --- //
		$apix = $display_pixelsize*1e10;
		$diam_scalefactor = 1/$apix;
		if (!$diam || $diam == $selectionparams['diam']) {
			// apply scaling if not applied before
			$diam = $selectionparams['diam'] * $diam_scalefactor;
		} elseif ($diam) {
			$diam = $diam * $diam_scalefactor;
		}
		$groupcolors = setGroupColors($particleinfo,$img);

		foreach ((array)$particleinfo as $particle) {
			$cx = $particle['xcoord']/$display_bin;
			$cy = $particle['ycoord']/$display_bin;

			$col=$groupcolors[(int)$particle['diameter']];
			//set diam and threshhold by particle label
			if ($labeldata) {
				if ($colorby=='label') {
					$col=$particlelabelparams['color'][$particle['label']];
				}
				$diam=$particlelabelparams['diam'][$particle['label']] * $diam_scalefactor;
	$debug_message = $particlelabelparams['diam'][$particle['label']];
	$debug_message = $particlelabelparams['msg'];
				$thres1=$particlelabelparams['thres1'][$particle['label']];
				$thres2=$particlelabelparams['thres2'][$particle['label']];
			}
			//apply threshold
			$threshold = (is_numeric($thres1) && is_numeric($thres2)) ? true : false;
			if ($threshold && ($particle['correlation']<$thres1 || $particle['correlation']>$thres2)) {
				continue;
			}
			//set to default color if everything fails
			if (!$col) {
				$col = imagecolorallocate($img, 255,255,255);
			}
			//draw
			drawcircle($img, $cx, $cy, $diam, $col, true);
		}
		//draw object trace
		if ($selectionparams['trace']) {
			$traces = getTraces($particlerun, $imageId);
			if (!empty($traces)) {
				$col = imagecolorallocate($img, 0,255,0);
				foreach ($traces as $t) {
					// draw each trace as a polygon
					$linearpoints = array();
					$pointcount = count($t);
					foreach ($t as $point) {
						$linearpoints[] = $point['x'] / $display_bin ;
						$linearpoints[] = $point['y'] / $display_bin ;
					}
					drawpolygon($img,$linearpoints,$col,true);
				}
			}	
		}
	}
	if (!$img) 
		$img = blankimage(512);
	// This is a good place to add debug message as a string on the image
	$debug_message = '';
	imagestring($img, 2, 10, 30, $debug_message, imagecolorallocate($img,0,255,255));
	return $img;
}

function makeFakeImageInfo($parent) {
	$targetinfo = array();
	$targetinfo['x'] = $parent['targetx'];
	$targetinfo['y'] = $parent['targety'];
	$targetinfo['targetdim'] = 50;
	return $targetinfo;
}

function getTargetLocation ($leginondata,$imageId,$imginfo,$parentimginfo,$target,$frame_size) {
	$tId=(int)$target['childId'];
	if ($tId) {
		$targetinfo = $leginondata->getImageInfo($tId);
	} else {
		$targetinfo = makeFakeImageInfo($parentimginfo);
	}
	// --- use "stage position" or "image shift" based on magnification
	$type = ($targetinfo['magnification']>2500 && $imginfo['magnification']>2500) ? "image shift" : "stage position";

	$targetcal = $leginondata->getImageMatrixCalibration($tId, $type);
	$parentcal = $leginondata->getImageMatrixCalibration($imageId, $type);
	$truedim=$targetinfo['targetdim'];
	#$msg .= 'target=('.$target[x].','.$target[y].'), parenttarget=('.$parent['targetx'].','.$parent['targety'].') ';
	if (abs($target[x]-$parentimginfo['targetx'])<5
		&& abs($target[y]-$parentimginfo['targety'])<5 ){
		$child_shown = true;
	} else {
		$child_shown = false;
	}
	$tn = $target['tnumber'];
	$ratioX = ($frame_size) ? $frame_size/$target['dimx'] : (($binning) ? 1/$binning : 1);
	$cx = $target['x']*$ratioX;
	$cy = $target['y']*$ratioX;
	$msg .= 'tId'.$tId;
	$angle = $targetcal['angle']-$parentcal['angle'];
	//pack as an array to return
	return array(array($cx,$cy,$angle,$truedim*$ratioX),$child_shown,$msg);
}

function getTraces($particlerun, $imageId) {
	require_once "inc/particledata.inc";
	$particledata = new particledata();
	return $particledata->getTracesFromImageId($particlerun, $imageId);
}
function getParticles($sessionId,$ptclsel,$newptcl,$imginfo,$binning) {
		require_once "inc/particledata.inc";
		require_once "inc/histogram.inc";
		$particledata = new particledata();
		$particlerun=$particledata->getLastParticleRun($sessionId);
		if ($ptclsel) {
			$particleruns=$particledata->getParticleRunIds($sessionId);
			foreach ($particleruns as $prun) {
				$particlerun=$prun['DEF_id'];
				if($ptclsel==$particlerun)
					break;
			}
		}
		$particleinfo=$particledata->getParticlesFromImageId($particlerun, $imginfo['imageId']);
		list($selectionparams)=$particledata->getSelectionParams($particlerun);
		if (!$diam) {
			$diam = $selectionparams['diam'];
		}
		$selectionparams['runId'] = $particlerun;
		$labeldata=array();
		$particlelabels =$particledata->getParticleLabels($particlerun);
		// --- parse particle params
		$threshold = false;
		// $parts only have one item (1) the first time particles are display. 
		// diameter scale need to be done at another place
		$parts=explode(";", $newptcl['info']);
		foreach ($parts as $k=>$part) {
			if ($k) {
				if ($particlelabels) {
					list($labelid, $setdiam, $thres1, $thres2) = explode(":", $part);
				} else {
					list($diam, $thres1, $thres2) = explode(":", $part);
				}
				$threshold = (is_numeric($thres1) && is_numeric($thres2)) ? true : false;
				$diam = ($setdiam) ? $setdiam:$diam;
				if (is_numeric($labelid)) {
					$labeldata[$labelid]=array('diam'=>$diam);
					if ($threshold) {
						$labeldata[$labelid]['thres1']=$thres1;
						$labeldata[$labelid]['thres2']=$thres2;
					}
				}
			}
		}

	return array($particleinfo,$selectionparams,$particlelabels,$labeldata);
}

function setParticleLabelParams($img,$particlelabels,$labeldata) {
	$labeldata_keys = array_keys($labeldata);
	$particlelabelparams=array();
	$particlelabelparams['msg']='';
	$particlelabelparams['color']=array();
	$particlelabelparams['diam']=array();
	$particlelabelparams['thres1']=array();
	$particlelabelparams['thres2']=array();
	//set particle color, diameter and threshold
	foreach ((array)$particlelabels as $index=>$particlelabel) {
		if (!in_array($index, $labeldata_keys)) {
			continue;
		}
		$text = $particlelabel['label'];
		$col = getParticleLabelColor($img, $index);
	$particlelabelparams['msg'] .= $col;
		$particlelabelparams['color'][$text]=$col;
		$particlelabelparams['diam'][$text]=$labeldata[$index]['diam'];
		$particlelabelparams['thres1'][$text]=$labeldata[$index]['thres1'];
		$particlelabelparams['thres2'][$text]=$labeldata[$index]['thres2'];
	}
	return $particlelabelparams;
}

function blankimage($w=256, $h="", $text="Failed") {
	if (!$h)
		$h=$w;
	$blkimg = imagecreate($w, $h);
	$background = imagecolorallocate($blkimg, 255, 255, 255);
	$textcolor = imagecolorallocate($blkimg, 0, 0, 255);
	imagestring($blkimg, 5, 2, 2, $text, $textcolor);
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
	header("Content-type: image/png");
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
	var $ratio = 4;
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

		if ($fromImg) {
			$img = $fromImg;
		} else {
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
				// use image dimension to calculate width and height in case
				// that the images are rectangular
				$src_w = $imageinfo[0]['dimx']/$ratio;
				$src_h = $imageinfo[0]['dimy']/$ratio;

				imagecopy($img, $gimg, $dst_x, $dst_y, $src_x, $src_y, $src_w, $src_h);
				imagedestroy($gimg);
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
		// Use this to add debug message
		#$debug_message = $this->size.' '.$squaresize.' '.$src_w;
		imagestring($img, 2, 10, 20, $debug_message, imagecolorallocate($img,0,255,255));
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

function particleLabelsColors() {
	return array (
		'ff0000',
		'00ff00',
		'0000ff',
		'ffff00',
		'ff00ff',
		'00ffff',
		'ff8f00',
		'008f08'
	);
}

function getParticleLabelColor($img, $index) {
	$colors = particleLabelsColors();
	$n=sizeof($colors);
	$index=$index%$n;
	$hexstr=$colors[$index];
	$int = hexdec($hexstr);
	return ImageColorAllocate ($img,
				0xFF & ($int >> 0x10),
				0xFF & ($int >> 0x8),
				0xFF & $int);
}

function setGroupColors($particleinfo,$img) {
		$d=array_map('getdiam', $particleinfo);
		$d=array_unique($d);
		$groupcolors=array();
		$index=0;
		foreach ((array)$d as $val) {
			$groupcolors[(int)$val]=getParticleColor($img, $index);
			$index++;
		}
	return $groupcolors;
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
