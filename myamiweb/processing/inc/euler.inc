<?php

function location3d($a, $b, $c) {
	return array('a'=>$a, 'b'=>$b, 'c'=>$c);
}

function getMatrix($b, $c, $a) {
	//the matrix to represent the euler rotations
	$v[0][0] = round(cos($c)*cos($a)-cos($b)*sin($a)*sin($c),4);
	$v[0][1] = round(cos($c)*sin($a)+cos($b)*cos($a)*sin($c),4);
	$v[0][2] = round(sin($c)*sin($b),4);
	$v[1][0] = round(-sin($c)*cos($a)-cos($b)*sin($a)*cos($c),4);
	$v[1][1] = round(-sin($c)*sin($a)+cos($b)*cos($a)*cos($c),4);
	$v[1][2] = round(cos($c)*sin($b),4);
	$v[2][0] = round(sin($b)*sin($a),4);
	$v[2][1] = round(-sin($b)*cos($a),4);
	$v[2][2] = round(cos($b),4);
	return $v;
}

function calculatePoint($eulers) {
	//the angles rotate a certain vector around the origin
	//this method uses p to store the vector 
	//p is the vector (0,0,1)
	$p = array(0,0,1);
	// rotate for zxz convention

	/*the method is:
	 *create a matrix to represent the euler rotations
	 *multiply the matrix by the vector or 1*3 matrix
	 *take the resulting matrix and put it into xyz form (Location3D)
	 **/
	
	// v is a matrix found at the wiki page:
	// http://en.wikipedia.org/wiki/Euler_angles
	$v = getMatrix($eulers['a'], $eulers['b'], $eulers['c']);
	
	
	//mutliplication of the 3*3 matrix by the 1*3 vector
	$loc = array(
		'x'=> ($p[0]*$v[0][0] + $p[1]*$v[0][1] + $p[2]*$v[0][2]),
		'y'=> ($p[0]*$v[1][0] + $p[1]*$v[1][1] + $p[2]*$v[1][2]), 
		'z'=> ($p[0]*$v[2][0] + $p[1]*$v[2][1] + $p[2]*$v[2][2]),
	);
	return $loc;//return the point
}

function multiply($a, $b) {
	for($i = 0; $i<count($a); $i++) {
		for($j = 0; $j<count($b[0]); $j++) {
			$sum = 0;
			for($k = 0; $k<count($a[$i]); $k++)
				$sum+=$a[$i][$k]*$b[$k][$j];
			$c[$i][$j] = $sum;
		}
	}
	return $c;
}	

function trace($d) {
	$sum = 0;
	for($i = 0; $i<count($d); $i++) {
		$sum = $sum+$d[$i][$i];
	}
	return $sum;
}

function transpose($d) {
	for($i = 0; $i<count($d); $i++)
		for($j = 0; $j<count($d[$i]); $j++)
			$result[$i][$j] = $d[$j][$i];
	return $result;
}

function calculateDistance($e1,$e2) {
	//two matricies to represent the eulers
	$v1 = getMatrix($e1['a'], $e1['b'], $e1['c']);
	$v2 = getMatrix($e2['a'], $e2['b'], $e2['c']);
	$r = multiply(transpose($v1),$v2);
	$trace = trace($r);
	$s = ($trace-1)/2.0;
	if($s < -.95 && $s>-1.05)
		return 3.14159;
	else if($s > .95 && $s<1.05)
		return 0;
	else {
		$theta = acos($s);
		$d = abs($theta/(2*sin($theta)))*sqrt(pow($r[0][1]-$r[1][0],2)+pow($r[0][2]-$r[2][0],2)+pow($r[1][2]-$r[2][1],2));
		return $d;
	}
}

function getDifferences($e1s,$e2s) {
	//differences stores the numbers
	//temp is the list of eulers from the euler being compared to
	//a counter of the spot in the list
	$count = 0;
	$differences = array();
	while($count<count($e1s) && $count<count($e2s)) {
		//count is in range of list
		//add distance onto list and update count
		$differences[$count] = (calculateDistance($e1s[$count],$e2s[$count]));
		$count++;
	}
	return $differences;
}

function meanDifference($e1s,$e2s) {
	//temp is the list of eulers from the euler being compared to
	//the total and count to calculate average
	$total = 0;
	$count = 0;
	while($count<count($e1s) && $count<count($e2s)) {
		//count is in range of list
		//add another distance and update count
		$total += calculateDistance($e1s[$count], $e2s[$count]);
		$count++;
	}
	//formula for average is total/(# of elements)
	return $total/$count;
}

function getStats($recon,$iter1,$iter2,$e1s,$e2s) {
	$errors = array();
	$std = 0;
	$termsSquared = 0;
	$terms = 0;
	$count = 0;
	$error = 0;
	$min = 99999999;
	$max = -99999999;
	while($count<count($e1s) && $count<count($e2s))//count is in range of list
	{
		$distance = calculateDistance($e1s[$count], $e2s[$count]);
		if($min>$distance)
			$min = $distance;
		if($max<$distance)
			$max = $distance;
		$errors[] = $distance;
		$terms = $terms+$distance;
		$termsSquared = $termsSquared+($distance*$distance);
		$count++;
	}
	$std = (1.0/$count)*sqrt($count*($termsSquared) - $terms*$terms);
	$theStats = new Statistics($recon,$iter1,$iter2,$terms/$count, $std, $min, $max,$errors,$e1s,$e2s); 
	return $theStats;
}

class Statistics {
	var $myReconId = 0;
	var $myIterId1 = 0;
	var $myIterId2 = 0;
	var $myMean = 0;
	var $myStandardDeviation = 0;
	var $myMin = 0;
	var $myMax = 0;
	var $myData = array();
	var $eulers1 = array();
	var $eulers2 = array();
	function Statistics($recon,$iter1,$iter2,$mean,$std,$min,$max,$data,$e1,$e2) {
		$this->myReconId= $recon;
		$this->myIterId1= $iter1;
		$this->myIterId2= $iter2;
		$this->myMean = $mean;
		$this->myStandardDeviation = $std;
		$this->myMin = $min;
		$this->myMax = $max;
		$this->myData = $data;
		$this->eulers1 = $e1;
		$this->eulers2 = $e2;
	}
}

//writes an image to a file with a trianlge with points $eulers drawn on it
function createTriangle($eulers) {	
	$max = yMax($eulers);
	echo "Max: ".$max."\n";
	$maxArray = array_fill(0,count($eulers),$max);
	$points = array_map("changePoint", $eulers, $maxArray);
	$points = array_map("roundForHistogram",$points);
	$map = calculateFrequency($points);
	$myImage = drawImage($points, $map);
	return $myImage;
}

function calculateFrequency($points) {
	$map = array();
	foreach($points as $point) {
		$index = round($point['x']*500*$point['y'],1);
		if($map[$index])
			$map[$index]++;
		else
			$map[$index] = 1;
	}
	return $map;
}
function roundForHistogram($point) {
	$point['x'] = round($point['x'],2);
	$point['y'] = round($point['y'],2);
	return $point;
}

function yMax($eulers) {
	$max = -999999;
	foreach($eulers as $e) {
		$n = $e['b'];
		if($n>$max)
			$max = $n;
	}
	return $max;
}

function changePoint($euler,$max) {
	$euler['b'] -= $max/2;
	$n = calculatePoint($euler);
	$r = sqrt($n['x']*$n['x'] + $n['y']*$n['y'] + $n['z']*$n['z']);
	if($n['x']==0)
		$theta = pi()/2;
	else
		$theta = atan($n['y']/$n['x']);
	$theta = $n['x'];
	$phi = acos($n['z']/$r);
//	$theta = 0;
//	$theta = 0;
	return array('x' => $theta, 'y' => $phi);
}

//returns a png
function drawImage($locations,$map) {
	$image = imagecreate(600, 600);
	imagecolorallocate($image, 0, 0, 0);
	for($i = 0; $i<count($locations); $i++) {
		$index = $locations[$i]['x']*500*$locations[$i]['y'];
		$maxi = max($map);
		$freq = $map[$index]*225/($maxi/8);
		if($freq>=225)
			$freq = 225;
		$color = imagecolorresolve($image, $freq, $freq, $freq);
		$a = $locations[$i];
		$x = 150+(9*rad2deg($a['x'])); 
		$y = 20+(3*rad2deg($a['y']));
		$squaresize = 25;
		imagefilledellipse($image, $x, $y, $squaresize, $squaresize, $color);
	}
	return $image;
}

?>
