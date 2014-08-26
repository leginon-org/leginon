<?php
require_once 'inc/imagerequest.inc';
require_once 'inc/login.inc';

#login_header();

function redux_request_string($request_string) {
	$address = "http://bnc16.scripps.edu";
	$port = 55123;
	$msg = $request_string."\n";   // new line indicates end of request
	$reduxsock = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
	socket_connect($reduxsock, $address, $port);
	socket_write($reduxsock, $msg, strlen($msg));

	$reply = "";
	do {
			 $recv = "";
			 $recv = socket_read($reduxsock, 8192);
			 #$recv = socket_read($reduxsock, '100000000');
			 if($recv != "") {
					 $reply .= $recv;
			 }
	} while($recv != ""); 

	return $reply;
}
if($_POST){

	$powerValue = ($_POST['power'] == "false") ? false : true;

	$imagerequest = new imageRequester();
	$reply = $imagerequest->requestImage($_POST['filename'],$_POST['oFormat'],
		array($_POST['shapeX'],$_POST['shapeY']),
		$_POST['scaleType'],$_POST['scaleMin'],$_POST['scaleMax'],
		0,false,$powerValue);
	
	header('Content-Type: image/jpeg');
	echo($reply);
	exit;
}

?>
 
<body>
	<h3>MRC Image Convertor</h3>
	<form name="myform" action="<?php echo $_SERVER['PHP_SELF']; ?>" method="POST">
	<table>
	<tr>
		<td>MRC Source File Location</td>
		<td><input type="text" name="filename" size="55" value="<?php if($_POST) echo $_POST['filename']; ?>" /></td>
	</tr>
	<tr>
		<td>Output format</td>
		<td>
			<select name="oFormat">
				<option value="JPEG" <?php if($_POST['oFormat'] == "JPEG") echo "selected"; ?>>JPEG</option>
				<option value="GIF" <?php if($_POST['oFormat'] == "GIF") echo "selected"; ?>>GIF</option>
				<option value="TIFF" <?php if($_POST['oFormat'] == "TIFF") echo "selected"; ?>>TIFF</option>
				<option value="PNG" <?php if($_POST['oFormat'] == "PNG") echo "selected"; ?>>PNG</option>
				<option value="MRC" <?php if($_POST['oFormat'] == "MRC") echo "selected"; ?>>MRC</option>
			</select>			
		</td>
	</tr>
	<tr>
		<td>Pad Shape</td>
		<td>
			x-asix : <input type="text" name="padShapeX" size="4" value="<?php if($_POST) echo $_POST['padShapeX']; ?>" />&nbsp;
			y-asix : <input type="text" name="padShapeY" size="4" value="<?php if($_POST) echo $_POST['padShapeY']; ?>" />
		</td>
	</tr>
	<tr>
		<td>Pad Position</td>
		<td>
			x-asix : <input type="text" name="padPosX" size="4" value="<?php if($_POST) echo $_POST['padPosX']; ?>" />&nbsp;
			y-asix : <input type="text" name="padPosY" size="4" value="<?php if($_POST) echo $_POST['padPosY']; ?>" />
		</td>
	</tr>
	<tr>
		<td>Pad value</td>
		<td><input type="text" name="padValue" size="2" value="<?php if($_POST) echo $_POST['padValue']; ?>" /> (float)</td>
	</tr>
	<tr>
		<td>Power</td>
		<td>
			<input type="radio" name="power" value="true" <?php if($_POST['power'] == "true") echo "checked"; ?>>TRUE
			<input type="radio" name="power" value="false" <?php if($_POST['power'] == "false") echo "checked"; ?>>FALSE
		</td>
	</tr>
	<tr>
		<td>Mask Radius</td>
		<td><input type="text" name="maskRadius" size="2" value="<?php if($_POST) echo $_POST['maskRadius']; ?>" /> (float)</td>
	</tr>
	<tr>
		<td>Shape</td>
		<td>
			x-asix : <input type="text" name="shapeX" size="4" value="<?php if($_POST) echo $_POST['shapeX']; ?>" />&nbsp;
			y-asix : <input type="text" name="shapeY" size="4" value="<?php if($_POST) echo $_POST['shapeY']; ?>" />
		</td>
	</tr>
	<tr>
		<td>LPF</td>
		<td><input type="text" name="lpf" size="2" value="<?php if($_POST) echo $_POST['lpf']; ?>" /> (float)</td>
	</tr>
	<tr>
		<td>Scale minimum</td>
		<td><input type="text" name="scaleMin" size="2" value="<?php if($_POST) echo $_POST['scaleMin']; ?>" /> (float)</td>
	</tr>
	<tr>
		<td>Scale Maximum</td>
		<td><input type="text" name="scaleMax" size="2" value="<?php if($_POST) echo $_POST['scaleMax']; ?>" /> (float)</td>
	</tr>
	<tr>
		<td>Scale Type</td>
		<td>
			<select name="scaleType">
				<option value="minmax" <?php if($_POST['scaleType'] == "minmax") echo "selected"; ?>>minmax</option>
				<option value="stdev" <?php if($_POST['scaleType'] == "stdev") echo "selected"; ?>>stdev</option>
				<option value="cdf" <?php if($_POST['scaleType'] == "cdf") echo "selected"; ?>>cdf</option>
			</select>
		</td>
	</tr>
	<tr>
		<td>&nbsp;</td>
		<td>&nbsp;</td>
	</tr>
	<tr>
		<td>&nbsp;</td>
		<td><input type="submit" value="Submit" /></td>
	</tr>
	</table>

<?php 
login_footer(); 
?>
</body>
</html>
 
