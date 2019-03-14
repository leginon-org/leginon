<?php
require_once "inc/leginon.inc";
require_once "inc/viewer.inc";
require_once "inc/project.inc";
require_once "inc/cachedb.inc";
require_once "inc/particledata.inc";
// --- get Predefined Variables form GET or POST method --- //
list($projectId, $sessionId, $imageId, $preset, $runId, $scopeId) = getPredefinedVars();

//Block unauthorized user
checkExptAccessPrivilege($sessionId);

$sessioninfo=$leginondata->getSessionInfo($sessionId);
$session=$sessioninfo['Name'];

$summary=$leginondata->getSummary($sessionId);
$imageinfo = $leginondata->getImageInfoFromPreset(end($summary)['presetId']);
$instrumentinfo = $leginondata->getInstrumentInfo($sessioninfo['InstrumentId']);

echo "<link rel='stylesheet' href='css/neiladd.css' />";

//echo '<pre>'; print_r($sessioninfo); echo '</pre>';
//echo '<pre>'; print_r($imageinfo); echo '</pre>';
//echo '<pre>'; print_r($summary); echo '</pre>';
//echo '<pre>'; print_r($instrumentinfo); echo '</pre>';
echo '<center>';
echo '<table cellspacing="0">';

if (strpos($sessioninfo['Purpose'], 'nccat') !== false){
	echo '<tr style="background-color:#d4e0ee; color:black;font-size:18px;font-weight:bold;">';
	echo '<td><a href="http://nccat.nysbc.org/" target="_blank"><img src="./img/nccat_logo.png" width="75" height="75"></a></td>';
	echo '<td style="padding: 0 5px 0 5px;">NCCAT Operations<br>';
}
else {
 	echo '<tr style="background-color:#475e7a;color:white;font-size:18px;font-weight:bold;">';
 	echo '<td><a href="http://semc.nysbc.org/" target="_blank"><img src="./img/semc_logo.png" width="75" height="75"></a></td>';
 	echo '<td style="padding: 0 5px 0 5px;">SEMC Operations<br>';
}
if ($instrumentinfo[0]['description']) echo str_replace('-EF','',$instrumentinfo[0]['description']);
else echo $instrumentinfo[0]['name'].' '.$instrumentinfo[0]['hostname'];
echo '<br>'.$sessioninfo['Purpose'];

echo '</td>';
echo '<td style="padding: 0 25px 0 25px;">Session<br>'.$sessioninfo['Name'].'</td>';
if (strpos($instrumentinfo[0]['description'], 'Krios') !== false) {
	echo '<td><img src="./img/krios.png" width="43" height="75"></a></td>';
	echo '<td style="padding: 0 25px 0 5px;">TFS<br>Titan Krios</td>';
}
if (strpos($imageinfo['camera'], 'GatanK2') !== false) {
	echo '<td><img src="./img/k2.png" width="73" height="75"></a></td>';
	echo '<td style="padding: 0 5px 0 5px;">Gatan<br>K2 Summit<br><div style="font-size:12px;">Direct Detector</div></td>';
} else {
	echo '<td style="padding: 0 5px 0 5px;">'.$imageinfo['camera'].'</td>';
}
echo '</tr>';
echo '</table>';
echo '<table>';
echo '<tr valign="top">';

$expId = $sessionId;
$summary = $leginondata->getSummary($expId);
if (!empty($summary)) {
	$timingstats2 = $leginondata->getPresetTiming($expId);
	$timingstats = $leginondata->getTimingStats($expId);
	//print_r($timingstats);
	$tot_time=0;
	foreach ((array)$timingstats as $t) {
		$images_time[$t['name']]=$t['time'];
		$images_mean[$t['name']]=$t['mean'];
		$images_stdev[$t['name']]=$t['stdev'];
		$images_min[$t['name']]=$t['min'];
		$images_max[$t['name']]=$t['max'];
		$tot_time += $t['time_in_sec'];
	}
	//echo print_r($summary);
	$summary_fields[]="Preset<br/>label";
	$summary_fields[]="Mag (X)";
	$summary_fields[]="Dose<br/>(e<sup>-</sup>/&Aring;<sup>2</sup>)";
	$summary_fields[]="Pixel<br/>size (&Aring;)";
	$summary_fields[]="Dimensions";
	$summary_fields[]="Binning";
	$summary_fields[]="Image<br/>count";
	foreach($summary_fields as $s_f) {
		$table_head.="<th>$s_f</th>";
	}
	echo "<td>";
	echo divtitle("Imaging Summary");
	echo "<table class='paleBlueRows'>\n";
	echo "<tr>". $table_head."</tr>";
	$maxpresetscore = 0.0;
	$maxpresetid = -1;
	$maxpresetarray = array();
	foreach($summary as $s) {
		if($s['dose'] > 0) {
			$dose = number_format($s['dose']/1e20,3);
		} else { $dose = ""; }
		$pixelsize = 0.0;
		$imageinfo = $leginondata->getImageInfoFromPreset($s['presetId']);
		//echo print_r($imageinfo);
		//echo "<br/><br/>";
		$pixelsize = 1e10*$imageinfo['pixelsize']*$imageinfo['binning'];
		if ($pixelsize > 50) {
			$apix = number_format($pixelsize,1);
		} else {
			$apix = number_format($pixelsize,3);
		}
		$dims = $imageinfo['dimx'].'x'.$imageinfo['dimy'];
		if ($imageinfo['binning'] == 1) {
			$presetscore = $imageinfo['dimx']*$imageinfo['dimy']*$s['nb']/$pixelsize;
		} else { $presetscore=0; }
		if ($presetscore > $maxpresetscore) {
			$maxpresetscore = $presetscore;
			$maxpresetid = $s['presetId'];
			$maxpresetarray = $s;
		}
		echo formatArrayHtmlRow(
				$s['name'],
				$s['magnification'],
				$dose,
				$apix,
				$dims,
				$imageinfo['binning'],
				$s['nb']
				);
		$tot_imgs += $s['nb'];
	}
	echo "</table>\n";
	
	echo "<p><b>Total images:</b> $tot_imgs ";
	
	$totalsecs = $leginondata->getSessionDuration($expId);
	$totaltime = $leginondata->formatDuration($totalsecs);
	
	echo "&nbsp;&nbsp;<b>Duration:</b> $totaltime";
}
echo divtitle("Defocus summary");
$ctf = new particledata();
$ctfrundatas = $ctf->getCtfRunIds($expId, True);
$display_keys = array ( 'nb', 'min', 'max', 'avg', 'stddev');
$fields = array('defocus1', 'defocus2',
		//'confidence', 'confidence_d',
		'angle_astigmatism', 'astig_distribution',
		'extra_phase_shift',
		'resolution_80_percent', 'resolution_50_percent', 'ctffind4_resolution');
$stats = $ctf->getCTFStats($fields, $expId);
		
echo displayCTFstats($stats, $display_keys);
echo "<center><a href='./processing/ctfgraph.php?hg=1&expId=$expId&s=1&f=defocus1'>\n";
echo "<img border='0' width='500' height='300' src='./processing/ctfgraph.php?"
."w=800&h=600&hg=1&expId=$expId&s=1&xmax=7e-6&f=defocus1' alt='please wait...'></a></center>\n";
echo '</td>';
echo '<td>';
$icethicknessobj = $leginondata->getObjIceThickness($expId); # see if anything was collected
echo divtitle("Ice thickness summary");
if (!empty($icethicknessobj)) {
	echo "<table border='0'>\n";
	echo "<tr>";
	echo "<td>";
	//echo "<a href='zlp_icegraph.php?Id=$expId?h=256'>";
	echo "<a href='obj_icegraph.php?Id=$expId&w=500&h=580'>";
	echo "<img border='0' src='obj_icegraph.php?Id=$expId&w=500&h=360'>";
	
	echo "</a>\n";
	echo "</td>\n";
	echo "</tr>\n";
	
	
	echo "</table>\n";	
	
} else {
	echo "no Objective Scattering Ice Thickness information available";
}
$imageinfo = $leginondata->getImageInfoFromPreset($summary[0]['presetId']);
echo divtitle("Atlas");
echo "<img border='0' src='getimg.php?session=$expId&id=".$imageinfo['imageId']."&preset=atlas&t=80&sb=1&flt=default&fftbin=a&binning=auto&m=1&r=-1&opt=2&lj=1&psel=2&pcb=d&autoscale=s;5&conly=1&s=500'>";

echo '</td>';
echo '</tr>';
echo '<tr>';
echo '<td colspan=2>';
echo divtitle("References");
echo '<div style="padding:10px;">Leginon: Suloway, C., Pulokas, J., Fellmann, D., Cheng, A., Guerra, F., Quispe, J.,'
.'Stagg, S., Potter, C.S., Carragher, B., 2005. Automated molecular microscopy: the'
.'new Leginon system. J Struct Biol 151, 41-60.'
.'https://doi.org/10.1016/j.jsb.2005.03.010</div>';
echo '<br>';
echo '<div style="padding:10px;">Appion: Lander, G.C.; Stagg, S.M., Voss, N.R., Cheng, A., Fellmann, D., Pulokas,'
.'J., Yoshioka, C., Irving, C., Mulder, A., Lau, P.W., et al. (2009). "Appion: an'
.'integrated, database-driven pipeline to facilitate EM image processing.". Journal of'
.'Structural Biology 166: 95-102. PMID 19263523.</div>';
echo '</td>';
echo '</tr>';
echo '</table>';

//echo '<div>User: '.$sessioninfo['User'].' &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Purpose: '.$sessioninfo['Purpose'].'</div>';
// $base_path = '/gpfs/uploads/semc';
// if(isset($_FILES['leftimage'])){
// 	$errors= array();
// 	$file_name = $_FILES['leftimage']['name'];
// 	$file_size =$_FILES['leftimage']['size'];
// 	$file_tmp =$_FILES['leftimage']['tmp_name'];
// 	$file_type=$_FILES['leftimage']['type'];
// 	$file_ext=strtolower(end(explode('.',$_FILES['leftimage']['name'])));
	
// 	$extensions= array("jpeg","jpg","png");
	
// 	if(in_array($file_ext,$extensions)=== false){
// 		$errors[]="extension not allowed, please choose a JPEG or PNG file.";
// 	}
	
// 	if($file_size > 2097152){
// 		$errors[]='File size must be less than 2 MB';
// 	}
	
// 	if(empty($errors)==true){
// 		move_uploaded_file($file_tmp,$base_path.'_left'.$sessionId.$file_name);
// 	}else{
// 		print_r($errors);
// 	}
// }
// echo '<table border="1">';
// echo '<tr>';
// echo '<td width="500px" height="420px">';
// $list = glob($base_path.'_left'.$sessionId.'*');
// if ($list) {
// 	echo '<img src="file:/'.$list[0].'" title="Remove '.$list[0].' to upload a new image."/>';

// } else {
// echo '<div style="text-align: right; ">';
// echo '<form action="" method="POST" enctype="multipart/form-data">';
// echo '<input type="file" name="leftimage" />';
// echo '<input value="Upload Image" type="submit"/>';
// echo '</form>';
// echo '</div>';
// }
// echo '</td/>';
// echo '<td width="500px" height="420px">';
// echo '<div style="text-align: right; ">';
// echo '<form action="" method="POST" enctype="multipart/form-data">';
// echo '<input type="file" name="rightimage" />';
// echo '<input value="Upload Image" type="submit"/>';
// echo '</form>';
// echo '</div>';
// echo '</td>';
// echo '</tr>';
// echo '</table>';

echo '</center>';
?>
