<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/leginon.inc";
require "inc/viewer.inc";

$baseurl = BASE_URL;

$link = new iconlink();
$link->setImagePath('img/');
$link->cols = 3;
$link->addlink('imageviewer.php','Image Viewer','', 'viewer');
$link->addlink('3wviewer.php','3 Way Viewer','', '3wviewer');
$link->addlink('loi.php','LOI','', 'loi');
$link->addlink('rctviewer.php','RCT','', 'rct');
$link->addlink('admin.php','Administration','', 'admin');
$link->addlink('dualview.php','Dual Viewer','', 'dual_view');
$link->addlink('tomo/','Tomography','', 'tomo_icon_3');
$link->addlink('/phpMyAdmin/','phpMyAdmin','', 'phpMyAdmin');


$ip = $_SERVER['REMOTE_ADDR'];
$host = $_SERVER['REMOTE_HOST'];

/*
$title = "Viewed sessions";
$R = $leginondata->getviewerlog('last');
$content="<b>Lastest:</b><table>";
if ($R)
foreach ($R as $r) {
	$url = "3wviewer.php?expId=".$r['sessionId'];
	$content .= "<tr><td><a href='".$url."'>".$r['name']."</a> ".$r['comment']."</td></tr>";
}
$content.="</table>";

$content.="<b>Most:</b><table>";
$R = $leginondata->getviewerlog('most');
if ($R)
foreach ($R as $r) {
	$url = "3wviewer.php?expId=".$r['sessionId'];
	$content .= "<tr><td><a href='".$url."'>".$r['name']."</a> ".$r['comment']."</td></tr>";
}
$content.="</table>";
$log = display_table($title, $content);

$title = "Viewed sessions from : $host";

$R = $leginondata->getviewerlog('last', $host, $ip);
$content="<b>Lastest:</b><table>";
foreach ($R as $r) {
	$url = "3wviewer.php?expId=".$r['sessionId'];
	$content .= "<tr><td><a href='".$url."'>".$r['name']."</a> ".$r['comment']."</td></tr>";
}
$content.="</table>";
$R = $leginondata->getviewerlog('most', $host, $ip);
$content.="<b>Most:</b><table>";
foreach ($R as $r) {
	$url = "3wviewer.php?expId=".$r['sessionId'];
	$content .= "<tr><td><a href='".$url."'>".$r['name']."</a> ".$r['comment']."</td></tr>";
}
$content.="</table>";
$log_from = display_table($title, $content);
*/


$title = "Leginon II database Tools";
viewer_header($title);
?>
<style>
	BODY {background-image:url('img/background.jpg')}
</style>

<script src="js/prototype.js"></script>
<script>
	function preSearch()
	{
		var q = $F('query');
		var url = '<?=$baseurl?>getsessioninfo.php';
		var pars = 'q=' + q;
		$('result').innerHTML = "Searching...";
		var myAjax = new Ajax.Request( url, { method: 'get', parameters: pars, onComplete: showResponse });
	}

	function showResponse(originalRequest){
		$('result').innerHTML = originalRequest.responseText;
	}

</script>


<center><h1>Leginon II Database Tools</h1></center>
<hr/>
<noscript>
<?php echo divtitle("<center>Please enable Javascript in you Browser</center>"); ?>
</noscript>
<table align="center">
<tr valign="top">
<? /*
	<td>
		<?php echo $log_from; ?>
		<?php echo $log; ?>
	</td>
*/ ?>
	<td>
		<?php echo $link->Display(); ?>
	</td>
</tr>
</table>
<label for="query"><strong>Session finder:</strong>&nbsp;
<input style="border: 1px solid #bdcebb;" type="text" name="search" autocomplete="off" id="query" onKeyUp="preSearch()" />
</label>
<p>
<div style="border: 1px solid #bdcebb; padding-left: 5px" id="result">&nbsp;</div>
<?php
viewer_footer();
?>
