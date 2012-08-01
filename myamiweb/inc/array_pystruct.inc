<?php
/**
 *	Some tools to deal with python string structure representations
 *	stored in the database
 *
 */

/**
 *	This function returns a PHP array which contains 
 *	elements from a python string representation structure.
 *
 *	for example:
 *	[{0: 'manager', 34: {}, 1: 'grids', 2: 4}, 4, ('manager', 'grids', 10)]
 *
 *	Array
 *	(
 *	    [0] => {0: 'manager', 34: {}, 1: 'grids', 2: 4}
 *	    [1] => 4
 *	    [2] => ('manager', 'grids', 10)
 *	)
 *
 */
function get_pystruct_elements($pystruct=array()) {
	$elements = array();
	if ($pystruct)
		foreach ($pystruct as $k=>$v) {
			if ($pystruct['PAR_TYPE']!=$v)
				$elements[] = array_to_pystruc_str($v);
		}
	return $elements;
}

/**
 *	This function converts a PHP structure from pystruct_to_array()
 *	into a python string representation structure.
 *
 *	for example:
 *	array (						[
 *		'PAR_TYPE' => '{'				{       0:'manager',
 *		array ( 'PAR_TYPE' => '{'				1:'grids',
 *			0=>'manager',					2:4,
 *			1=>'grids',				},
 *			2=>4
 *		),	  			=>		(	
 *		array ( PAR_TYPE' => '('				'manager',
 *			'manager',					'grids',
 *			'grids',					10
 *			10					)
 *		)						
 *	)						]
 *
 */
function array_to_pystruc_str($data) {
	$type = $data[PAR_TYPE];
	switch ($type) {
		case '{':
			$open = '{';
			$close = '}';
			break;
		case '(':
			$open = '(';
			$close = ')';
			break;
		case '[':
			$open = '[';
			$close = ']';
			break;
		default:
			return $data;
	}
	$str = array();
	if (is_array($data))
	foreach ($data as $k=>$d) {
		if ($k=='PAR_TYPE' && !$k==0)
			continue;
		if (is_array($d)) {
			$d = array_to_pystruc_str($d);
			$f = 'pass';
		} else {
			$f='addquotes';
		}
		if ($type == '{') 
			$str[] = addquotes($k).': '.$f($d);
		else
			$str[] = $f($d);
		
	}
	return $open.implode(', ',$str).$close;
		
}

/**
 *	This function returns a passed var.
 */
function pass($var) {
	return $var;
}

/**
 *	This function add single quotes to any string var.
 */
function addquotes($var) {
	if (!is_numeric($var) && is_string($var))
		$var = "'$var'";
	return $var;
}
	
/**
 *	This function evaluates a python structure string representation
 *	as a PHP array.
 *
 *	for example:
 *	[					array (
 *							'PAR_TYPE' => '{'
 *		{	0:'manager',			array ( 'PAR_TYPE' => '{'
 *			1:'grids',				0=>'manager',
 *			2:4,					1=>'grids',
 *		},						2=>4
 *		  			=>		),
 *		(					array ( PAR_TYPE' => '('
 *			'manager',				'manager',
 *			'grids',				'grids',
 *			10					10
 *		)					)
 *	]					)
 *
 */
function pystruct_to_array($pylist) {
	$par_type = 'PAR_TYPE';
	$phparray = array();
	$pylist = trim($pylist);
	$matchbracket1 = preg_match('%(^\[)(.*)(\]$)%', $pylist);
	$matchbracket2 = preg_match('%(^\()(.*)(\)$)%', $pylist);
	$matchbracket3 = preg_match('%(^\{)(.*)(\}$)%', $pylist);

	if (!$matchbracket1 && !$matchbracket2 && !$matchbracket3)
		return false;

	$pylist = preg_replace('%\]|\}', ')%', $pylist);
	$pylist = preg_replace('%:%', '=>', $pylist);
	$pylist = preg_replace('%\(%', 'array (\''.$par_type.'\'=>\'(\', ', $pylist);
	$pylist = preg_replace('%\[%', 'array (\''.$par_type.'\'=>\'[\', ', $pylist);
	$pylist = preg_replace('%\{%', 'array (\''.$par_type.'\'=>\'{\', ', $pylist);
	eval("\$phparray = $pylist;");
	return $phparray;
}

?>
