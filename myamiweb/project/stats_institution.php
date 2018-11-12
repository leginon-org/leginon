<?php
require_once('inc/project.inc.php');
if (privilege('projects')) {
	$title = "Statistics Report";
	login_header($title);
} else {
	$redirect=$_SERVER['PHP_SELF'];
	redirect(BASE_URL.'login.php?ln='.$redirect);
}

$today = date("m/d/y");
project_header("Statistics Report - " . $today);
$link = mysqli_connect(DB_HOST, DB_USER, DB_PASS);
if (mysqli_connect_errno()) {
    die("Could not connect: " . mysqli_connect_error());
}

/* use leginon database */
mysqli_select_db($link, DB_PROJECT);
?>


		<h3>Leginon Statistics Across Institutions:</h3>
		<table border="1"  cellpadding="5" cellspacing="0" width="100%">
			<tr><td><b>Institution</b></td><td><b># Projects</b></td><td><b># Sessions</b></td></tr>
	<?php
	if(isset($_GET['dateFrom']) and isset($_GET['dateTo'])){
		$dateFrom = date('Y-m-d', strtotime($_GET['dateFrom']));
		$dateTo = date('Y-m-d', strtotime($_GET['dateTo']));
		$q = "SELECT userdetails.`institution`, count( DISTINCT projectexperiments.`REF|projects|project` ) as project_count, count( DISTINCT projectexperiments.`REF|leginondata|SessionData|session` ) as session_count
	FROM projectexperiments
	LEFT JOIN projectowners ON projectowners.`REF|projects|project` = projectexperiments.`REF|projects|project`
	LEFT JOIN userdetails ON userdetails.`REF|leginondata|UserData|user` = projectowners.`REF|leginondata|UserData|user`
	WHERE (projectexperiments.`DEF_timestamp` BETWEEN '$dateFrom' and '$dateTo')
		GROUP BY userdetails.`institution` order by session_count DESC";
		$r = mysqli_query($link, $q) or die("Query error: " . mysqli_error($link));
	}
	else{
		$q = "SELECT userdetails.`institution`, count( DISTINCT projectexperiments.`REF|projects|project` ) as project_count, count( DISTINCT projectexperiments.`REF|leginondata|SessionData|session` ) as session_count
	FROM projectexperiments
	LEFT JOIN projectowners ON projectowners.`REF|projects|project` = projectexperiments.`REF|projects|project`
	LEFT JOIN userdetails ON userdetails.`REF|leginondata|UserData|user` = projectowners.`REF|leginondata|UserData|user`
	GROUP BY userdetails.`institution` order by session_count DESC";
		$r = mysqli_query($link, $q) or die("Query error: " . mysqli_error($link));
		$date_q = "SELECT DATE_FORMAT(MIN(projectexperiments.`DEF_timestamp`), '%Y-%m-%d') AS date1,
       				DATE_FORMAT(MAX(projectexperiments.`DEF_timestamp`), '%Y-%m-%d') AS date2
					FROM projectexperiments";
		
		$date_r = mysqli_query($link, $date_q) or die("Query error: " . mysqli_error($link));
		$row = mysqli_fetch_row($date_r);
		$dateFrom = $row[0];
		$dateTo = $row[1];
	}
	while ($totalProjectWithSessionsByInstitution =  mysqli_fetch_row($r))
	{
		echo "<tr><td>$totalProjectWithSessionsByInstitution[0]</td><td>$totalProjectWithSessionsByInstitution[1]</td><td>$totalProjectWithSessionsByInstitution[2]</td></tr>"; 
	}
	echo '<tr>
	<td colspan=3>
		<form action="runStat.php">
		From:
		<input type="date" name="dateFrom" value='.$dateFrom.'>
		To:
		<input type="date" name="dateTo" value='.$dateTo.'>
		<input type="submit">
		</form>
	</td
	</tr>'
	?>		</table>
