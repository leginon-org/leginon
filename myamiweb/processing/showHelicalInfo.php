<?php
/**
 *	Displays helical information about a class or list of classes
 */

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";

?>
<html>
<head>
<style type="text/css">
html {
	font-size:82%;
}
body {
	font-family: sans-serif;
	color: black;
}

table {
	display: table;
	border-width: 0px;
	border-spacing: 0px;
	border-style: solid;
	border-color: gray;
	border-collapse: separate;
	background-color: white;
}
table th, table td {
	font-size:82%;
	padding: 0.1em 0.5em 0.1em 0.5em;
	margin: 0.1em;
}

table th {
	border-width: 1px;
	border-style: solid;
	border-color: white;
	background-color: #D3DCE3;
}
table td {
	border-width: 1px;
	border-style: solid;
	border-color: white;
}
table td.one {
	background-color: #EDEDED;
}
table td.two {
	background-color: #D5D5D5;
}

</style>
</head>
<body>
<?php

$expId=$_GET['expId'];
if (!$expId) {
	echo "<b>ERROR: Experiment ID (expId) number is missing</b><br/>\n";
	exit;
}
$alignId = $_GET['alignId'];
$include = $_GET['include'];
$classes = explode(',',$include);

$particle = new particledata();

if (!$particle->hasHelicalInfo($alignId)) {
	echo "<b>ERROR: Class doesn't have helical info</b><br/>\n";
	exit;
}
$totimgs = $particle->getNumImagesInAlignment($alignId);
echo "Total number of images used in alignment: $totimgs";
$hinfo = $particle->getHelicalInfoForClasses($alignId,$classes);
// reverse order of results, to start with first image
$hinfo = array_reverse($hinfo);

$nimgs = $particle->getHelicalInfoForClasses($alignId,$classes,$onlyNumImgs=True);
$nimgp=($nimgs/$totimgs*100);
$nimgp=roundToPoint($nimgp,1);
echo "<br>\n";
echo "Total number of images used in this class: $nimgs ($nimgp%)";
$labels = array('image','helixnum','partnum','xshift','yshift','rotation','angle');

echo "<table><tr>";
foreach ($labels as $l) {
	echo "<th align='center'><b>$l</b></th>\n";
}
echo "<th align='center'><b>finalRot</b></th>\n";
echo "</tr>\n";

$toggle=0;
foreach ($hinfo as $p) {
	// change color for each image
	echo "<tr>\n";
	if ($p['image']!=$lastimg) {
		$toggle++;
		$col="one";
		if ($toggle%2) $col="two";
	}
	foreach ($labels as $l) {
		$val = $p[$l];
		$val = roundToPoint($val,2);
		echo "<td class='$col' align='right'>$val</td>\n";
	}
	echo "<td class='$col' align='right'>";
	$finalrot=$p['rotation']+$p['angle'];
	if ($finalrot<-180) $finalrot=$finalrot+180;
	if ($finalrot>180) $finalrot=$finalrot-180;
	if ($finalrot<-90) $finalrot=$finalrot+180;
	if ($finalrot>90) $finalrot=$finalrot-180;
	$lastimg=$p['image'];
	echo roundToPoint($finalrot,2);
	echo "</td>\n";
	echo "</tr>\n";
}
echo "</table>\n";

function roundToPoint($num,$point) {
	$num=$num*pow(10,$point);
	$num=round($num);
	$num=$num/pow(10,$point);
	return $num;
}

?>
</body>
</html>

