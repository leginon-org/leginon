<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');
$selectedmodelId = $_POST[modelId];
$models= $leginondata->getAllGoniometerModels();
?>
<html>
<head>
<title>Leginon2 - Goniometer</title>
<link rel="stylesheet" type="text/css" href="css/leginon.css"> 
</head>
<body>
<form name="goniometerform" method="POST" action="<?=$PHP_SELF?>">
<select name="modelId" onChange="javascript:document.goniometerform.submit()">
<?
foreach($models as $model) {
	if ($model[DEF_id]==$selectedmodelId)
        	$s='selected';
    	else
        	$s='';
	echo '<option value="'.$model[DEF_id].'" '.$s.' >'.$model[label].'</option>';
}

?>
</select>
<input type="submit" value="view">
</form>
<?
if($selectedmodelId) {
?>
<img src="goniometergraph.php?Id=<?=$selectedmodelId?>">
<?
}
?>
</body>
</html>
