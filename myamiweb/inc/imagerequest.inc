<?php
require_once dirname(__FILE__).'/../config.php';
require_once 'inc/redux.inc';

class imageRequester {
	// filepath is the full path to file ex: /a/b/c.d
	// filename is the base name of file path ex: c.d
	// fileroot is the root name of the filename ex: c
	function requestImage($filepath,$oFormat,$shape=array(512,512),$scaleType='stdev',$scaleMin=-5,$scaleMax=5,$lpf=0,$rgb=false,$power=false,$cacheOff=false,$frame=false,
							$overlay='', $overlayColor=0.35) 
	{
		if (empty($filepath)) return false;
		$redux = new redux($filepath, $oFormat);
		$redux->setPipeline('standard');
		$redux->setScaleType($scaleType);
		$redux->setShape($shape);
		$redux->setScaleMin($scaleMin);
		$redux->setScaleMax($scaleMax);
		$redux->setPadShape(array($_POST['padShapeX'], $_POST['padShapeY']));
		$redux->setPadPos(array($_POST['padPosX'], $_POST['padPoxY']));
		$redux->setPadValue($_POST['padValue']);
		$powerValue = ($power == false) ? false : true;
		$cacheOffValue = ($cacheOff == false) ? false : true;
		$rgbValue = ($rgb == false) ? false : true;
		$redux->setPower($powerValue);
		$redux->setCacheOff($cacheOffValue);
		if ($powerValue) $maskRadius = 0.01 * $shape[0];
		$redux->setMaskRadius($maskRadius);
		$redux->setLpf($lpf);
		$redux->setRGB($rgbValue);
		$redux->setFrameValue($frame);
		$redux->setOverlay($overlay);
		$redux->setOverlayColor($overlayColor);

//		$errMsg = $redux->getErrMsg();
//		if(!empty($errMsg)){
//			echo "Error requesting image from redux: padvalue-> ";
//			echo $_POST['padValue'];
//			echo "  maskRaduis-> ". $maskRadius;
//			echo " shape-> ";
//			print_r($shape);
//			print_r($errMsg);
//			exit;
//		}

		$reply = $redux->requestImage();
		return $reply;
	}

	function requestInfo($filepath,$frame=0) {
		if (empty($filepath) || !is_file($filepath)) return false;
		$redux = new redux($filepath, 'JSON');
		$redux->setFrameValue($frame);
		$redux->setInfo(true);

		$errMsg = $redux->getErrMsg();
		$reply = $redux->requestImage();
		$infoclass = json_decode($reply);
		return $infoclass;
	}

	function requestDefaultFullImage($filepath,$oformat,$fft=false) {
		// Used so far only in downloading image
		$imginfo = $this->requestInfo($filepath);
		$pmin = $imginfo->amin;
		$pmax = $imginfo->amax;
		$height = $imginfo->ny;
		$width = $imginfo->nx;
		$xyDim = array($width,$height);
		return $this->requestImage($filepath,$oformat,$xyDim,'stdev',-5,5,0,false,(bool)$fft,false,false);
	}
	function requestHistdata($filepath,$number_of_bins,$min,$max) {
		if (empty($filepath)) return false;
		$redux = new redux($filepath, 'JSON');
		$redux->setPipeline('histdata');
		$redux->setHistBins($number_of_bins);
		$redux->setHistMin($min);
		$redux->setHistMax($max);

		$errMsg = $redux->getErrMsg();
		$reply = $redux->requestImage();
		$infoclass = json_decode($reply);
		return $infoclass;
	}

	function displayPNGString($imgstr,$fileroot='') {
		$filename = $fileroot.'.png';
		$img = imagecreatefromstring($imgstr);
		$this->displayImageObj($img,'PNG','',$filename);
	}

	function displayImageObj($img,$format='JPEG',$quality=80,$filename='') {
		if ($format == 'jpg') $format = 'JPEG';
		$type = strtolower($format);

		header("Content-type: image/$type");
		if ($filename)
			//filename for downloading
			header( "Content-Disposition: inline; filename=".$filename);
		
		if (strtoupper($format) == 'PNG')
			imagepng($img);
		if (strtoupper($format) == 'JPEG')
			imagejpeg($img,NULL,$quality);
		
		imagedestroy($img);
	}

	function displayJPEGString($imgstr,$fileroot='') {
		$filename = $fileroot.'.jpg';
		$img = imagecreatefromstring($imgstr);
		$this->displayImageObj($img,'JPEG',80,$filename);
	}

	function displayImageString($imgstr,$format,$filepath='') {
		$pathinfo = pathinfo($filepath);
		$fileroot = $pathinfo['filename'];
		if ($format == 'jpg') $format = 'JPEG';
		if (strtoupper($format) == 'JPEG') $this->displayJPEGString($imgstr,$fileroot);
		elseif (strtoupper($format) == 'PNG') $this->displayPNGString($imgstr,$fileroot);
	}

}
?>
