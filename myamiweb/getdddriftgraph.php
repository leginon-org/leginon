<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

$aligned_imgid=$_GET['id'];
$size = ($_GET['s']) ? $_GET['s'] : 255;
$sessionid = $_GET['expId'];
?>
<html>
<head>
<title>
MAP: <?php echo $filename; ?>
</title>
<body>
<img src="dddriftgraph.php?id=<?php echo $aligned_imgid?>&expId=<?php echo $sessionid?>&s=<?php echo $size?>">
</body>
</html>
