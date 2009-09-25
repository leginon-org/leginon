<?php
class ScaleBar {

	var $scales = array (
			'1nm'  => 1e-9,
			'2nm'  => 2e-9,
			'5nm'  => 5e-9,
			'10nm'  => 10e-9,
			'20nm'  => 20e-9,
			'50nm'  => 50e-9,
			'100nm'  => 100e-9,
			'200nm'  => 200e-9,
			'500nm'  => 500e-9,
			'1um'  => 1e-6,
			'2um'  => 2e-6,
			'5um'  => 5e-6,
			'10um' => 10e-6,
			'20um' => 20e-6,
			'50um' => 50e-6,
			'100um' => 100e-6,
			'200um' => 200e-6,
			'500um' => 500e-6,
			'1mm' => 1e-3,
			'2mm' => 2e-3,
			'5mm' => 5e-3
		);

	var $labelfontsize=4;
	var $offsetbarX=10;
	var $offsetbarY=20;

	function ScaleBar($img, $size, $value) {
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
		foreach ($this->scales as $this->label=>$scale) {
			$this->nbpixels = $scale/$this->value;
			$r = $this->size/$this->nbpixels;
			if ($r > 2 && $r <5) {
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

	function setoffsetbarX($v) {
		$this->offsetbarX = $v;
	}

	function setoffsetbarY($v) {
		$this->offsetbarY = $v;
	}

	function display($h="") {
		// --- display label / scale bar
		$h = ($h) ? $h : $this->size;
		$offsetbarlabelX = $this->offsetbarX + $this->nbpixels/2;
		
		$offsetbarlabelY = $h - $this->offsetbarY - $this->labelfontsize * 4;
		if ($this->labelfontsize<3) {
			$offsetbarlabelY -= 4;
		}
		$barX1 = $this->offsetbarX;
		$barX2 = $this->nbpixels+$this->offsetbarX;
		$barY1 = $h-$this->offsetbarY;
		$barY2 = $h-$this->offsetbarY+1;

		$black = imagecolorallocate($this->img, 0, 0, 0);
		imagestring($this->img, $this->labelfontsize, $offsetbarlabelX+1,
			$offsetbarlabelY+1, $this->label,$black);
		imagestring($this->img, $this->labelfontsize, $offsetbarlabelX,
			$offsetbarlabelY, $this->label,$this->color);
		ImageRectangle($this->img,$barX1-1, $barY1, $barX2+1, $barY2+1,$black);
		ImageRectangle($this->img,$barX1, $barY1, $barX2, $barY2,$this->color);
	}
}
?>
