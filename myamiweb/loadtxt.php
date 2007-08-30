<?php
// --- Read a text file and print it
$filename=$_GET['filename'];
$lines = file($filename);
echo "<PRE>\n";
foreach ($lines as $line) {
  echo $line;
}
echo "</PRE>\n";
?>
