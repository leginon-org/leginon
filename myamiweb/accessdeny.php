<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/leginon.inc";

$baseurl = BASE_URL;

login_header(PROJECT_TITLE);

$defaulttext = 'You are not an owner of the project nor a guest invited 
by the owner to the experiment session.';
$t = $_GET['text'];
$text = ($_GET['text']) ? $t: $defaulttext;

?>
<style>
	body {background-image:url('img/background.jpg')}
</style>

<center><h1><?php echo PROJECT_TITLE; ?></h1></center>
<hr/>
<p>
	<h3> Your access to the page was denied </h3>
	<h4> <? echo $text ?> </h4>
	<h4> Use your browser to return to the last allowed page. </h4>
</p>
<?php
login_footer();
?>
