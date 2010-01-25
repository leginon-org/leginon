<?php
require "inc/project.inc.php";
require "inc/leginon.inc";
require "inc/utilpj.inc.php";

if ($_GET['pId']) {
	$selectedprojectId=$_GET['pId'];
}
if ($_POST['currentproject']) {
	$selectedprojectId=$_POST['currentproject'];
}
$view = ($_REQUEST['v']=='s') ? 'd' : 's';
$link = ($view=='s') ? 'Detailed view' : 'Simple view';
$privilege = privilege();
$is_admin = ($privilege == 2);
$project = new project();
$projects = $project->getProjects("order");
$projectinfo = $project->getProjectInfo($selectedprojectId);
$projectname = ": ".$projectinfo['Name'];

if ($_POST['updateprocessing']) {
	$q="delete from processingdb where projectId='$selectedprojectId'";
	$r=$project->mysql->SQLQuery($q);
}

$linkprocessing=false;
if ($_POST['linkprocessing']) {
	$linkprocessing=true;
}

if ($_POST['createprocessing'] || $linkprocessing) {
	$dbname=trim($_POST['dbname']);
	if ($dbname) {
		$q='create database `'.$dbname.'`';
		$r=$project->mysql->SQLQuery($q);
		if (!$r && !$linkprocessing) {
			$dberror = $project->mysql->getError();
			$dberrornb = $project->mysql->getErrorNumber();
		} else {
			// --- created default tables --- //
			$filename = $DEF_PROCESSING_TABLES_FILE;
			$leginondata->mysql->setSQLHost( array('db'=>$dbname) );
			$leginondata->importTables($filename);

			$data=array();
			$data['projectId']=$selectedprojectId;
			$data['db']=$dbname;
			$project->mysql->SQLInsertIfNotExists('processingdb', $data);
		}
	}
}

if (!$p_prefix = trim($DEF_PROCESSING_PREFIX)) {
	$p_prefix = false;
}


$q="select db from processingdb where projectId='$selectedprojectId'";
list($r)=$project->mysql->getSQLResult($q);
$processingdb=$r['db'];
$title = "Project".$projectname;
login_header($title);
project_header($title, 'init()');
?>
<script type="text/javascript" >
	function onChangeProject(){
		var cId = document.projectform.currentproject.options[document.projectform.currentproject.selectedIndex].value;
		document.projectform.submit();
	}

	function init() {
		if (obj = window.document.projectform.currentproject)
			obj.focus();
	}

</script>
<?php
$url = $_SERVER['PHP_SELF']."?v=".$_REQUEST['v']."&amp;pId=".$selectedprojectId;
$link_on = "<a class='header' href='$url&amp;ld=1'>[x]</a> ";
$link_off = "<a class='header' href='$url&amp;ld=0'>[o]</a> ";
$ld = ($_GET['ld']==0) ? $link_on : $link_off;
$cat  = ($_GET['cat']==0) ? $link_on : $link_off;
?>
<form method="POST" name="projectform" action="<?php echo $PHP_SELF ?>">
<input type="hidden" name="v" value="<?=$_REQUEST['v']?>">
<table border="0" >
<tr>
<td valign="top" >
<select size="15" name="currentproject" tabindex="1" onchange="onChangeProject()">
<?php
foreach ($projects as $proj) {
    $s = ($proj["projectId"]==$selectedprojectId) ? 'selected' : $s='';
    echo "<option value='",$proj["projectId"],"' $s >",$proj["name"]."</option>\n";
}
?>
</select>
</td>
<td valign="top">
<?php

?>
<a class="header" href="<?=$_SERVER['PHP_SELF']."?v=$view&amp;pId=".$selectedprojectId?>">&lt;<?=$link?>&gt;</a>
<?php
	if ($is_admin)
		echo "<a class='header' href='updateproject.php?id=$selectedprojectId&amp;ln=".urlencode($url)."'>&lt;edit&gt;<img alt='edit' border='0' src='img/edit.png'></a>";
?>
<?=divtitle('Info');?>
<table border="0" width="600">
<tr>
	<th>Short Description</th>
</tr>
<?php
$pId = $selectedprojectId;
	echo "<tr>\n";
	echo "<td>";
	echo $projectinfo['Title'];
	echo "</td>";
	echo "</tr>\n";
	echo "<tr>\n";
	echo "<td>";
	echo "<b>processing db:</b> ";
	if ($processingdb) {
		echo "$processingdb ";
		if ($is_admin)
			echo '<input type="submit" name="updateprocessing" value="unlink"><span style="font-size:8px"><b>Note:</b> db won\'t be deleted</span>';
	} else {
		if ($p_prefix) {
			$defaultdbname=$p_prefix.$selectedprojectId;
		} else {
			$defaultdbname='processing';
		}
		if ($_POST['dbname']) {
			$defaultdbname=trim($_POST['dbname']);
		}
		echo ' <span style="color:red">not set</span> ';
		if (!$dberror) {
			if ($is_admin) {
				echo '<input type="submit" name="createprocessing" value="create processing db">';
			} else {
				echo 'see administrator to create the processing db';
			}
		}
		echo ' <b>db name:</b> <input type="text" name="dbname" size="5" value="'.$defaultdbname.'">';
	}
	if ($dberror) {
		echo '<p>';
		if ($dberrornb==1007) {
			echo '<span>database '.$dbname.' exists</span> ';
			echo '<input type="submit" name="linkprocessing" value="link anyway"> ';
			echo '<input type="submit" name="no" value="cancel">';
		} else {
			echo $dberror;
		}
		echo '</p>';
	}
	echo '</td>';
	echo '</tr>';
?>
</table>
<?php
$ln=urlencode($url);
$projectId = $projectinfo['projectId'];

// Experiments 
	$experimentIds = $project->getExperiments($projectId);
	echo divtitle(count($experimentIds).' Experiments');

	echo '<a alt="upload" target="_blank" class="header" href="'.UPLOAD_URL.'?pId='.$selectedprojectId.'">upload images to new session</a>';

	$sessions=array();
	$experiments=array();
	foreach ($experimentIds as $k=>$exp) {
	
		$info = $leginondata->getSessionInfo($exp);
		$sessions[trim($info['SessionId'])]=$info['Name'];
		$sessionlink="<a class='header' target='viewer' href='".VIEWER_URL.$info['SessionId']."'>".$info['Name']."</a>";
		$experiments[$k]['name']=$sessionlink;
		$experiments[$k]['purpose']=$info['Purpose'];
		$experiments[$k]['totalimg']=$info['Total images'];
		$experiments[$k]['totaltime']=$info['Total Duration'];
		$summarylink="<a class='header' target='viewer' href='".SUMMARY_URL.$info['SessionId']."'>summary&raquo;</a>";
		$experiments[$k]['summary']=$summarylink;
	}

$columns=array(
	'name'=>'Name',
	'purpose'=>'Purpose',
	'totalimg'=>'Total images',
	'totaltime'=>'Total Duration'
	);
	$columns['summary']="";

$display_header=true;
echo data2table($experiments, $columns, $display_header);
	
if ($view=='d') {
	echo "<br>";
	echo divtitle('Description', $ld);
	$cols = 80;
	$rows = 10;
if ($_GET['ld']!=1) {
?>
<textarea class='textarea' cols="<?=$cols?>" rows="<?=$rows?>" readonly="readonly" >
<?=($projectinfo['Description'])?>
</textarea>
<?php
}
	echo divtitle('Category | Funding | Associates');
?>
<textarea class="textarea" cols="<?=$cols?>" rows="<?=$rows?>" readonly="readonly" >
<?php
	echo $projectinfo['Category'];
	echo "\n";
	echo $projectinfo['Funding'];
?>
</textarea>
<?php
}
?>
</td>
</tr>
</table>
</form>
<?php
project_footer();
?>
