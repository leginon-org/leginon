<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/leginon.inc');
?>
<html>
<head>
</head>
<?
$template = $_GET['tmpl'];
$table = $_GET['table'];
$session = $_GET['session'];
$id= $_GET['id'];
$size=$_GET['s'];
$quality=$_GET['t'];
$minpix=$_GET['np'];
$maxpix=$_GET['xp'];

$targets = $leginondata->getImageTargets($id);
$focustargets = $leginondata->getImageFocusTargets($id);

$src = "$template?table=$table&session=$session&id=$id&t=$quality&s=$size&np=$minpix&xp=$maxpix&sb=1";
?>

<body leftmargin="0" topmargin="0" bottommargin="0" marginwidth="0" marginheight="0" >
<img id=imgmv name=newimgmv src="<?= $src ?>">
</body>
</html>

