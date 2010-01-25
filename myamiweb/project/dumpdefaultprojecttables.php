<?php
require 'inc/project.inc.php';
require 'inc/leginon.inc';
$host="cronus4";
$user="usr_object";
$pass="";
$db="project";

$leginondata->mysql = &new mysql($host, $user, $pass, $db);
$tables = array (
'boxtypes',
'grids',
'gridboxes',
'gridlocations',
'processingdb',
'projects',
'projectexperiments');
$leginondata->getXMLData("boxtypes", $data);
$dump = $leginondata->dumpDefaultTables($tables, $data);
echo $dump;
?>
