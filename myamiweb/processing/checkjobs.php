<?php
require"inc/particledata.inc";
require"inc/util.inc";
require"inc/leginon.inc";
require"inc/project.inc";
require"inc/processing.inc";

$expId= $_GET['expId'];
$particle = new particledata();
$projectId=getProjectFromExpId($expId);
?>

<html>
<head>
<title>Cluster Jobs</title>
<link rel="stylesheet" type="text/css" href="../css/viewer.css">
</head>
<body>

<?php
writeTop("Cluster Jobs","Cluster Jobs Awaiting Upload");
$formAction=$_SERVER['PHP_SELF']."?expId=$expId";
$jobs = $particle->getJobIdsFromSession($expId);
echo "<FORM NAME='jobform' method='POST' ACTION='$formaction'>\n";
echo "<TABLE CLASS='tableborder' BORDER='1' CELLSPACING='1' CELLPADDING='5'>\n";
echo "<TR><TD>\n";
echo "Username: <INPUT TYPE='text' name='user' value='$_POST[user]'>\n";
echo "Password: <INPUT TYPE='password' name='password' value='$_POST[password]'>\n";
echo "</TD></TR></TABLE>\n";
echo "<P>\n";
echo "<INPUT TYPE='SUBMIT' NAME='checkjobs' VALUE='Check Jobs in Queue'>\n";
echo "</FORM>\n";
// if clicked button, list jobs in queue
if ($_POST['checkjobs']) {
  $queue = checkClusterJobs($_POST['user'], $_POST['password']);
  if ($queue) {
    echo "<P>Jobs currently running on the cluster:\n";
    echo "<PRE>$queue</PRE>\n";
  }
  else {
    echo "no jobs on cluster\n";
  }	
  echo "<P>\n";	
}
foreach ($jobs as $job) {
  $jobinfo = $particle->getJobInfoFromId($job['DEF_id']);
  echo divtitle("Job: $jobinfo[name] (ID: $job[DEF_id])");
  echo "<TABLE BORDER='0' >\n";
  $display_keys['appion path'] = $jobinfo['appath'];
  $display_keys['dmf path'] = $jobinfo['dmfpath'];
  $display_keys['cluster path'] = $jobinfo['clusterpath'];
  foreach($display_keys as $k=>$v) {
    echo formatHtmlRow($k,$v);
  }
  echo "</TABLE>\n";
  echo "<P>\n";
}

?>
</body>
</html>
