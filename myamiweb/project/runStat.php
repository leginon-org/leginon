<?php
require_once('inc/project.inc.php');
require_once "inc/jpgraph.php";
require_once "inc/jpgraph_line.php";
require_once "inc/jpgraph_scatter.php";
require_once "inc/jpgraph_bar.php";
require_once "inc/histogram.inc";
require_once "inc/image.inc";

if (privilege('projects')) {
	$title = "Statistics Report";
	login_header($title);
} else {
	$redirect=$_SERVER['PHP_SELF'];
	redirect(BASE_URL.'login.php?ln='.$redirect);
}

function getStatistic($dbname) {
	$stats = array(
		'db_name' => $dbname,
		'tot_cell' => 0,
		'tbl_cnt' => 0,
		'data_sz' => 0,
		'idx_sz' => 0,
		'tot_sz' => 0
	);
	$legdb = new mysql(DB_HOST, DB_USER, DB_PASS, $dbname);
	$res = $legdb->SQLQuery('SHOW TABLE STATUS FROM `'.$dbname.'`'); 
	while ($row = mysql_fetch_array($res, MYSQL_ASSOC)) {
		$stats['tbl_cnt']++;
		$stats['data_sz'] += $row['Data_length'];
		$stats['idx_sz'] += $row['Index_length'];

		$crn=count_tbl_rows($legdb, $row['Name']);
		$cfn=count_tbl_fields($legdb, $row['Name']);
		$ccn=$crn*$cfn;
		$stats['tot_cell'] += $ccn;
        }
	$stats['tot_sz'] = $stats['data_sz'] + $stats['idx_sz'];

	return $stats;
}

function count_tbl_rows($dbc, $table) {
        $res = $dbc->SQLQuery("SELECT COUNT(*) FROM `$table`");
        $row = mysql_fetch_row($res);
	$num_rows = $row[0];
	return $num_rows;
}

function count_tbl_fields($dbc, $table) {
        $res = $dbc->SQLQuery("SHOW FIELDS FROM `$table`");
	$num_rows = mysql_num_rows($res);
	return $num_rows;
}

/* convert byte to readable format */
function byteSize($bytes){
    $size = $bytes / 1024;
    if($size < 1024){
        $size = number_format($size, 2);
        $size .= ' KB';
    }else{
        if($size / 1024 < 1024){
            $size = number_format($size / 1024, 2);
            $size .= ' MB';
        }else 
        	if ($size / 1024 / 1024 < 1024){
            	$size = number_format($size / 1024 / 1024, 2);
            	$size .= ' GB';
            }else
            	if ($size / 1024 / 1024 / 1024 < 1024){
            	$size = number_format($size / 1024 / 1024 / 1024, 2);
            	$size .= ' TB';
            	} 
        }
    return $size;
} 


$dbStats = getStatistic(DB_LEGINON);

$sizeOfLeginonDB = byteSize($dbStats['tot_sz']);
$numOfLeginonDBRecord = $dbStats['tot_cell'];

$today = date("m/d/y");
project_header("Statistics Report - " . $today);

mysql_connect(DB_HOST, DB_USER, DB_PASS) or
    die("Could not connect: " . mysql_error());

/* use leginon database */
mysql_select_db(DB_LEGINON);

/* get total number of images and total size of images */
$q = "select count(DEF_id), sum(pixels) from AcquisitionImageData";
$r = mysql_query($q) or die("Query error: " . mysql_error());
$row = mysql_fetch_row($r);
$numOfImages = (int)$row[0];
$numOfImageSize = byteSize($row[1] * 4);

/* get total number of sessions with at least 10 images */
$q = "select distinct `REF|SessionData|session` as sessionID, 
		count(DEF_id) as images from AcquisitionImageData group by sessionID";
$r = mysql_query($q) or die("Query error: " . mysql_error());

while ($row = mysql_fetch_array($r, MYSQL_ASSOC)) {
	$numOfSessionsWithImages += (int)$row['images'] > 10 ? 1 : 0;
}

/* get total tomographic tilt series */
$q = "SELECT count(*) from TiltSeriesData where `tilt max` is not null";
$r = mysql_query($q) or die("Query error: " . mysql_error());
$row = mysql_fetch_row($r);
$TomographicTiltSeries = (int)$row[0];

/* change to project database */
mysql_select_db(DB_PROJECT);

/* get total number of projects */
$q = "select count(DEF_id) from projects";
$r = mysql_query($q) or die("Query error: " . mysql_error());
$row = mysql_fetch_row($r);
$totalNumProjects = (int)$row[0];

/* get total sessions tie with projects and total project contain sessions.*/
$q = "select count(distinct `REF|leginondata|SessionData|session`), 
		count(distinct `REF|projects|project`) from projectexperiments";
$r = mysql_query($q) or die("Query error: " . mysql_error());
$row = mysql_fetch_row($r);
$totalNumSessionUnderProjects = (int)$row[0];
$totalProjectWithSessions = (int)$row[1];

$q = "select DATE_FORMAT(DEF_timestamp, '%Y-%m-%e'), `REF|leginondata|SessionData|session` 
		from projectexperiments order by DEF_timestamp desc limit 1";
$r = mysql_query($q) or die("Query error: " . mysql_error());
$row = mysql_fetch_row($r);
$lastSessionTime = $row[0];
$lastSessionID = $row[1];

$q = "select DATE_FORMAT(DEF_timestamp, '%Y-%m-%e'), `REF|leginondata|SessionData|session` 
		from projectexperiments where `REF|leginondata|SessionData|session` <> 'NULL' 
		order by DEF_timestamp ASC limit 1";
$r = mysql_query($q) or die("Query error: " . mysql_error());
$row = mysql_fetch_row($r);
$firstSessionTime = $row[0];
$firstSessionID = $row[1];

/* found out when was the lastest data in the database
 * if latest data not older than 7 days, just display the 
 * latest data from dataStatusReport table. Otherwise, run
 * through all the ap database and save the result in the
 * dataStatusReport table.
 */

$q = "select * from dataStatusReport order by `DEF_timestamp` desc limit 1";
$r = mysql_query($q) or die("Query error: " . mysql_error());
$row = mysql_fetch_row($r);

if(!empty($row)){
	$latestRunTimestamp = $row[1];
	// if the stats are older than 7 days, don't set them. we need to recalculate them in the while loop below
	if (isset($latestRunTimestamp) && strtotime($latestRunTimestamp) >= strtotime("-1 week") ) {
		$numOfApProjects = $row[2];
		$numOfSessionsProcessed = $row[3];
		$numOfTotalProcessingRuns = $row[4];
		$lastExptRunTime = $row[5];
		$aceRun = $row[6];
		$ace2Run = $row[7];
		$ctfindRun = $row[8];
		$aceProcessedImages = $row[9];	
		$particleSelectionRuns = $row[10];
		$dogPickerRuns = $row[11];
		$manualPickerRuns = $row[12];
		$tiltPickerRuns = $row[13];
		$templatePicker = $row[14];
		$selectedParticles = $row[15];
		$classificationRuns = $row[16];
		$numOfClasses = $row[17];
		$classifiedParticles = $row[18];
		$totalRCTModels = $row[19];
		$tomogramRun = $row[20];
		$totalStacks = $row[21];
		$totalStacksParticles = $row[22];
		$totalReconRun = $row[23];
		$totalReconIterations = $row[24];
		$totalClassifiedParticles = $row[25];
		$totalTemplates = $row[26];
		$totalInitialModels = $row[27];
		$firstExptRunTime = $row[28];
	}
}

if (empty($latestRunTimestamp) || strtotime($latestRunTimestamp) < strtotime("-1 week")){ 
	
	/* get all the ap databases name */
	$result = mysql_query("select distinct appiondb from processingdb");
	/*
	 * select count(appiondb) from processingdb;  => 208 (total projects have ap database)
	 * select count(*) from projects; => 258 (total projects)
	 * 
	 */
	
	/* use the current time to compare processing run times while looking for the earliest date */
	$currentTime = time();
	$firstExptRunTime = $currentTime;
	
	while ($row = mysql_fetch_array($result, MYSQL_ASSOC)) {

		//This is only special for our group.
		//if($row['appiondb'] == 'ap5') continue;
		
		mysql_select_db($row['appiondb']);
		$apdb = new mysql(DB_HOST, DB_USER, DB_PASS, $row['appiondb']);
		// No ScriptProgramRun means no processing
		if (!$apdb->SQLTableExists('ScriptProgramRun')) continue;

		/* get Total number of Projects with processed data: */
		$q = "SELECT count(DEF_id) from ScriptProgramRun";
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$numOfApProjects += count((int)$row[0]) == 0 ? 0 : 1;
		
		/* get number of Sessions with processed data */
		$q = "select count(distinct `REF|leginondata|SessionData|session`), 
				count(DEF_id), max(DEF_timestamp), min(DEF_timestamp) from ApAppionJobData";
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$numOfSessionsProcessed += (int)$row[0];
		$numOfTotalProcessingRuns += (int)$row[1];
		
		/* set the first and last processing run dates */ 
		$lastExptRunTime = ($row[2] > $lastExptRunTime) ? $row[2] : $lastExptRunTime;
		if (isset($row[3]) && $row[3] != "0000-00-00 00:00:00") {
			$firstExptRunTime = ($row[3] < $firstExptRunTime) ? $row[3] : $firstExptRunTime;
		}
		
		/* get total processed images */
		$q = "SELECT COUNT(DISTINCT `REF|leginondata|AcquisitionImageData|image`) AS img
				FROM `ApCtfData`";	
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$aceProcessedImages += (int)$row[0];
		
		/* get ace run */
		$q = "SELECT count(*) from ApAceParamsData";
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$aceRun += (int)$row[0];
		
		/* get ace 2 run */
		$q = "SELECT count(*) from ApAce2ParamsData";
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$ace2Run += (int)$row[0];
		
		/* get ctffind run */
		$q = "SELECT count(*) from ApCtfTiltParamsData";
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$ctfindRun += (int)$row[0];
	
		/* get particle picking run information */
		$q = "SELECT count(*) AS runs, 
				COUNT(DISTINCT `REF|ApDogParamsData|dogparams`) AS dog,
				COUNT(DISTINCT `REF|ApManualParamsData|manparams`) AS manual,
				COUNT(DISTINCT `REF|ApTiltAlignParamsData|tiltparams`) AS tilt
				FROM `ApSelectionRunData`";	
		
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$particleSelectionRuns += (int)$row[0];
		$dogPickerRuns += (int)$row[1];
		$manualPickerRuns += (int)$row[2];
		$tiltPickerRuns += (int)$row[3];
		$templatePicker = $particleSelectionRuns-$dogPickerRuns-$manualPickerRuns-$tiltPickerRuns;
		
		/* get total number of particle picked */
		$q = "SELECT count(`DEF_id`) AS p,
				COUNT(DISTINCT `REF|leginondata|AcquisitionImageData|image`) AS i 
				FROM `ApParticleData`";
		
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$selectedParticles += (int)$row[0];
		
		/* classification runs */
		$q = "SELECT count(*), sum(num_classes) as total_classes from ApClusteringStackData";
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$classificationRuns += (int)$row[0];
		$numOfClasses += (int)$row[1];
		
		/* Classified particles */
		$q = "SELECT count(*) from ApClusteringParticleData";
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$classifiedParticles += (int)$row[0];
		
		/* Stack info */
		$q = "SELECT count(*) AS particles,
				COUNT(DISTINCT p.`REF|ApStackData|stack`) AS stacks
				FROM `ApStackData` AS s
				LEFT JOIN `ApStackParticleData` AS p
				ON s.`DEF_id` = p.`REF|ApStackData|stack`";
		
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$totalStacks += (int)$row[1];
		$totalStacksParticles += (int)$row[0];
		
		/* RCT Models */
		$q = "SELECT count(*) from ApRctRunData";
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$totalRCTModels += (int)$row[0];		
		
		/* Tomograms (need to add sub tomogram run and also full tomogram run */
		$q = "SELECT count(*) from ApTomogramData";
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$tomogramRun += (int)$row[0];
		$q = "SELECT count(*) from ApFullTomogramData";
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$tomogramRun += (int)$row[0];
		
		/* get information about Reconstruction */
		$q = "SELECT count(*) AS particles,
			COUNT(DISTINCT p.`REF|ApRefineIterData|refineIter`) AS iter,
			COUNT(DISTINCT i.`REF|ApRefineRunData|refineRun`) AS runs
			FROM `ApRefineIterData` AS i
			LEFT JOIN `ApRefineParticleData` AS p
			ON i.`DEF_id` = p.`REF|ApRefineIterData|refineIter`";
		
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$totalReconRun += (int)$row[2];
		$totalReconIterations += (int)$row[1];
		$totalClassifiedParticles += (int)$row[0];
		
		/* Total templates */
		$q = "SELECT count(*) AS templates
				FROM ApTemplateImageData";
		
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$totalTemplates += (int)$row[0];
	
		/* total initial models */
		$q = "SELECT count(*) AS models
				FROM ApInitialModelData";
		
		$r = mysql_query($q) or die("Query error: " . mysql_error());
		$row = mysql_fetch_row($r);
		$totalInitialModels += (int)$row[0];
		   
	} // end while loop
	
	// make sure the first run time was set, if not, set it to default
	if ( $firstExptRunTime == $currentTime ) $firstExptRunTime = "0000-00-00-00:00:00";
	
	// save data in to the dataStatusReport table
	mysql_select_db(DB_PROJECT);
	$q = "insert into dataStatusReport 
			(appion_project, processed_session, processed_run, last_exp_runtime, 
			ace_run, ace2_run, ctfind_run,ace_processed_image, particle_selection, dog_picker, 
			manual_picker, tilt_picker, template_picker, selected_particle, 
			classification, classes, classified_particles, RCT_Models, tomogram, stack, stack_particle, 
			3D_recon, recon_iteration, classified_particle, template, initial_model, first_exp_runtime) values(".
			$numOfApProjects.", ".$numOfSessionsProcessed.", ".$numOfTotalProcessingRuns.", '".$lastExptRunTime."', ".
			$aceRun.", ".$ace2Run.", ".$ctfindRun.", ".$aceProcessedImages.", ".$particleSelectionRuns.", ".$dogPickerRuns.", ".$manualPickerRuns.", ".
			$tiltPickerRuns.", ".$templatePicker.", ".$selectedParticles.", ".$classificationRuns.", ".$numOfClasses.", ".
			$classifiedParticles.", ".$totalRCTModels.", ".$tomogramRun.", ".$totalStacks.", ".
			$totalStacksParticles.", ".$totalReconRun.", ".$totalReconIterations.", ".$totalClassifiedParticles.", ".
			$totalTemplates.", ".$totalInitialModels.", '".$firstExptRunTime."')";
	$r = mysql_query($q) or die("Query error: " . mysql_error());
}
	
$totalCTF = $aceRun + $ace2Run + $ctfindRun;
?>
<table border="0" cellpadding="5" cellspacing="0">
	<tr>
		<td><h3>Current status:</h3></td>
	</tr>
	<tr>
		<td><table border="1"  cellpadding="5" cellspacing="0" width="100%">
			<tr><td><b># Project</b></td><td><b># Experiments</b></td><td><b>First Experiment (Date)</b><td><b>Last Experiment (Date)</b></td>
			<td><b># Processing Runs</b></td><td><b>First Run (Date)</b></td><td><b>Last Run (Date)</b></td></tr>
			<tr align="center"><td><?php echo number_format($totalNumProjects); ?></td>
			<td><?php echo number_format($totalNumSessionUnderProjects); ?></td>
			<td><?php echo $firstSessionTime ?></td>
			<td><?php echo $lastSessionTime ?></td>
			<td><?php echo number_format($numOfTotalProcessingRuns); ?></td>
			<td><?php echo substr($firstExptRunTime, 0, 10); ?></td>
			<td><?php echo substr($lastExptRunTime, 0, 10); ?></td></tr>
		</table></td>
	</tr>
</table>
<table border="0" cellpadding="5" cellspacing="0">
	<tr>
		<td colspan=2><h3>Leginon Statistics:</h3></td>
	</tr>
	<tr>
		<td># Projects:</td><td><?php echo number_format($totalProjectWithSessions); ?></td>
	</tr>
	<tr> 
		<td># Sessions:</td><td><?php echo number_format($numOfSessionsWithImages); ?></td>
	</tr>
	<tr height="15"></tr>
	<tr>
		<td># Images:</td><td><?php echo number_format($numOfImages); ?></td>
	</tr>
	<tr>
		<td>&nbsp;&nbsp;&nbsp;&nbsp; # Tomographic tilt series:</td><td><?php echo number_format($TomographicTiltSeries); ?></td>
	</tr>
	<tr> 
		<td>Size of images:</b></td><td><?php echo $numOfImageSize; ?></td>
	</tr>
	<tr height="15"></tr>
	<tr>
		<td># DB records:</td><td><?php echo number_format($numOfLeginonDBRecord); ?></td>
	</tr>
	<tr> 
		<td>Size of DB records:</td><td><?php echo $sizeOfLeginonDB; ?></td>
	</tr>
	<tr>
		<td colspan=2><b>Notes:</b> Only projects that have sessions sessions associated are counted.<br />
		Only sessions with more than 10 images are counted.</td>
	</tr>

	<tr>
		<td colspan=2><h3>Appion Statistics:</h3></td>
	</tr>
	<tr>
		<td># Projects:</td><td><?php echo number_format($numOfApProjects); ?></td>
	</tr>
	<tr>
		<td># Sessions:</td><td><?php echo number_format($numOfSessionsProcessed); ?></td>
	</tr>
	<tr height="15"></tr>
	<tr>
		<td># Processed images:</td><td><?php echo number_format($aceProcessedImages);?></td>
	</tr>
	<tr height="15"></tr>
	<tr>
		<td># Particle picking runs:</td><td><?php echo number_format($particleSelectionRuns); ?></td>
	</tr>
	<tr>
		<td>&nbsp;&nbsp;&nbsp;&nbsp; # Template Picker runs:</td><td><?php echo number_format($templatePicker);?></td>
	</tr>
	<tr>
		<td>&nbsp;&nbsp;&nbsp;&nbsp; # Dog Picker runs:</td><td><?php echo number_format($dogPickerRuns);?></td>
	</tr>
	<tr>
		<td>&nbsp;&nbsp;&nbsp;&nbsp; # Manual Picker runs:</td><td><?php echo number_format($manualPickerRuns);?></td>
	</tr>
	<tr>
		<td>&nbsp;&nbsp;&nbsp;&nbsp; # Tilt Picker runs:</td><td><?php echo number_format($tiltPickerRuns);?></td>
	</tr>
	<tr>
		<td># Particles picked:</td><td><?php echo number_format($selectedParticles);?></td>
	</tr>
	<tr height="15"></tr>
	<tr>
		<td># CTF runs:</td><td><?php echo number_format($totalCTF); ?></td>
	</tr>
	<tr>
		<td>&nbsp;&nbsp;&nbsp;&nbsp; # Ace runs:</td><td><?php echo number_format($aceRun); ?></td>
	</tr>
	<tr>
		<td>&nbsp;&nbsp;&nbsp;&nbsp; # Ace 2 runs:</td><td><?php echo number_format($ace2Run); ?></td>
	</tr>
	<tr>
		<td>&nbsp;&nbsp;&nbsp;&nbsp; # CtfFind runs:</td><td><?php echo number_format($ctfindRun); ?></td>
	</tr>
	<tr height="15"></tr>
	<tr>
		<td># Particle stacks:</td><td><?php echo number_format($totalStacks); ?></td>
	</tr>
	<tr>
		<td>&nbsp;&nbsp;&nbsp;&nbsp; # Particles in stacks:</td><td><?php echo number_format($totalStacksParticles);?></td>
	</tr>	
	<tr height="15"></tr>
	<tr>
		<td># Classification runs:</td><td><?php echo number_format($classificationRuns);?></td>
	</tr>
	<tr>
		<td># Classes:</td><td><?php echo number_format($numOfClasses);?></td>
	</tr>
	<tr>
		<td># Classified particles:</td><td><?php echo number_format($classifiedParticles);?></td>
	</tr>
	<tr>
		<td># RCT models:</td><td><?php echo number_format($totalRCTModels);?></td>
	</tr>
	<tr>
		<td># Tomograms:</td><td><?php echo number_format($tomogramRun);?></td>
	</tr>
	<tr height="15"></tr>
	<tr>
		<td># 3D Maps:</td><td><?php echo number_format($totalReconRun);?></td>
	</tr>
	<tr>
		<td>&nbsp;&nbsp;&nbsp;&nbsp; # Iterations:</td><td><?php echo number_format($totalReconIterations);?></td>
	</tr>
	<tr>
		<td>&nbsp;&nbsp;&nbsp;&nbsp; # Classified Particles:</td><td><?php echo number_format($totalClassifiedParticles);?></td>
	</tr>
	<tr height="15"></tr>
	<tr>
		<td># Templates:</td><td><?php echo number_format($totalTemplates);?></td>
	</tr>
	<tr>
		<td># Initial Models:</td><td><?php echo number_format($totalInitialModels);?></td>
	</tr>
	<tr>
		<td colspan=2><b>Notes:</b> Only projects that have processed data associated are counted.<br />
		Only sessions with processed data associated are counted.</td>
	</tr>
	<tr>
		<td colspan=2><h3>Graphical summaries:</h3></td>
	</tr>
</table>

<img src="../totalimagegraph.php"><br />
<a href="../totalimagegraph.php?vd=1">[data]</a>
<a href="../totalimagegraph.php?vs=1">[sql]</a><br />
<br />

<img src="../totalimagegraph.php?cu=1"><br />
<br />

<img src="../totalimagegraph.php?type=s"><br />
<a href="../totalimagegraph.php?type=s&vd=1">[data]</a>
<a href="../totalimagegraph.php?type=s&vs=1">[sql]</a><br />
<br />

<img src="../totalimagegraph.php?type=s&cu=1"><br />
<br />

<img src="../totalimagegraph.php?type=r"><br />
<a href="../totalimagegraph.php?type=r&vd=1">[data]</a><br />
<br />

<img src="../totalimagegraph.php?type=r&cu=1"><br />
<br />

