<?php
require('inc/project.inc.php');

project_header("Appion Run Statistics");

mysql_connect(DB_HOST, DB_USER, DB_PASS) or
    die("Could not connect: " . mysql_error());
mysql_select_db(DB_PROJECT);

$result = mysql_query("select distinct appiondb from processingdb");

while ($row = mysql_fetch_array($result, MYSQL_ASSOC)) {
	//mysql_select_db('ap172');

	mysql_select_db($row['appiondb']);
	$q = "SELECT count(DISTINCT `REF|ApAceRunData|acerun`) AS runs,
			COUNT(DISTINCT `REF|leginondata|AcquisitionImageData|image`) AS img
			FROM `ApCtfData`";	
	$r = mysql_query($q) or die("Query error: " . mysql_error());
	$row = mysql_fetch_row($r);
	$aceRun += (int)$row[0];
	$aceProcessedImages += (int)$row[1];

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
	
	$q = "SELECT count(`DEF_id`) AS p,
			COUNT(DISTINCT `REF|leginondata|AcquisitionImageData|image`) AS i 
			FROM `ApParticleData`";
	
	$r = mysql_query($q) or die("Query error: " . mysql_error());
	$row = mysql_fetch_row($r);
	$processedImages += (int)$row[1];
	$selectedParticles += (int)$row[0];
	
	$q = "SELECT count(*) AS particles,
			COUNT(DISTINCT p.`REF|ApStackData|stack`) AS stacks
			FROM `ApStackData` AS s
			LEFT JOIN `ApStackParticleData` AS p
			ON s.`DEF_id` = p.`REF|ApStackData|stack`";
	
	$r = mysql_query($q) or die("Query error: " . mysql_error());
	$row = mysql_fetch_row($r);
	$totalStacks += (int)$row[1];
	$totalStacksParticles += (int)$row[0];
	
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
	
	$q = "SELECT count(*) AS templates
			FROM ApTemplateImageData";
	
	$r = mysql_query($q) or die("Query error: " . mysql_error());
	$row = mysql_fetch_row($r);
	$totalTemplates += (int)$row[0];

	$q = "SELECT count(*) AS models
			FROM ApInitialModelData";
	
	$r = mysql_query($q) or die("Query error: " . mysql_error());
	$row = mysql_fetch_row($r);
	$totalInitialModels += (int)$row[0];
	
   
}

$today = date("m/d/y");
PRINT ("<h4>As ". $today. "</h4>");
print("<table class='tableborder' cellpadding='0' cellspace='0'>");
print("<b>ACE Run:</b><br />");
print("&nbsp;&nbsp;Total Runs: ". number_format($aceRun) . '<br />');
print("&nbsp;&nbsp;Total Processed Images: ". number_format($aceProcessedImages) . '<br /><br />');

print("<b>Particle Selection:</b><br />");
print("&nbsp;&nbsp;Total Runs: ". number_format($particleSelectionRuns) . '<br />');
$templatePicker = $particleSelectionRuns-$dogPickerRuns-$manualPickerRuns-$tiltPickerRuns;
print("&nbsp;&nbsp;&nbsp;&nbsp; - Template Picker Runs: ". number_format($templatePicker) . '<br />');
print("&nbsp;&nbsp;&nbsp;&nbsp; - Dog Picker Runs: ". number_format($dogPickerRuns) . '<br />');
print("&nbsp;&nbsp;&nbsp;&nbsp; - Manual Picker Runs: ". number_format($manualPickerRuns) . '<br />');
print("&nbsp;&nbsp;&nbsp;&nbsp; - Tilt Picker Runs: ". number_format($tiltPickerRuns) . '<br />');
print("&nbsp;&nbsp;Total Processed Images: ". number_format($processedImages) . '<br />');
print("&nbsp;&nbsp;Total Selected Particles: ". number_format($selectedParticles) . '<br /><br />');

print("<b>Stacks Creation:</b><br />");
print("&nbsp;&nbsp;Total Stacks: ". number_format($totalStacks) . '<br />');
print("&nbsp;&nbsp;Total Particles: ". number_format($totalStacksParticles) . '<br /><br />');

print("<b>Reconstruction:</b><br />");
print("&nbsp;&nbsp;Total Recons: ". number_format($totalReconRun) . '<br />');
print("&nbsp;&nbsp;Total Iterations: ". number_format($totalReconIterations) . '<br />');
print("&nbsp;&nbsp;Total Classified Particles: ". number_format($totalClassifiedParticles) . '<br /><br />');

print("<b>Template Creation:</b><br />");
print("&nbsp;&nbsp;Total Templates: ". number_format($totalTemplates) . '<br />');
print("&nbsp;&nbsp;Total Initial Models: ". number_format($totalInitialModels) . '<br />');
print("</table>");



?>