<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/admin.inc";

$login_check = $dbemauth->is_logged();

$instrumenthosts = $leginondata->getInstrumentHosts();
$validhosts = array();
foreach($instrumenthosts as $host) {
	$models = $leginondata->getGoniometerModelsByHost($host);
	if ($models) $validhosts[] = $host;
}
$selectedhost = ($_POST[host])? $_POST[host]:$validhosts[0];
$selectedmodelId = $_POST[modelId];
if (!$selectedhost) {
	$models= $leginondata->getAllGoniometerModels();
} else {
$models= $leginondata->getGoniometerModelsByHost($selectedhost);
}
//change selected model if host changes
$in = 0;
foreach($models as $model) {
	if ($model[DEF_id]==$selectedmodelId)
        	$in += 1;
    	else
        	$in +=0;
}
if ($in == 0) $selectedmodelId = $models[0][DEF_id];

admin_header();
?>
<h3>View Goniometer</h3>
<form name="goniometerform" method="POST" action="<?php echo $_SERVER['PHP_SELF'];?>">
<select name="host" onChange="javascript:document.goniometerform.submit()">
<?php
foreach($validhosts as $host) {
	if ($host==$selectedhost)
        	$s='selected';
    	else
        	$s='';
	echo '<option value="'.$host.'" '.$s.' >'.$host.'</option>';
}
?>
</select>

<select name="modelId" onChange="javascript:document.goniometerform.submit()">
<?php
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
<?php if($selectedmodelId) { ?>
<img src="goniometergraph.php?Id=<?php echo $selectedmodelId?>">
<?php
}
admin_footer();
?>
