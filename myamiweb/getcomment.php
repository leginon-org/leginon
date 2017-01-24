<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once 'inc/leginon.inc';

$id=$_GET['id'];
$preset=$_GET['preset'];

// --- find image
$newimage = $leginondata->findImage($id, $preset);
$imageId = $newimage['id'];

function editImageCommentTable($sessionId, $imageId, $commentv) {
	// Edit and update Session description
	global $leginondata;
	if ( !empty($_POST['comment']) && $commentv != $_POST['comment'] ) {
		$leginondata->updateImageComment($sessionId, $imageId, $_POST['comment']);
		$commentv = $_POST['comment'];
	}
	$display .= '
			<form name="commentform" method="POST" action="'.$_SERVER['REQUEST_URI'].'">
				<table width=100% cellpadding="0" cellspacing="0" style="position:relative; border: 1px #696969 solid">
					<tr valign="top">
						<td>
							<textarea class="textarea" name="comment" rows="1" cols="70%" wrap="virtual"
									>'.$commentv.'</textarea>
						</td><td align="right">
							<input class="bt1" type="button" name="save comment" value="update" onclick=\'javascript:document.commentform.submit()\'/>
						</td>
					</tr>
				</table>
			</form>
		';
	return $display;
}

function displayImageCommentTable($commentv) {
	$display = '
		<table width=100% cellpadding="2" cellspacing="0" style="position:relative; border: 1px #696969 solid">
			<tr valign="top">
				<td >
					'.$commentv.'
				</td>
			</tr>
		</table>
	';
	return $display;
}

?>
<html>
<head>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
</head>
<body leftmargin="0" topmargin="0" bottommargin="0" marginwidth="5" marginheight="0" >
<font face="Arial, Helvetica, sans-serif" size="2">
<?php

if ($imageId) {
	echo "<font style='font-size: 10px;'>";
	$imagecommentv = $leginondata->getImageComment($imageId);
	//Block unauthorized user
	$sessioninfo = $leginondata-> getSessionInfoFromImage($imageId);
	$sessionId = $sessioninfo['sessionId'];
	$allow_edit = hasExptAdminPrivilege($sessionId,$privilege_type='data');
	if ( $allow_edit ) {
		echo editImageCommentTable($sessionId, $imageId, $imagecommentv);
	} else {
		echo displayImageCommentTable($imagecommentv);
	}
}

?>
</font>
</body>
</html>
