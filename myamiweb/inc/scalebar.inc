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

	var $rec_scales = array (
			// This is hacked so that a value of 1e-9 distance from center 
			// to corresponds to 1 nm-1 so it is best expressed in nm-1 unit
			// The unit subscript of "-1" is added during display
			'100 um'  => 1e-10,
			'200 um'  => 2e-10,
			'500 um'  => 5e-10,
			'1 nm'  => 1e-9,
			'2 nm'  => 2e-9,
			'5 nm'  => 5e-9,
			'10 nm'  => 10e-9,
			'20 nm'  => 20e-9,
			'50 nm'  => 50e-9,
			'100 nm'  => 100e-9,
			'200 nm'  => 200e-9,
			'500 nm'  => 500e-9
		);

	var $labelfontsize=4;
	var $offsetbarX=10;
	var $offsetbarY=20;

	function __construct($img, $size, $value, $imgheight=0, $is_diffraction=false) {
		// --- value should be in meter --- //
		if ($imgheight==0) $imgheight=$size;
		$this->img = $img;
		$this->size = $size;
		$this->imgheight = $imgheight;
		$this->value = $value;
		$this->is_diffraction = $is_diffraction;
		$this->findScale();
		$this->setColor(255,255,255);
	}


	function findScale() {
		$this->nbpixels = 0;
		$label = "";
		if (!$this->value)
			$this->value = 1;
		$scales_used = ($this->is_diffraction) ? $this->rec_scales: $this->scales;
		foreach ($scales_used as $this->label=>$scale) {
			$this->nbpixels = $scale/$this->value;
			$r = $this->size/$this->nbpixels;
			if ($r > 2 && $r <5) {
				break;
			}
		}
		if ($this->nbpixels <1) {
			$this->label = $this->value;
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
		$h = ($h) ? $h : $this->imgheight;
		$offsetbarlabelX = $this->offsetbarX + $this->nbpixels/2;
		
		$offsetbarlabelY = $h - $this->offsetbarY - $this->labelfontsize * 4;
		if ($this->labelfontsize<3) {
			$offsetbarlabelY -= 4;
		}
		$barX1 = $this->offsetbarX;
		$barX2 = $this->nbpixels+$this->offsetbarX;
		$barY1 = $h-$this->offsetbarY;
		$barY2 = $h-$this->offsetbarY+1;
		if ($this->size > 2000) {
		    $this->labelfontsize = 85;
		    $barY2 = $barY2 + 10;
		    $font = dirname(__FILE__).'/fonts/DejaVuSans-Bold.ttf';
		    imagettftext($this->img, $this->labelfontsize, 0,  $offsetbarlabelX, $offsetbarlabelY-100, $this->color, $font, $this->label);
				if ($this->is_diffraction) {
					// add inverse sign to diffraction scale
					$extra_xoffset = strlen($this->label)*$this->labelfontsize*1;
					imagettftext($this->img, $this->labelfontsize*0.7, 0,  $offsetbarlabelX+$extra_xoffset, $offsetbarlabelY-100-$this->labelfontsize*0.5, $this->color, $font, "-1");
				}
		    # main bar
		    imagefilledrectangle($this->img,$barX1+100, $barY1-100, $barX2+100, $barY2-100,$this->color);
		    
		}
		else{
    		$black = imagecolorallocate($this->img, 0, 0, 0);
    		imagestring($this->img, $this->labelfontsize, $offsetbarlabelX+1,
    			$offsetbarlabelY+1, $this->label,$black);
    		imagestring($this->img, $this->labelfontsize, $offsetbarlabelX,
    			$offsetbarlabelY, $this->label,$this->color);
				if ($this->is_diffraction) {
					$extra_xoffset = strlen($this->label)*$this->labelfontsize*2;
					// add inverse sign to diffraction scale
					imagestring($this->img, $this->labelfontsize*0.8, $offsetbarlabelX+1+$extra_xoffset,
						$offsetbarlabelY+1-$this->labelfontsize*0.5, '-1',$black);
					imagestring($this->img, $this->labelfontsize*0.8, $offsetbarlabelX+$extra_xoffset,
						$offsetbarlabelY-$this->labelfontsize*0.5, '-1',$this->color);
				}
    		ImageRectangle($this->img,$barX1-1, $barY1, $barX2+1, $barY2+1,$black);
    		ImageRectangle($this->img,$barX1, $barY1, $barX2, $barY2,$this->color);
		}
	}
}
?>
