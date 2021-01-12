<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement see
 *	@licence http://leginon.org
 *	@version $Revision: 1.84 $
 *	@version $Id: stats.inc,v 1.00 2018-09-11 18:16:12  $
 */
/**
 *	some somple stats functions: mean, sd, linear regression	
 *	
 */


function mean($array) {
	return array_sum($array)/count($array);
}

// Function to calculate square of value - mean
function sd_square($x, $mean) { return pow($x - $mean,2); }

// Function to calculate standard deviation (uses sd_square)    
function sd($array) {
   // square root of sum of squares devided by N-1
	return sqrt(array_sum(array_map("sd_square", $array, array_fill(0,count($array), (array_sum($array) / count($array)) ) ) ) / (count($array)-1) );
}

// Function to calculate linear regression coefficients of a pair of arrays (no checking they are equal!!)
function linear_regression( $x, $y) {
   $n=count($x) ; // number of items in array
   $x_sum = array_sum($x);  // sigma x
   $y_sum = array_sum($y) ; // sigma y
   $x_avg = $x_sum / $n;   // for correlation
   $y_avg = $y_sum / $n;  //for correlation
   $a=0 ; $bx=0; $by = 0; // for correlation

   $xx_sum=0;
   $xy_sum=0;

   for($i=0; $i < $n; $i++) {
      $xy_sum += ($x[$i]*$y[$i]) ;
      $xx_sum += ($x[$i]*$x[$i]) ;
      $xr = $x[$i] - $x_avg;  //for correlation
      $yr = $y[$i] - $y_avg;  //for correlation
       $a += $xr * $yr;  //for correlation
       $bx += pow($xr,2);  //for correlation
       $by += pow($yr,2);  //for correlation
   }

  //Slope
   $slope = ( ( $n * $xy_sum ) - ( $x_sum * $y_sum ) ) / ( ( $n * $xx_sum ) - ( $x_sum * $x_sum ) ) ;
  //Intercept
   $intercept = ($y_sum - ( $slope * $x_sum ) ) / $n;
  //Correlation
   $b = sqrt($bx*$by);
   if ($b==0) {
      $correlation=0;
   }
   else {
      $correlation = pow($a/$b,2);   // r-squared
   }
   return array (
      'slope' => $slope,
      'intercept' => $intercept,
      'correlation' => $correlation,
   );
}
?>
