<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */


function drawcross ($img, $cx, $cy, $size, $col) {
	imagearc($img, $cx, $cy, $size, $size, 0, 360, $col);
	imageline($img, $cx-$size, $cy, $cx+$size, $cy, $col);
	imageline($img, $cx, $cy-$size, $cx, $cy+$size, $col);
}

function drawsquare($img, $squarepoints, $col) {
	$npoints=count($squarepoints)/2;
	imagepolygon($img, $squarepoints, $npoints, $col);
	return true;
}

function getsquarepoints($cx, $cy, $angle, $size) {
	$square = new square($cx, $cy, $size);
	$squarepoints = $square->getRotatedPointCoords($angle);
	return $squarepoints;
}

function imagestringshadow($img, $size, $cx, $cy, $text, $col, $colshadow="") {
	if (empty($colshadow)) 
		$colshadow = imagecolorallocate($img, 0, 0, 0); 
	imagestring($img, $size, $cx+1, $cy+1, $text, $colshadow);
	imagestring($img, $size, $cx, $cy, $text, $col);
}

class graphutil {

	function translatePoint(&$x,&$y,$angle,$cx,$cy)
	{
	   $x -= $cx;
	   $y -= $cy;

	   $new_x = $x * cos($angle) - $y * sin($angle);
	   $new_y = $x * sin($angle) + $y * cos($angle);
	   $x = $new_x+ $cx;
	   $y = $new_y + $cy;
	}

	function rotatePoly($pointarray, $angle, $cx, $cy)
	{
	   $rotatedpoly = Array();
	   while(count($pointarray) > 1)
	   {
	       $temp_x = array_shift($pointarray);
	       $temp_y = array_shift($pointarray);
	       $this->translatePoint($temp_x, $temp_y, $angle, $cx, $cy);
	       array_push($rotatedpoly, $temp_x);
	       array_push($rotatedpoly, $temp_y);
	   }
	   return $rotatedpoly;
	}
}

class square extends graphutil {

	function square($cx,$cy, $dim) {
		$this->cx=$cx;
		$this->cy=$cy;
		$this->points = $this->getSquarePoints($cx,$cy, $dim);
	}

	function getPointCoords() {
		return $this->points;
	}

	function getRotatedPointCoords($angle) {
		return $this->rotatePoly($this->points, $angle, $this->cx, $this->cy);
	}

	function getSquarePoints($cx, $cy, $squaredim) {
		$hs = $squaredim/2;
		$squarepoints = array (
			$cx-$hs, $cy-$hs,
			$cx+$hs, $cy-$hs,
			$cx+$hs, $cy+$hs,
			$cx-$hs, $cy+$hs
		);
		return $squarepoints;
	}
}

class arrow extends graphutil {

	var $arrow_data = array ();
	var $size = 5;

	function arrow($img, $x1,$y1, $x2, $y2, $col) {
		$this->img = $img;
		$this->col = $col;
		$this->x1 = $x1;
		$this->x2 = $x2;
		$this->y1 = $y1;
		$this->y2 = $y2;
		$this->angle = atan2(($y2-$y1), ($x2-$x1));
		$this->arrowPoints($x2, $y2);
		$this->arrow_data = $this->rotatePoly($this->arrow_data, $this->angle, $x2, $y2);
	}

	function setSize($size) {
		$this->size = $size;
	}

	function draw() {
		imageline($this->img, $this->x1, $this->y1, $this->x2, $this->y2, $this->col);
		imageline($this->img, $this->x1-.5, $this->y1+.5, $this->x2-.5, $this->y2+.5, $this->col);
		imagefilledpolygon ($this->img, $this->arrow_data, count($this->arrow_data)/2, $this->col);
	}

	function arrowPoints($x, $y) {
		$this->arrow_data = array (
					$x-2*$this->size, $y+$this->size,
					$x-2*$this->size, $y-$this->size,
					$x, $y
				);
	}

}
?>
