<?php
class imageUtil{

	/* return an array of x, y dimensions by the following rule
	 * when bin is set to auto:
	 * if either x or y bigger than 1024, then use 1024
	 * and resize the base on their ratio
	 * otherwise use their original image size.
	 * When binning has been set, find x, y by given binning.
	 */
	function getDefaultImageSize($isfft) {
		if ($isfft)
			// imcache size before fft
			return 4096;
		return 1024;
	}

	function getDefaultImageSourceSize($isfft) {
		if ($isfft)
			// final power spectrum imcache size
			return 1024;
		return $this->getDefaultImageSize(false);
	}

	function getResampleCoordinates($file_dimx,$file_dimy,$dimxy, $bin, $default_size) {
		//resample unbinned power spectrum to fake prefft bin
		$dimMax = max((int)$dimxy[0], (int)$dimxy[1]);
		$file_dimMax = max((int)$file_dimx, (int)$file_dimy);
		if ($bin == 'auto') {
			$bin = ($file_dimMax > $default_size) ? (int) ($file_dimMax / $default_size):1;
		}
		$center = $dimMax / 2;
		$start = $center - $dimMax /(2*$bin);
		return array((int) $start,(int) $start,(int) $dimxy[0]/$bin,(int) $dimxy[1]/$bin);
	}

	function imageBinning($dimx, $dimy, $bin, $default_size=1024){
		if($bin == 'auto'){
			$dimMax = max((int)$dimx, (int)$dimy);

			if($dimMax > $default_size){
				$xyRatio = $dimx / $dimy;
				switch($xyRatio){
					case ($xyRatio < 1):
						$dimy = $default_size;
						$dimx = $dimy * $xyRatio;
						break;
					default:
						$dimx = $default_size;
						$dimy = $dimx / $xyRatio;
						break;
				}
			}
		}
		else{
			$dimx = (int) ($dimx / $bin);
			$dimy = (int) ($dimy / $bin);
		}
		return array($dimx, $dimy);
	}

	// Fit the image into the frame size with aspect ratio preserved	
	function imageFitIn($dimx, $dimy, $frame_size){
		$ratio = max($dimx,$dimy) / $frame_size;
		//$ratio = $dimx / $frame_size;
		if ($ratio > 0) {
			$dimx = (int) ($dimx / $ratio);
			$dimy = (int) ($dimy / $ratio);
		} else {
			$dimx = $frame_size;
			$dimy = $frame_size;
		}
		return array($dimx, $dimy);
	}

	/*
	 * We need to convert the original min and max ratio
	 * to percentage. Original passed from web is between
	 * 0 to 255, so need to convert to between 
	 * 0 to 100
	 * return: an array of the percentage of scaleMin and scaleMax
	 */
	function scaleMinMaxConvert($min, $max){
		$min = (255/100) * $min;
		$max = (255/100) * $max;
		return array('minpix'=>$min, 'maxpix'=>$max);
	}

	function getDisplayPixelSize($calpixelsize,$camera_binning,$db_dimx,$display_dimx,$isfft=false,$fftbintype='b',$prefft_dimx=2048,$iscache=false) {
		if (!$isfft) {
			return $this->getRealSpaceDisplayPixelSize($calpixelsize,$camera_binning,$db_dimx,$display_dimx);
		} else {
			if ($iscache)
				// The default size saved in cache
				return $this->getCacheFFTDisplayPixelSize($calpixelsize,$camera_binning,$db_dimx,$display_dimx,$prefft_dimx);
			if ($fftbintype=='b') {
				return $this->getBinBeforeFFTDisplayPixelSize($calpixelsize,$camera_binning,$db_dimx,$display_dimx,$prefft_dimx);
			} else {
				return $this->getBinAfterFFTDisplayPixelSize($calpixelsize,$camera_binning,$db_dimx,$display_dimx);
			}
		}
	}

	function getRealSpaceDisplayPixelSize($calpixelsize,$camera_binning,$db_dimx,$display_dimx) {
		$ratio = $db_dimx / $display_dimx;
		$pixelsize = $calpixelsize*$camera_binning*$ratio;
		return $pixelsize;
	}

	function getCacheFFTDisplayPixelSize($calpixelsize,$camera_binning,$db_dimx,$display_dimx,$prefft_dimx) {
		$source_pixelsize = 1 / ($calpixelsize*$camera_binning*$db_dimx);
		$post_fft_binning = $prefft_dimx / $display_dimx;
		return  $source_pixelsize * $post_fft_binning;
	}

	function getBinBeforeFFTDisplayPixelSize($calpixelsize,$camera_binning,$db_dimx,$display_dimx,$prefft_dimx) {
		// result is in 1/m
		// This may still be wrong for 5120xany.  But it is more important to get
		// CacheFFTDisplayPixelSize right so I will leave it as is.
		$prefft_binning = $db_dimx / $prefft_dimx;
		return  1 / ($calpixelsize*$camera_binning*$prefft_binning*$display_dimx);
	}

	function getBinAfterFFTDisplayPixelSize($calpixelsize,$camera_binning,$db_dimx,$display_dimx) {
		// result is in 1/m
		return 1 / ($calpixelsize*$camera_binning*$display_dimx);
	}

	function makeBlankImageWithErrorMessage($error_text) {
		$img = blankimage(512);
		$error_text_array = (is_array($error_text)) ? $error_text: array($error_text);
		$yoffset = 31;
		foreach ($error_text_array as $text) {
			imagestring($img, 4, 21, $yoffset, $text, imagecolorallocate($img,0,0,255));
			$yoffset += 20;
		}
		return $img;
	}
}
?>
