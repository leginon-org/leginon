<?php
if(!isset($_GET['sessionId']))
    exit('no session specified');
$sessionId = $_GET['sessionId'];
?>
<html>

<head>
<title>Summary</title>
<link rel="stylesheet" href="../css/viewer.css" type="text/css" /> 
</head>

<div class="header">
Tomography Summary
</div>

<div class="body">
<table>
<tr><td>
<img src="graphdoserate.php?sessionId=<?php echo $sessionId; ?>&width=800&height=500">
</td></tr>
<tr><td>
<img src="graphenergyshift.php?sessionId=<?php echo $sessionId; ?>&width=800&height=500">
</td></tr>
</table>
</div>

</form>

</body>

</html>

