<?php
// Fourier space resolution ring scale, equivalent to scalebar.inc in real space
class ScaleRing {

	var $scales = array (
			'1A'  => 1e-10,
			'2A'  => 2e-10,
			'4A'  => 4e-10,
			'7A'  => 7e-10,
			'1nm'  => 1e-9,
			'2nm'  => 2e-9,
			'4nm'  => 4e-9,
			'7nm'  => 7e-9,
			'10nm'  => 10e-9,
			'20nm'  => 20e-9,
			'40nm'  => 40e-9,
			'70nm'  => 70e-9,
			'100nm'  => 100e-9,
			'200nm'  => 200e-9,
			'400nm'  => 400e-9,
			'700nm'  => 700e-9,
			'1um'  => 1e-6,
			'2um'  => 2e-6,
			'4um'  => 4e-6,
			'7um'  => 7e-6,
			'10um' => 10e-6,
			'20um' => 20e-6,
			'40um' => 40e-6,
			'70um' => 70e-6,
			'100um' => 100e-6,
			'200um' => 200e-6,
			'400um' => 400e-6,
			'700um' => 700e-6,
			'1mm' => 1e-3,
			'2mm' => 2e-3,
			'4mm' => 4e-3,
			'7mm' => 7e-3
		);

	var $labelfontsize=4;
	var $offsetbarX=10;
	var $offsetbarY=20;

	function ScaleRing($img, $size, $value) {
		// --- value should be in meter --- //
		$this->img = $img;
		$this->size = $size;
		$this->value = $value;
		$this->findScale();
		$this->setColor(255,255,255);
	}


	function findScale() {
		$this->nbpixels = 0;
		$label = "";
		if (!$this->value)
			$this->value = 1;
		#echo "size=".$this->size." res-limit=".$this->value." ";
		foreach ($this->scales as $this->label=>$scale) {
			$this->nbpixels = ($this->size * $this->value) / (2 * $scale);
			#echo "for ".$this->label." nbpixels=".$this->nbpixels." ****";
			$r = $this->size/$this->nbpixels;
			if ($r > 2 && $r < 4) {
				break;
			}
		}
	}

	function setColor($r, $v, $b) {
		$this->color = imagecolorallocate($this->img, $r, $v, $b);
	}

	function setFontSize($v) {
		$this->labelfontsize = $v;
	}

	function setoffsetlabelX($v) {
		$this->offsetlabelX = $v;
	}

	function setoffsetlabelY($v) {
		$this->offsetlabelY = $v;
	}

	function display($h="") {
		// --- display label / scale bar
		$h = ($h) ? $h : $this->size;
		$direction = 1;
		if ($this->nbpixels > $h/2 - 6 * $this->labelfontsize)
			$direction = -1;
		$offsetringlabelX = floor($h/2 + $this->offsetlabelX + 0.75 * $this->nbpixels);
		
		$offsetringlabelY = floor($h/2 - $this->offsetlabelY + 0.70 * $this->nbpixels);
		if ($this->labelfontsize<3) {
			$offsetringlabelY -= 4;
		}

		$blue = imagecolorallocate($this->img, 0, 0, 255);
		drawcircle($this->img, $h/2, $h/2, 2*$this->nbpixels, $this->color, true);
		imagestring($this->img, $this->labelfontsize, $offsetringlabelX,
			$offsetringlabelY, $this->label,$this->color);
		drawcircle($this->img, $h/2, $h/2, 2*($this->nbpixels+1), $blue, true);
		imagestring($this->img, $this->labelfontsize, $offsetringlabelX+1,
			$offsetringlabelY+1, $this->label,$blue);
	}
}
?>
