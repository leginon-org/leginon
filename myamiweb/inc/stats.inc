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
 *	some somple stats functions: mean, sd	
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
?>
