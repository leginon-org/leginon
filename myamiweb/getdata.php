<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require ('inc/leginon.inc');

$g=true;
$opennodes = $_GET['r'];
if (!$id=$_GET[id]) {
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
<?
	echo $arr_node;
}
?>
</script>
</head>

<body >
<div id="tree">
<? if ($arr_node) { ?>
<script>
<!--
<?
if (ereg("undefined",$opennodes))
	$opennodes=0;
if (!empty($opennodes))
	$opennodes = '0,'.$opennodes;
echo "ano = new Array($opennodes);\n";?>
createTree(Tree,0,ano);
//-->
</script>
<? } ?>
</div>
</body>
</html>
