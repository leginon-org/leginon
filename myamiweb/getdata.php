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
if (!$table=$_GET[table]) {
	$g=false;
}
if (!$id=$_GET[id]) {
	$g=false;
}

	
if($g) {
	$arr_node=$leginondata->getDataTree($table,$id);
?>
<html>
<head>
        <title>DataTree</title>
        <meta http-equiv="Content-Type" content="text/html; charset=iso-8859-1"> 
        <link rel="StyleSheet" href="css/tree.css" type="text/css">
        <script src="js/tree.js"></script>
        <script>
<?
}
if ($arr_node) {
echo "var Tree = new Array; \n";
while (list($k1, $v1) = each($arr_node)) {
        $jsvar[]="Tree[".($k1-1)."]";
        $nodeId[]=$k1;
        $nodeparent[]=0;
        $node[]=$v1;
}

foreach($nodeId as $i) {
        foreach($nodeId as $l) {
                if (ereg ("^".$node[$i].".+", $node[$l])) {
                        $nodeparent[$l]=$nodeId[$i];
			continue;
		}
        }

        $file = ereg_replace ("^.*\/","", $node[$i]);
		if ($i<>0)
                // echo $jsvar[$i],"=\"", $nodeId[$i],"|", $nodeparent[$i],"|",$file,"|","","\";\n";
                echo $jsvar[$i],"=\"", $nodeId[$i],"|", $nodeparent[$i],"|",$file,"|","javascript:oc($nodeId[$i], $nodeparent[$i])","\";\n";
}
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
