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
	function calculatePoint($eulers)
	{
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
		$loc = array('x'=>($p[0]*$v[0][0] + $p[1]*$v[0][1] + $p[2]*$v[0][2]),'y'=> ($p[0]*$v[1][0] + $p[1]*$v[1][1] + $p[2]*$v[1][2]), 'z'=>($p[0]*$v[2][0] + $p[1]*$v[2][1] + $p[2]*$v[2][2]));
		return $loc;//return the point
	}

	function multiply($a, $b)
	{
		for($i = 0; $i<count($a); $i++)
		{
			for($j = 0; $j<count($b[0]); $j++)
			{
				$sum = 0;
				for($k = 0; $k<count($a[$i]); $k++)
					$sum+=$a[$i][$k]*$b[$k][$j];
				$c[$i][$j] = $sum;
			}
		}
		return $c;
	}	

	function trace($d)
	{
		$sum = 0;
		for($i = 0; $i<count($d); $i++)
		{
			$sum = $sum+$d[$i][$i];
		}
		return $sum;
	}
	function transpose($d)
	{
		for($i = 0; $i<count($d); $i++)
			for($j = 0; $j<count($d[$i]); $j++)
				$result[$i][$j] = $d[$j][$i];
		return $result;
	}

	function calculateDistance($e1,$e2)
	{
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
		else
		{
			$theta = acos($s);
			$d = abs($theta/(2*sin($theta)))*sqrt(pow($r[0][1]-$r[1][0],2)+pow($r[0][2]-$r[2][0],2)+pow($r[1][2]-$r[2][1],2));
			return $d;
		}
	}

	function getDifferences($e1s,$e2s)
	{
		//differences stores the numbers
		//temp is the list of eulers from the euler being compared to
		//a counter of the spot in the list
		$count = 0;
		$differences = array();
		while($count<count($e1s) && $count<count($e2s))//count is in range of list
		{
			//add distance onto list and update count
			$differences[$count] = (calculateDistance($e1s[$count],$e2s[$count]));
			$count++;
		}
		return $differences;
	}
	function meanDifference($e1s,$e2s)
	{
		//temp is the list of eulers from the euler being compared to
		//the total and count to calculate average
		$total = 0;
		$count = 0;
		while($count<count($e1s) && $count<count($e2s))//count is in range of list
		{
			//add another distance and update count
			$total += calculateDistance($e1s[$count], $e2s[$count]);
			$count++;
		}
		//formula for average is total/(# of elements)
		return $total/$count;
	}
	function getStats($e1s, $e2s)
	{
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
		$theStats = new Statistics($terms/$count, $std, $min, $max,$errors); 
		return $theStats;
	}

	class Statistics
	{
		var $myMean = 0;
		var $myStandardDeviation = 0;
		var $myMin = 0;
		var $myMax = 0;
		var $myData = array();
		function Statistics($mean,$std,$min,$max,$data)
		{
			$this->myMean = $mean;
			$this->myStandardDeviation = $std;
			$this->myMin = $min;
			$this->myMax = $max;
			$this->myData = $data;
		}
	}

//writes an image to a file with a trianlge with points $eulers drawn on it
function createTriangle($eulers)
{
	$points = array();
	for($i = 0; $i<count($eulers); $i++)
		$points[] = calculatePoint($eulers[$i]);
	$myImage = drawImage($points);
	return $myImage;
}

//returns a png
function drawImage($locations)
{
	$image = imagecreate(300,300);
	imagecolorallocate($image,255,255,255);
	$color = imagecolorallocate($image,0,0,0);
	for($i = 0; $i<count($locations); $i++)
	{
		$a = $locations[$i];
		$x = ($a['x']*125)+150;
		$y = (-$a['z']*125)+200;
		imageellipse($image,$x,$y,2,2,$color);
	}
	return $image;
}

?>
