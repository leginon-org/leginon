<?php
class square {

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
			/*
			add an arrow
			$cx-$hs, $cy-$hs,
			$cx, $cy-$hs,
			$cx, $cy-$hs-15,
			$cx-5, $cy-$hs-10,
			$cx, $cy-$hs-15,
			$cx+5, $cy-$hs-10,
			$cx, $cy-$hs-15,
			$cx, $cy-$hs,
			*/
			$cx-$hs, $cy-$hs,
			$cx+$hs, $cy-$hs,
			$cx+$hs, $cy+$hs,
			$cx-$hs, $cy+$hs
		);
		return $squarepoints;
	}

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
	   $rotatedpoly= Array();
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
?>
