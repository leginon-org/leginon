<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "inc/ptcl.inc";
require_once "inc/picker.inc";

$title = "Particle Selection Adjust";
if (!$name=$_REQUEST['name'])
	$name='v';
if ($displayname=$_REQUEST['displayname'])
	$title .=" - ".$displayname;
$sessionId = $_REQUEST['session'];
$selectioninfo = string2selections($_REQUEST['psel']);

$pdb = new particledata();
$selections = $pdb->getSelections($sessionId);
$currentselections = array();

foreach ($selections as $k=>$selection) {
	$p[$k] = new colorpick('p'.$selection['SelectionId']);
	$tp[$k] = new targetpick('t'.$selection['SelectionId']);
	foreach ($selectioninfo as $selinfo) {
		if ($selinfo[0]==$selection['SelectionId']) {
			$p[$k]->setColor($selinfo[1]);
			$tp[$k]->setTarget($selinfo[2]);
			$currentselections[]=$selection['SelectionId'];
			break;
		}
	}
	$init .= $p[$k]->getInitJavascript();
	$init .= $tp[$k]->getInitJavascript();
	$checkbox .= "jsobj[$k] = ".$selection['SelectionId'].";\n";
}
?>
<html>
<head>
<title><?php echo $title; ?></title>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
<link rel="stylesheet" type="text/css" href="css/view.css">

<script src="js/viewer.js"></script>
<script src="js/picker.js"></script>
<script><!--
var jschkobj = '';
var jsobj = Array();
<?php
echo $checkbox;
if ($p || $pt) {
	echo $p[0]->getJavascript();
	echo $tp[0]->getJavascript();
}

echo"
var jsviewname = '$name';
";

?>
function update() {
	jschkobj = Array();
        for (n in jsobj) {
                if (ch = eval("document.adjustform.s"+jsobj[n])) {
			selinfo  = "(";
                        if (ch.checked) {
                                selinfo += jsobj[n];
                        }
			color = getValue("p"+jsobj[n]);
			target = getValue("t"+jsobj[n]);
			jschkobj[jschkobj.length] = selinfo+","+escape(color)+","+target+")";
                }
        }
	jsselection = (jschkobj.join(","));
	parentwindow.setParticleSelection(jsviewname,jsselection);
	parentwindow.newfile(jsviewname);
}

function init(){
	parentwindow = window.opener;
	this.focus();
	<?php echo $init; ?>
} 

 // --> 
</script> 

</head>
<body leftmargin="0" topmargin="0" bottommargin="0" marginwidth="0" marginheight="0" bgcolor="#FFFFFF" onload="init();">
<a class="header" href="addptclselect.php" target="particle" >Edit particle selections &raquo;</a>
<form method="post" name="adjustform" id="adjust" >
<table border="0">
 <tr>
	<td>
    <table border="0" cellspacing="2" cellpadding="2" >
	<tr>
		<td>Selection</td>
		<td>Color</td>
		<td>Target</td>
	</tr>
	<?php
	foreach ($selections as $k=>$selection) {
		echo "<tr>";
                echo "<td>";
		$sel = (in_array($selection['SelectionId'], $currentselections)) ? 'checked' : '';
		echo '<input type="checkbox" name="s'.$selection['SelectionId'].'" '.$sel.'>'.$selection['Name'].''."\n";
		echo $p[$k]->getFormInput();
                echo $tp[$k]->getFormInput();
                echo "</td>";
                echo "<td align='center'>";
                echo $p[$k]->add();
                echo "</td>";
                echo "<td align='center'>";
                echo $tp[$k]->add();
                echo "</td>";
                echo "</tr>";
	}
	?>
    </table>
  </td>
 </tr>
 <td>
	<input id="updatebutton" type="button" alt="Update Image" value="Display" onclick="update();">
 </td>
 </tr>
</table>
</form>
</body>
</html>
