<?php
require_once "inc/graphutil.inc";
require_once "inc/scalebar.inc";
require_once "inc/scalering.inc";
// gd functions to add graphic to an image

class imageOverlay {

	function __construct($img) {
		$this->setImage($img);
		$this->setColors();
	}

	function setImage($image) {
		$this->img = $image;
		#$this->setColors();	
	}

	function setColors() {
		$this->white = imagecolorallocate($this->img, 255, 255, 255);
		$this->blue = imagecolorallocate($this->img, 0, 255, 255);
		$this->yellow= imagecolorallocate($this->img, 255, 255, 0);
		$this->red = imagecolorallocate($this->img, 255,0,0);
	}

	function addScaleBar($pixelsize,$xyDim) {
		if ($pixelsize) {
			$size = ($xyDim[0]) ? $xyDim[0]: 1;
			$value = $pixelsize;
			$scalebar = new ScaleBar($this->img, $size, $value);
			$scalebar->display();
		}
	}

	function addScaleRing($fftpixelsize,$xyDim,$fftbin) {
		if ($fftpixelsize) {
			$size = ($xyDim[0]) ? $xyDim[0]: 1;
			//value is the pixelsize in Fourier space in 1/meters
			$value = $fftpixelsize;
			$scalebar = new ScaleRing($this->img, $size, $value);
			$scalebar->display();
		}
	}

	function drawTarget($params,$child_shown,$targettype) {
		$cx = $params[0];
		$cy = $params[1];
		$angle = $params[2];
		$length = $params[3];
		if ($child_shown) {
			$col = $this->blue;
			$crosscol = $this->yellow;
		} else {
			$col = $this->white;
			$crosscol = $this->white;
		}
		if ($targettype == 'acq') {
			$squarepoints = getsquarepoints($cx, $cy, $angle, $length);
			drawsquare($this->img, $squarepoints, $crosscol);
		} else {
			$col = ($targettype == 'focus') ? $this->blue : $this->white;
			drawcross($this->img, $cx, $cy, $length*0.5, $col, false, 0, true);
			drawcircle($this->img, $cx, $cy, $length*0.2, $col, true);
		}
	}

}

?>
