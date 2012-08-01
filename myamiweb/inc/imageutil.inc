<?php
class imageUtil{

	/* return an array of x, y dimensions by the following rule
	 * when bin is set to auto:
	 * if either x or y bigger than 1024, then use 1024
	 * and resize the base on their ratio
	 * otherwise use their original image size.
	 * When binning has been set, find x, y by given binning.
	 */
	function getDefaultImageSize($isfft,$binorder) {
		if ($isfft && $binorder == 'b')
			return 2048;
		return 1024;
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

	function getDisplayPixelSize($calpixelsize,$camera_binning,$db_dimx,$display_dimx,$isfft=false,$fftbintype='b',$prefft_dimx=2048) {
		if (!$isfft) {
			return $this->getRealSpaceDisplayPixelSize($calpixelsize,$camera_binning,$db_dimx,$display_dimx);
		} else {
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
	function getBinBeforeFFTDisplayPixelSize($calpixelsize,$camera_binning,$db_dimx,$display_dimx,$prefft_dimx) {
		// result is in 1/m
		$prefft_binning = $db_dimx / $prefft_dimx;
		return  1 / ($calpixelsize*$camera_binning*$prefft_binning*$display_dimx);
	}

	function getBinAfterFFTDisplayPixelSize($calpixelsize,$camera_binning,$db_dimx,$display_dimx) {
		// result is in 1/m
		return 1 / ($calpixelsize*$camera_binning*$display_dimx);
	}
}
?>
