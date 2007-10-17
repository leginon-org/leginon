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
    echo "<P>Jobs currently running on the cluster:<P>\n";
    $list = streamToArray($queue);
    $dispkeys = array('Job ID','User','Queue','Jobname','SessId','NDS','TSK','ReqMem','ReqTime','S','ElapTime');
    echo "<TABLE CLASS='tableborder' border=1 cellspacing=0, cellpadding=5>\n";
    echo "<TR>\n";
    foreach ($dispkeys as $key) {
      echo "<TD><SPAN CLASS='datafield0'>$key</SPAN></TD>";
    }
    echo "</TR>\n";
    foreach ($list as $line) {
      echo "<TR>\n";
      foreach ($line as $i) {echo "<TD>$i</TD>\n";}
      echo "</TR>\n";
    }
    echo "</TABLE>\n";
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
  if ($_POST['checkjobs']) {
    echo "<B>Current Status:</B>\n";
    $stat = checkJobStatus($jobinfo['clusterpath'],$jobinfo['name'],$_POST['user'],$_POST['password']);
    $numtot=count($stat['allref']);
    $current=count($stat['curref']);
    echo "Currently processing iteration $current of $numtot\n";
    //    print_r($stat['current']);
    if ($stat['errors']) echo "<P><FONT COLOR='RED'>There are errors in this job, you should resubmit</FONT><P>";
  }
  echo "<P>\n";
}
writeBottom();
exit;

function checkJobStatus($jobpath,$jobfile,$user,$pass) {
  $cmd = "grep refine $jobpath/$jobfile ";
  $r = exec_over_ssh('garibaldi',$user,$pass,$cmd, True);
  $allref = streamToArray($r);
  foreach ($allref as $i){
    if ($i[0]=='refine' && preg_match('/\d+/',$i[1])) $stat['allref'][]=$i;
  }
  $cmd = "grep refine $jobpath/recon/refine.log";
  $r = exec_over_ssh('garibaldi',$user,$pass,$cmd, True);
  $curref = streamToArray($r);
  foreach ($curref as $i){
    if ($i[0]=='refine' && preg_match('/\d+/',$i[1])) $stat['curref'][]=$i;
  }
  $cmd = "grep Alarm $jobpath/recon/refine.* ";
  $stat['errors'] = exec_over_ssh('garibaldi',$user,$pass,$cmd, True);

  return $stat;
}

