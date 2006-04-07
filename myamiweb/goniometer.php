<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/admin.inc');
$selectedmodelId = $_POST[modelId];
$models= $leginondata->getAllGoniometerModels();
admin_header();
?>
<h3>View Goniometer</h3>
<form name="goniometerform" method="POST" action="<?php=$_SERVER['PHP_SELF']?>">
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
<?php
if($selectedmodelId) {
?>
<img src="goniometergraph.php?Id=<?php=$selectedmodelId?>">
<?php
}
admin_footer();
?>
