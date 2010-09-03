<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

$pick_colors = array (
	'ff0000',
	'00ff00',
	'0000ff',
	'ffff00',
	'ff00ff',
	'00ffff',
	'808000',
	'ff8080'
);

function imagecolorallocatehex($img, $c) {
	/* return a color from hex string: 
		FFFFF
		ABC
		#FFFFF
		#ABC
	*/
        $c= ereg_replace('^\#','',$c);
        switch (strlen($c)) {
                case 3:
                        $s = preg_split('//', $c, -1, PREG_SPLIT_NO_EMPTY);
                        $r = hexdec($s[0].=$s[0]);
                        $g = hexdec($s[1].=$s[1]);
                        $b = hexdec($s[2].=$s[2]);
                        break;
                case 6:
                        $r = hexdec(substr($c, 0, 2));
                        $g = hexdec(substr($c, 2, 2));
                        $b = hexdec(substr($c, 4, 2));
                        break;
                default:
                        $r = 0;
                        $g = 0;
                        $b = 0;
                        break;
        }
        return imagecolorallocate($img, $r, $g, $b);
}

function drawcross ($img, $cx, $cy, $size, $col, $arc=true, $angle=0, $shadow=false) {

	$angle = ($angle*2/360+1/4)*PI();
	$square = new square($cx, $cy, $size);
	$sp = $square->getRotatedPointCoords($angle);
	$npoints=count($sp)/2;
	if ($shadow) {
		imageline($img, $sp[0]+1, $sp[1], $sp[4]+1, $sp[5], 0);
		imageline($img, $sp[2]+1, $sp[3], $sp[6]+1, $sp[7], 0);
		if ($arc)
			imagearc($img, $cx+1, $cy, $size, $size, 315, 135, 0);
	}
	if ($arc)
		imagearc($img, $cx, $cy, $size, $size, 0, 360, $col);
	imageline($img, $sp[0], $sp[1], $sp[4], $sp[5], $col);
	imageline($img, $sp[2], $sp[3], $sp[6], $sp[7], $col);
}

function drawbox($img, $cx, $cy, $size, $col, $angle=0, $shadow=false) {
		$square = new square($cx, $cy, $size);
		$squarepoints = $square->getRotatedPointCoords($angle);
		if ($shadow) {
			foreach ($squarepoints as $k=>$v)
				$squarepoints[$k] += 1;
			drawsquare($img, $squarepoints, 0);
		}
		drawsquare($img, $squarepoints, $col);
}

function drawsquare($img, $squarepoints, $col) {
	if (!is_array($squarepoints))
		return;
	$npoints=count($squarepoints)/2;
	imagepolygon($img, $squarepoints, $npoints, $col);
	return true;
}

function drawcircle($img, $cx, $cy, $size, $col, $shadow=false) {
	if ($shadow)
		imagearc($img, $cx+1, $cy+1, $size, $size, 315, 135, 0);
	imagearc($img, $cx, $cy, $size, $size, 0, 360, $col);
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


function translatePolygon($cx, $cy, &$polygon) {
	foreach ($polygon as $k=>$p) {
			if ($k % 2 ==0)
				$polygon[$k] += $cx;
			else
				$polygon[$k] += $cy;
	}
}

function polygon2points($data) {
	$points=array();
	for($i=0; $i<count($data); $i+=2) {
		$x=$data[$i];
		$y=$data[$i+1];
		$points[] = new Point2D($x,$y);
	}
		return $points;
}

function getPolarCoord($x,$y) {
	return array(
			'r'=>sqrt($x*$x+$y*$y),
			'angle'=>atan2($y,$x)
		);
}

function getCartesianCoord($r, $angle) {
	return array(
			'x'=>$r*cos($angle),
			'y'=>$r*sin($angle)
		);
}

// --- return true if ($x,$y) in polygon delimited by $data
function insidePolygon($x, $y, $data) {
	$p = polygon2points($data);
	$n = count($p);
  $i = $j = 0;
	$c = false;
  for ($i = 0, $j = $n-1; $i < $n; $j = $i++) {
    if (((($p[$i]->y<$y) && ($y<$p[$j]->y)) ||
         (($p[$j]->y<$y) && ($y<$p[$i]->y))) &&
        ($x < ($p[$j]->x - $p[$i]->x) * ($y - $p[$i]->y) / ($p[$j]->y - $p[$i]->y) + $p[$i]->x))
      $c = !$c;
  }
  return $c;
}

function getPolygonArea($points) {
	$n=count($points);
	foreach($points as $i=>$point) {
		$j = ($i + 1) % $n;
		$area += $points[$i]->x * $points[$j]->y;
		$area -= $points[$i]->y * $points[$j]->x;
   }
   $area /= 2;
   return($area < 0 ? -$area : $area);
}

function getPolygonCenter($data) {
	$cx=0;
	$cy=0;
	$points = polygon2points($data);
	$n = count($points);
	if(!$area = getPolygonArea($points))
		return;
	$factor=0;
	for ($i=0;$i<$n;$i++) {
		$j = ($i + 1) % $n;
		$factor=($points[$i]->x*$points[$j]->y-$points[$j]->x*$points[$i]->y);
		$cx+=($points[$i]->x+$points[$j]->x)*$factor;
		$cy+=($points[$i]->y+$points[$j]->y)*$factor;
	}
	$area*=6;
	$factor=1/$area;
	$cx*=$factor;
	$cy*=$factor;
	return array('cx'=>$cx, 'cy'=>$cy);
}

function getVectors($polygon) {
	$points = polygon2points($polygon);
	$n = count($points);
	$x = $points[$n-1]->x;
	$y = $points[$n-1]->y;
	$vectors=array();
	foreach($points as $p) {
			$cur_x = $p->x;
			$cur_y = $p->y;
			$vectors[] = getPolarCoord($x-$cur_x,$y-$cur_y);
			$x = $cur_x;
			$y = $cur_y;
	}
	return $vectors;
}

function getMaxVector($vectors) {
		
		foreach ($vectors as $k=>$vector) {
				$r = $vector['r'];
				$max_r = max($r ,$max_r);
		}
		foreach ($vectors as $k=>$vector) {
				$r = $vector['r'];
				if ($r==$max_r)
						break;
		}

		return $vectors[$k];
}

class Point2D {
	var $x,$y;
	function Point2D($x,$y) {
		$this->x=$x;
		$this->y=$y;
	}
}
?>
