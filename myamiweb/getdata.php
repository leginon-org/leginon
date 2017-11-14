<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "inc/leginon.inc";

$g=true;
$opennodes = $_GET['r'];
if (!$id=$_GET['id']) {
	$g=false;
}

	
if($g) {
	$arr_node=$leginondata->getDataTree('AcquisitionImageData',$id);
?>
<html>
<head>
        <title>DataTree</title>
        <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"> 
        <link rel="StyleSheet" href="css/tree.css" type="text/css">
        <script src="js/tree.js"></script>
        <script>
<?php
	echo $arr_node;
}
?>
</script>
</head>

<body >
<div id="tree">
<?php if ($arr_node) { ?>
<script>
<!--
<?php
if (preg_match("%undefined%",$opennodes))
	$opennodes=0;
if (!empty($opennodes))
	$opennodes = '0,'.$opennodes;
echo "ano = new Array($opennodes);\n"; ?>
createTree(Tree,0,ano);
//-->
</script>
<?php
}
?>
</div>
</body>
</html>
