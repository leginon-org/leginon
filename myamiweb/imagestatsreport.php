<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require "inc/leginon.inc";

$defaultId= 1445;
$sessionId= ($_GET['Id']) ? $_GET['Id'] : $defaultId;

// --- Set  experimentId
// $lastId = $leginondata->getLastSessionId();
// $sessionId = (empty($_GET[Id])) ? $lastId : $_GET[sessionId];
$sessioninfo = $leginondata->getSessionInfo($sessionId);
$title = $sessioninfo['Name'];
$presets = $leginondata->getDatatypes($sessionId);


?>
<html>
<head>
<title>Image Statistics for session <?php echo $title; ?></title>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
</head>

<body>
<table border="0" cellpadding=10>
<tr>
 <td>
  <a class="header" HREF="index.php">&lt;index&gt;</a>
 </td>
 <td>
  <a class="header" HREF="3wviewer.php?sessionId=<?php echo $sessionId; ?>">&lt;view <?php echo $title; ?>&gt;</a>
 </td>
</tr>
</table>
<table border="0" cellpadding=10>
<tr valign="top">
	<td colspan="2">
	<?php echo divtitle("Image Statistics for session $title "); ?>
	</td>
</tr>
<?php
foreach ($presets as $preset) {
	echo "<tr>";
	echo "<td>";
	echo "- Mean & Stdev for Preset $preset"; 
	echo "</td>";
	echo "</tr>";
?>
<tr>
<td>
<a href="imagestatsgraph.php?hg=1&vdata=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[data]</a>
<a href="imagestatsgraph.php?hg=1&vs=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[sql]</a><br>
<a href="imagestatsgraph.php?hg=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>"><img border="0" src="imagestatsgraph.php?w=300&hg=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>"></a>
</td>
<td>
<a href="imagestatsgraph.php?vdata=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[data]</a>
<a href="imagestatsgraph.php?vs=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[sql]</a><br>
<a href="imagestatsgraph.php?Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>"><img border="0" src="imagestatsgraph.php?w=300&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>"></a>
</td>
</tr>
<tr>
<td>
<a href="imagestatsgraph.php?stdev=1&hg=1&vdata=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[data]</a>
<a href="imagestatsgraph.php?stdev=1&hg=1&vs=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[sql]</a><br>
<a href="imagestatsgraph.php?stdev=1&hg=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>"><img border="0" src="imagestatsgraph.php?stdev=1&w=300&hg=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>"></a>
</td>
<td>
<a href="imagestatsgraph.php?stdev=1&vdata=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[data]</a>
<a href="imagestatsgraph.php?stdev=1&vs=1&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>">[sql]</a><br>
<a href="imagestatsgraph.php?stdev=1&w=300&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>"><img border="0" src="imagestatsgraph.php?stdev=1&w=300&Id=<?php echo $sessionId; ?>&preset=<?php echo $preset; ?>"></a>
</td>
</tr>
<?php } ?>
</table>
</td>
</tr>
</table>
</body>
</html>
