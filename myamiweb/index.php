<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/leginon.inc";

$baseurl = BASE_URL;

$link = new iconlink();
$link->setImagePath('img/');
$link->cols = 4;
$link->addlink('imageviewer.php','Image Viewer','', 'viewer');
$link->addlink('3wviewer.php','3 Way Viewer','', '3wviewer');
$link->addlink('loi.php','LOI','', 'loi');
$link->addlink('rctviewer.php','RCT','', 'rct');
$link->addlink('2wayviewer.php','2 Way Viewer','', 'viewer');
$link->addlink('tomo/','Tomography','', 'tomo_icon_3');
$link->addlink('dualview.php','Dual Viewer','', 'dual_view');
$link->addlink('template.php', 'Hole Template viewer','', 'template');

if (privilege('groups') > 3 ) 
	$link->addlink('admin.php','Administration','', 'admin');
if (privilege('projects') >= 2 ) 
	$link->addlink('project','Project DB','', 'project');
if (privilege('users') >= 2 && privilege('groups') <= 3) 
	$link->addlink('admin.php','Miscellaneous','', 'admin');

login_header(PROJECT_TITLE,'','',true);

?>
<style>
	body {background-image:url('img/background.jpg')}
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


<center><h1><?php echo PROJECT_TITLE; ?></h1></center>
<a class="header" href="viewerxml.php">[ test Dataset ]</a>
<hr/>
<noscript>
<?php echo divtitle("<center>Please enable Javascript in you Browser</center>"); ?>
</noscript>
<p>
		<?php echo $link->Display(); ?>
</p>
<label for="query"><strong>Session finder:</strong>&nbsp;
<input style="border: 1px solid #bdcebb;" type="text" name="search" autocomplete="off" id="query" onKeyUp="preSearch()" />
</label>
<p>
<div style="border: 1px solid #bdcebb; padding-left: 5px" id="result">&nbsp;</div>
<?php
login_footer();
?>
