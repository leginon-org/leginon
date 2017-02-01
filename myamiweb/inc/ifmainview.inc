<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

?>
<!-- Debut Table Main View -->
<table class="bgcolor1" border="0" cellpadding="1" cellspacing="0" >
 <tr>
	<td>Image Type</td>
	<td align=right>
	<a href="javascript:toggleimage('mvscale_bt', 'scale_bt'); newfile();"
	onmouseover="imageonfocus('mvscale_bt', 'scale_bt', '_over')" 
	onmouseout="imageonfocus('mvscale_bt', 'scale_bt', '')" 
	><img name="mvscale_bt" src="img/scale_bt_off.gif" border="0" height="15" vspace="0"></a>
	<a href="javascript:toggleimage('mvtarget_bt', 'target_bt'); newfile();"
	onmouseover="imageonfocus('mvtarget_bt', 'target_bt', '_over')" 
	onmouseout="imageonfocus('mvtarget_bt', 'target_bt', '')" 
	><img name="mvtarget_bt" src="img/target_bt_off.gif" border="0" height="15" vspace="0"></a>
</td>
 </tr>
 <tr>
	<td colspan=2>
	<table class="bgcolor0" border="0" cellpadding="0" cellspacing="0" >
	 <tr>
<td>
<table border=0 cellpadding="1" cellspacing="0">
<tr>
<td>
	<input type="hidden" name = "mvsel" value="">
	<select name = "mlist" onchange = "setlist(); newexp(); " > 
<?php
	if (is_array($datatypes))
	foreach ($datatypes as $k=>$v) {
		if ($k==$mlist) $s='selected'; else $s=''; 	
			echo "<option value=\"$v\" $s>$k \n"; 
	}
?>
	</select>
</td>
<td>
<td>
	<input id=backbutton type=button name=back value =" Back " onclick = "decIndex(); newfile(); getdata(); updatemap();" > 
</td>
<td>
	<input id=nextbutton type=button name=next value =" Next " onclick = "incIndex(); newfile(); getdata(); updatemap();" >
</td>
</tr>
</table>
</td>
<td>
	&nbsp;
</td>
	 </tr>
	 <tr>
<td colspan=4 valign=top height=512 width=512 >
<?php
$iframesize = ($_GET["ifs"]==1) ? 'width=100% height=100% ' : 'width="512" height="512"';
$src = 'src="getiframeimage.php"';
?>
<iframe id=iframeimg name="picturebox" <?php
echo "$iframesize  $src";
?> scrolling="auto" ></iframe>
</td>
	 </tr>
	</table>
	</td>
	 	 </tr>
</table>
<!-- Fin Table Main View -->
