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
$end_summary = end($summary);
$imageinfo = $leginondata->getImageInfoFromPreset($end_summary['presetId']);
$instrumentinfo = $leginondata->getInstrumentInfo($sessioninfo['InstrumentId']);

echo "<link rel='stylesheet' href='css/neiladd.css' />";
echo "<title>".$sessioninfo['Name']." Report</title>";
echo '<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/1.5.3/jspdf.debug.js" integrity="sha384-NaWTHo/8YCBYJ59830LTz/P4aQZK1sS0SneOgAvhsIl3zBu8r9RevNg5lHCHAuQ/" crossorigin="anonymous"></script>';
echo '<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/0.4.1/html2canvas.js"></script>';
echo '<script src="tinymce/tinymce.min.js"></script>';
echo '<script type="text/javascript">';
$text = <<<EOT
tinymce.init({
    selector: "textarea#mytextarea",
    plugins: [
         "advlist autolink link image lists charmap print preview hr anchor pagebreak",
         "searchreplace wordcount visualblocks visualchars insertdatetime media nonbreaking",
         "table contextmenu directionality emoticons paste textcolor responsivefilemanager code"
   ],
   toolbar1: "undo redo | bold italic underline | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | styleselect",
   toolbar2: "| responsivefilemanager | link unlink anchor | image media | forecolor backcolor  | print preview code ",
   image_advtab: true ,
EOT;
echo $text;
$inline = $_GET["inline"];
if ($inline) echo 'inline: true,';
echo 'external_filemanager_path:"'.BASE_URL.'filemanager/",'
   .' filemanager_title:"Responsive Filemanager" ,'
   .' external_plugins: { "filemanager" : "'.BASE_URL.'filemanager/plugin.min.js"}'
 .' });';
echo '</script>';
	
//echo '<pre>'; print_r($sessioninfo); echo '</pre>';
//echo '<pre>'; print_r($imageinfo); echo '</pre>';
//echo '<pre>'; print_r($summary); echo '</pre>';
//echo '<pre>'; print_r($instrumentinfo); echo '</pre>';
echo PHP_EOL;
echo '<center>';
echo '<table cellspacing="0" width=100% >';

if (stripos($sessioninfo['Purpose'], 'nccat') !== false){
	echo '<tr style="background-color:#d4e0ee; color:black;font-size:18px;font-weight:bold;">';
	echo '<td style="padding: 0 5px 0 50px;"><a href="http://nccat.nysbc.org/" target="_blank"><img src="./img/nccat_logo.png" width="75" height="75"></a></td>';
	echo '<td style="padding: 0 5px 0 5px;">NCCAT Operations<br>';
}
elseif (defined("SEMC")) {
 	echo '<tr style="background-color:#475e7a;color:white;font-size:18px;font-weight:bold;">';
 	echo '<td style="padding: 0 5px 0 50px;"><a href="http://semc.nysbc.org/" target="_blank"><img src="./img/semc_logo.png" width="75" height="75"></a></td>';
 	echo '<td style="padding: 0 5px 0 5px;">SEMC Operations<br>';
}
else{
	echo '<tr><td>';
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
		//if ($imageinfo['binning'] == 1) {
			$presetscore = $imageinfo['dimx']*$imageinfo['dimy']*$s['nb']/$pixelsize;
		//} else { $presetscore=0; }
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
		
$mytextarea = "";
if($_SERVER['REQUEST_METHOD'] === 'POST'){
		if (!$ctf->mysql->SQLTableExists("poster")){
			$query = "CREATE TABLE IF NOT EXISTS poster (
            expId INT(11) NOT NULL,
            textarea TEXT NOT NULL,
			PRIMARY KEY (expId));";
			$ctf->mysql->SQLQuery($query);
		}
		$data['expId']=$expId;
		$data['textarea']=$_POST['mytext'];
		$mytextarea = $_POST['mytext'];
		
		$q = "SELECT textarea from poster WHERE expId = $expId";
		$r = $ctf->mysql->getSQLResult($q);
		if ($r) {
			$ctf->mysql->SQLUpdate('poster',$data);
		}
		else{
			$ctf->mysql->SQLInsert('poster',$data);
		}
		
}
elseif ($ctf->mysql->SQLTableExists("poster")){
	$q = "SELECT textarea from poster WHERE expId = $expId";
	$t = $ctf->mysql->getSQLResult($q);
	$mytextarea= $t[0]['textarea'];	
}

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

$gr_imageinfo = $leginondata->getImageInfoFromPreset($summary[0]['presetId']);
echo divtitle("Atlas");
echo "<img border='0' src='getimg.php?session=$expId&id=".$gr_imageinfo['imageId']."&preset=atlas&t=80&sb=1&flt=default&fftbin=a&binning=auto&m=1&r=-1&opt=2&lj=1&psel=2&pcb=d&autoscale=s;5&conly=1&s=500'>";

echo '</td>';
echo '</tr>';
echo '<tr>';
echo '<td colspan=2>';
echo divtitle("Experimental setup");
$presetdata = $leginondata->getAllPresetData($maxpresetid);
echo '<table width=99% class="paleBlueRows" style="border-spacing: 45px 0px">';
echo '<tr>';
echo '<td>';
echo 'TEM: <div style="float:right ">'.$imageinfo['scope'].'</div>';
echo '</td>';
echo '<td>';
echo 'Camera: <div style="float:right ">'.$imageinfo['camera'].'</div>';
echo '</td>';
echo '</tr>';
echo '<tr>';
echo '<td>';
echo 'Magnification: <div style="float:right ">'.$imageinfo['magnification'].'</div>';
echo '</td>';
echo '<td>';
echo 'Dimension: <div style="float:right ">'.$presetdata['SUBD|dimension|x'].' x '.$presetdata['SUBD|dimension|y'].'</div>';
echo '</td>';
echo '</tr>';
echo '<tr>';
echo '<td>';
echo 'High tension (kV): <div style="float:right ">'.intval($imageinfo['high tension']/1000).'</div>';
echo '</td>';
echo '<td>';
echo 'Binning: <div style="float:right ">'.$presetdata['SUBD|binning|x'].' x '.$presetdata['SUBD|binning|y'].'</div>';
echo '</td>';
echo '</tr>';
echo '<tr>';
echo '<td>';
$defdata = $leginondata->getMinMaxDefocusForPreset($presetdata['name'], $expId);
$defmin = number_format(-1e6*$defdata['maxdef'], 1);
$defmax = number_format(-1e6*$defdata['mindef'], 1);
echo 'Defocus range (µm): <div style="float:right ">'.$defmin.' - '.$defmax .'</div>';
echo '</td>';
echo '<td>';
echo 'Exposure time (ms): <div style="float:right ">'.$imageinfo['exposure time'].'</div>';
echo '</td>';
echo '</tr>';

echo '<tr>';
echo '<td>';
echo 'Spot size: <div style="float:right ">'.$presetdata['spot size'].'</div>';
echo '</td>';
echo '<td>';
echo 'Pixel size (Å): <div style="float:right ">'.number_format($imageinfo['pixelsize']*$presetdata['SUBD|binning|x']*1e10,4).'</div>';
echo '</td>';
echo '</tr>';
echo '<tr>';
echo '<td>';
echo 'Intensity: <div style="float:right ">'.$presetdata['intensity'].'</div>';
echo '</td>';
echo '<td>';
echo 'Dose rate (e<sup>-</sup>/&Aring;<sup>2</sup>/s): <div style="float:right ">'.number_format($maxpresetarray['dose']/$presetdata['exposure time']/1e17, 2).'</div>';
echo '</td>';
echo '</tr>';

echo '<tr>';
echo '<td>';
echo 'Cs (mm): <div style="float:right ">'.number_format($instrumentinfo[0]['cs']*1000,3).'</div>';
echo '</td>';
echo '<td>';
echo 'Total dose (e<sup>-</sup>/&Aring;<sup>2</sup>): <div style="float:right ">'.number_format($maxpresetarray['dose']/1e20,2).'</div>';
echo '</td>';
echo '</tr>';
echo '<tr>';

$x = ($presetdata['energy filter']== 1) ? "yes": "no";
echo '<tr>';
echo '<td>';
echo 'Energy filtered: <div style="float:right ">'.$x.'</div>';
echo '</td>';

echo '<td>';
echo 'Frame rate (ms): <div style="float:right ">'.number_format($presetdata['frame time'],2).'</div>';
echo '</td>';
echo '</tr>';
echo '<td>';
$x = ($presetdata['energy filter']== 1) ? $presetdata['energy filter width']: "None";
echo 'Energy filter width: <div style="float:right ">'.$x.'</div>';
echo '</td>';
echo '<td>';
echo 'Total frames: <div style="float:right ">'.intval(round($presetdata['exposure time']/$presetdata['frame time'],0)).'</div>';
echo '</td>';
echo '</tr>';

echo '<table>';

echo '<tr>';
echo '<td colspan=2>';
echo '<form method="post">';
if ($inline) echo '<div ';
else echo '<textarea ';
if (empty($mytextarea)) {
	$outDir = getBaseAppionPath($sessioninfo).'/csLIVE/*.png';
	foreach (glob($outDir) as $filename) {
		if (strpos($filename, '2dclasses')) {
			$mytextarea .="<img width='100%' src='processing/download.php?expId=".$expId."&file=".$filename."'/><br>";
		}
		else {
			$mytextarea .="<img src='processing/download.php?expId=".$expId."&file=".$filename."'/><br>";
		}
	}
	$class_file = getBaseAppionPath($sessioninfo).'/csLIVE/class_info';
	if (file_exists($class_file)) {
		$file = file_get_contents($class_file);
		$file = str_replace("==", "<br>", $file);
		$mytextarea .="<h5>2D Classes Info</h5>".$file;
	}
}
echo 'id="mytextarea" name="mytext">'.$mytextarea;
if ($inline) echo '</div>';
else {
	echo '</textarea>';
	echo '<input type="submit" value="Save" />';
}
echo '</form>';
echo '</td>';
echo '</tr>';
echo '<tr>';
echo '<td colspan=2>';
echo divtitle("Experimental Methods");
$microscope = $imageinfo['scope'];
$kv = intval($imageinfo['high tension']/1000);
$camera = $imageinfo['camera'];
$pixelsize = number_format($imageinfo['pixelsize']*1e10,4); ;
$mag = number_format($presetdata['magnification'],0);
$dosepersec = number_format($maxpresetarray['dose']/$presetdata['exposure time']/1e17, 2);
$exposure = number_format($presetdata['exposure time']/1000,2);
$totaldose = number_format($maxpresetarray['dose']/1e20,2);
$frametime = number_format($presetdata['frame time']/1000,2);
$numframes = intval(round($presetdata['exposure time']/$presetdata['frame time'],0));
$numimages = $maxpresetarray['nb'];
$defmin = number_format(-1e6*$defdata['maxdef'], 1);
$defmax = number_format(-1e6*$defdata['mindef'], 1);

echo opendivbubble();

echo "<p>";

echo "$microscope operated at $kv kV with a $camera imaging system collected at {$mag}X nominal magnification.
The calibrated pixel size of $pixelsize &Aring; was used for processing.";

echo "</p><p>";

echo "Movies were collected using Leginon (Suloway et al., 2005) at a dose
rate of $dosepersec e<sup>-</sup>/&Aring;<sup>2</sup>/s with a total exposure of $exposure seconds,
for an accumulated dose of $totaldose e<sup>-</sup>/&Aring;<sup>2</sup>. Intermediate frames were recorded
every $frametime seconds for a total of $numframes frames per micrograph. A total of $numimages images were
collected at a nominal defocus range of $defmin &ndash; $defmax &mu;m.";

echo "</p>";

echo '</div>';
echo '</td>';
echo '</tr>';

if (stripos($sessioninfo['Purpose'], 'nccat') !== false){
	echo '<tr>';
	echo '<td colspan=2>';
	echo divtitle("Acknowledgement");
	echo '<div style="padding:10px">'
	.' Some of this work was performed at the National'
	.' Center for CryoEM Access and Training (NCCAT) and the Simons'
	.' Electron Microscopy Center located at the New York Structural Biology'
	.' Center, supported by the NIH Common Fund Transformative High'
	.' Resolution Cryo-Electron Microscopy program (U24 GM129539), and by'
	.' grants from the Simons Foundation (SF349247) and NY State.</div>';
	echo '</td>';
	echo '</tr>';
}
elseif (defined("ACKNOWLEDGEMENTS")) {
	echo '<tr>';
	echo '<td colspan=2>';
	echo divtitle("Acknowledgement");
	echo '<div style="padding:10px">';
	echo ACKNOWLEDGEMENTS;
	echo '</div>';
	echo '</td>';
	echo '</tr>';											
}
echo '<tr>';
echo '<td colspan=2>';
echo divtitle("References");
echo '<div style="padding:10px;">Leginon: Suloway, C., Pulokas, J., Fellmann, D., Cheng, A., Guerra, F., Quispe, J.,'
.' Stagg, S., Potter, C.S., Carragher, B., 2005. Automated molecular microscopy: the'
.' new Leginon system. J Struct Biol 151, 41-60.'
.' https://doi.org/10.1016/j.jsb.2005.03.010</div>';
echo '<div style="padding:10px;">Appion: Lander, G.C.; Stagg, S.M., Voss, N.R., Cheng, A., Fellmann, D., Pulokas,'
.' J., Yoshioka, C., Irving, C., Mulder, A., Lau, P.W., et al. (2009). "Appion: an'
.' integrated, database-driven pipeline to facilitate EM image processing.". Journal of'
.' Structural Biology 166: 95-102. PMID 19263523.</div>';
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
echo '</td>';
echo '</tr>';
echo '</table>';

$text = <<<EOT
<script type="text/javascript">
function PDFFromHTML() {
var doc = new jsPDF('p','pt','a4');
//var iframe = document.getElementById("mytextarea_ifr");
//document.body.appendChild(iframe);
doc.addHTML(document.body,function() {
    doc.save('{$sessioninfo['Name']}_report.pdf');
});
};
EOT;
echo $text;
//echo 'doc.output("dataurlnewwindow");}';
//echo 'doc.save("'.$sessioninfo['Name'].'_report.pdf");}';
if ($inline) echo 'PDFFromHTML()';
echo '</script>';
if (!$inline) echo '<a class="button" href="'.$_SERVER['PHP_SELF'].'?expId='.$expId.'&inline=1">Download PDF</a>';
echo '</center>';
?>
