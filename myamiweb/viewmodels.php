<?php
require('inc/particledata.inc');
require('inc/util.inc');
require('inc/leginon.inc');
require('inc/project.inc');
require('inc/processing.inc');

$expId= $_GET[expId];
$particle = new particledata();
$projectId=getProjectFromExpId($expId);
?>

<html>
<head>
<title>Initial Models</title>
<link rel="stylesheet" type="text/css" href="css/viewer.css">
</head>
<body>

<?php
$models = $particle->getModelsFromProject($projectId);
echo divtitle("Initial Models");
echo "<P>\n";
foreach ($models as $model) {
  echo "<TABLE CLASS='tableborder' BORDER='1' CELLSPACING='1' CELLPADDING='2'>\n";
  # get list of png files in directory
  $pngfiles=array();
  $modeldir= opendir($model['path']);
  while ($f = readdir($modeldir)) {
    if (eregi($model['name'].'.*\.png$',$f)) $pngfiles[] = $f;
  }
  sort($pngfiles);
  
  # display starting model
  echo "<TR><TD COLSPAN=2>\n";
  echo "<B>Model ID: $model[DEF_id]</B><BR>\n";
  foreach ($pngfiles as $snapshot) {
    $snapfile = $model['path'].'/'.$snapshot;
    echo "<A HREF='loadimg.php?filename=$snapfile' target='snapshot'><IMG SRC='loadimg.php?filename=$snapfile' HEIGHT='80'>\n";
  }
  echo "</TD>\n";
  echo "</TR>\n";
  $sym=$particle->getSymInfo($model['REF|ApSymmetryData|symmetry']);
  echo"<TR><TD COLSPAN=2>$model[description]</TD></TR>\n";
  echo"<TR><TD COLSPAN=2>$model[path]/$model[name]</TD></TR>\n";
  echo"<TR><TD>pixel size:</TD><TD>$model[pixelsize]</TD></TR>\n";
  echo"<TR><TD>box size:</TD><TD>$model[boxsize]</TD></TR>\n";
  echo"<TR><TD>symmetry:</TD><TD>$sym[symmetry]</TD></TR>\n";
  echo "</TABLE>\n";
  echo "<P>\n";
}

?>
</body>
</html>
