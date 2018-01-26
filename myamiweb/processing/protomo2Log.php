<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 *
 */

ini_set('session.gc_maxlifetime', 604800);
session_set_cookie_params(604800);

session_start();
$sessionname=$_SESSION['sessionname'];
$imageinfo=$_SESSION['imageinfo'];
$runname=$_GET['runname'];
$tiltseries=$_GET['tiltseries'];
$log=$_GET['log'];
$rundir=dirname($log);

$html .= "
	<center><H2><b>Tilt-Series #".ltrim($tiltseries, '0')."<br><font size=3>($runname)</font></b></H2></center>
	";

if ((file_exists($log)) and (filesize($log) !== 0)) {
	$logfile = file($log);
	
	foreach($logfile as $line) {
		$description_line = explode(' ', $line);
		if ($description_line[0] == 'Description:') {
			$html .= "
				<H3><center><hr>Description</b></H3></center>
				<hr /></br>";
			$html .= substr(strstr($line," "), 1);
		}
	}
	$html .= "<br><br>
		<center><H3><b><hr>Image List</b></H3></center>
		<hr /></br>";
	$images = glob("$rundir/raw/original/*");
	foreach($images as $image) {
		$html .= basename($image).'<br>';
	}
	$html .= "<br>
		<center><H3><b><hr>Log File</b></H3></center>
		<hr /></br>";
	foreach($logfile as $line) {
		$html .= $line.'<br>';
	}
}else{
	$html .= "<center><b>Log file not found...</b><br>(not visible until tilt-series alignment finishes)</center>";
}

echo $html

?>
</body>
</html>