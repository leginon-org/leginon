<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require('inc/util.inc');
$link = new iconlink();
$link->setImagePath('img/');
$link->addlink('imageviewer.php','Image Viewer','', 'viewer');
$link->addlink('3wviewer.php','3 Way Viewer','', '3wviewer');
$link->addlink('loi.php','LOI','', 'loi');
$link->addlink('application.php','Import/Export Application','', 'application');
$link->addlink('admin.php','Administration','', 'admin');

?>

<html>
<head>
<title>Leginon II database Tools</title>
<link rel="stylesheet" href="css/viewer.css" type="text/css" /> 
</head>
<body Background='img/background.jpg'>





<center><h1>Leginon II Database Tools</h1></center>
<hr/>
<?
$link->Display();
?>

</table>
</body>
</html>
