<html>
<head>
<link rel="stylesheet" type="text/css" href="css/viewer.css"> 
<link rel="stylesheet" type="text/css" href="css/view.css">
<title>Leginon Image Viewer</title>
</head>


<?
echo "<pre>";
// print_r($_POST);
echo "</pre>";
require ('inc/leginon.inc');

// --- View setup based on the browser and platform type --- //
if (browser('b') =='Netscape' && strstr(browser('p'), 'Win')) {
	$mvtextsize=15;
	$cvcols=15;
	$mvcols=31;
	$v1cols=21;
	$v2cols=21;
} else if (browser('b')=='MSIE') { 
	$cvcols=35;
	$mvtextsize=30;
	$mvcols=60;
	$v1cols=47;
	$v2cols=47;
} else if (!(browser('b') =='Netscape' && (browser('v')< 5))) {
	$cvcols=35;
	$mvtextsize=30;
	$mvcols=60;
	$v1cols=47;
	$v2cols=47;
} else { 
	$cvcols=25;
	$mvtextsize=35;
	$mvcols=42;
	$v1cols=32;
	$v2cols=32;
}

// --- Viewer options
$sep = " | ";


// --- Set  experimentId
$lastId = $leginondata->getLastSessionId();
$expId = (empty($expId)) ? $lastId : $expId;

// --- Get all session and session Ids
$experiment = array();
$lexpId = array();
$re = $leginondata->getSessions();
$i=0;
foreach ($re['sessions'] as $r){
	if (!empty($r))
		if (!in_array($r, $experiment)) {
			$experiment[] = $r;
			$lexpId[] = $re['ids'][$i];
		}
	$i++;
}
$nrexp = sizeof($experiment);


// --- Get data type list
$datatypes = $leginondata->getDatatypes($expId);
// print_r($datatypes);
$def_label = $datatypes[0];
// --- Add foc pow 
$datatypes[] = "focpow";


// --- Get current user preferences
$v1sel = (empty($_POST[v1sel])) ? $_POST[v1list] : $_POST[v1sel];
$v1sel = (empty($v1sel)) ? $def_label : $v1sel;
// $v1sel = (empty($_POST[v1sel])) ? $def_label : $_POST[v1sel];
// $v2sel = (empty($_POST[v2sel])) ? $def_label : $_POST[v2sel];
// $mvsel = (empty($_POST[mvsel])) ? $def_label : $_POST[mvsel];
$v2sel = (empty($_POST[v2sel])) ? $_POST[v2list] : $_POST[v2sel];
$v2sel = (empty($v2sel)) ? $def_label : $v2sel;

$mvsel = (empty($_POST[mlist])) ? $def_label : $_POST[mlist];


$v1view = (empty($_POST[v1view])) ? "on" : $_POST[v1view];
$v2view = (empty($_POST[v2view])) ? "on" : $_POST[v2view];

$Rfile = $leginondata->getFilenames($expId, $mvsel);

if($Rfile) {
	$nrows=mysql_num_rows($Rfile);
	while ($row = mysql_fetch_row($Rfile)) {
		$fileId[]=$row[0]; 
		$r = explode("/",$row[1]);
		$file[]=$r[sizeof($r)-1]; 
	}
}


// --- Get images type list
$db = new mysql ('cronus1', 'anonymous', '' ,'dbemdata');
$db->connect_db();

// if ($mvsel=='' ) $t1=$mvImg; else $t1=$mvsel;
// if ($v1sel=='' ) $t2=$v1Img; else $t2=$v1sel;
// if ($v2sel=='' ) $t3=$v2Img; else $t3=$v2sel;

// --- Set Presets
if ($mvMag=='Y' || $mvDose=='Y' || $mvDefocus=='Y' || $mvPixelSize=='Y') 
	$mvpre=1;
if ($v1Mag=='Y' || $v1Dose=='Y' || $v1Defocus=='Y' || $v1PixelSize=='Y') 
	$v1pre=1;
if ($v2Mag=='Y' || $v2Dose=='Y' || $v2Defocus=='Y' || $v2PixelSize=='Y') 
	$v2pre=1;

// --- Update Comments for each Main View Images
require ('inc/check.viewer.inc');

mysql_close();

// --- View preferences Flags
// require('viewpref.inc');

$v1Id=1;
$v2Id=1;
$mvId=1;
$imgv1='getparentimgtarget.php';
$imgv2='getparentimgtarget.php';
$imgmv='getparentimgtarget.php';
// $imgmv='mrc2string.php';

// --- $view presets
$mvpre = 1;
$v1pre = 1;
$v2pre = 1;


?>

<script LANGUAGE="javascript" SRC="js/viewer.js">
</script>
<script> 
<!-- 
  <?

  echo "var jsprefId = \"$prefId\"; \n";
  echo "var jsName = \"$user\"; \n";
  echo "var jsexpId = \"$expId\"; \n";
  echo "var path = \"$path\"; \n";
  echo "var jsfileId = \"$fileId[0]\"; \n";
  echo "var jsfile = \"$file[0]\"; \n";
  echo "var jsimgmv = \"".$imgmv."\"; \n";
  echo "var jsmvId   = \"".trim($mvId)."\"; \n";
  echo "var jstmv   = \"".trim($t1)."\"; \n";
  echo "var jsimgv1 = \"".$imgv1."\"; \n";
  echo "var jsv1Id   = \"".trim($v1Id)."\"; \n";
  echo "var jstv1   = \"".trim($t2)."\"; \n";
  echo "var jsimgv2 = \"".$imgv2."\"; \n";
  echo "var jsv2Id   = \"".trim($v2Id)."\"; \n";
  echo "var jstv2   = \"".trim($t3)."\"; \n";
  echo "var jspremv = \"".trim($mvpre)."\"; \n";
  echo "var jsprev1   = \"".trim($v1pre)."\"; \n";
  echo "var jsprev2   = \"".trim($v2pre)."\"; \n";

  ?>


function init() {
     var currentfile="";
 if (document.listform.allfile.length !=0) {
     for (var i = 0; i < document.listform.allfile.length; i++) {
      if (document.listform.allfile.options[i].defaultSelected == true) {
          document.listform.allfile.options[i].selected=true;
          currentfile=document.listform.allfile.options[document.
          listform.allfile.selectedIndex].text;
          window.document.listform.filename_text.value=currentfile; 
      <? if ($save or $delete) {
         echo "incIndex(); \n"; } ?>
      } 
     }
     if (currentfile=="") {
          currentfile=document.listform.allfile.options[0].text;
          document.listform.allfile.options[0].selected=true;
          window.document.listform.filename_text.value=currentfile; 
     }
     toggleimage('v1target_bt', 'target_bt');
     toggleimage('v2target_bt', 'target_bt');
     toggleimage('mvtarget_bt', 'target_bt');
     toggleimage('v1scale_bt', 'scale_bt');
     toggleimage('v2scale_bt', 'scale_bt');
     toggleimage('mvscale_bt', 'scale_bt');
     newfile();
     GetPresets();
 } 
} 

 // --> 
</script> 

<body bgcolor="#FFFFFF" onload="init()">

<form method="post" name="listform" id="adjust" onsubmit="return sendForm('viewer.php', 'prefId')">
 <input type="hidden" name="ncfid" value="">
  <table border="0" cellpadding="1" cellspacing="1" height="600" width="950">
      <tr>
	<td vAlign="bottom" height="25" ><b>Experiment</b></td>
        <td vAlign="bottom" bgColor="#FFFFFF" colSpan="2" rowSpan="3" height="10" >
	<?
	$sessioninfo = $leginondata->getSessionInfo($expId);
	echo $sessioninfo['Purpose'];
	?>
	</td>
      </tr>
      <tr>
	<td><select name="expId" onchange="newexp()">
			<?
			for ($i=0; $i<$nrexp; $i++) {
				if ($lexpId[$i]==$expId) $s[$i]='selected'; else $s[$i]='';
         			echo "<option value=$lexpId[$i] $s[$i]>$experiment[$i] \n"; 
      			} 
			?>
		</select>
	</td>
      </tr>
      <tr>
	<td><b>Image List</b></td>
      </tr>
      <tr vAlign="top">
	<td height="462" rowSpan="2" >
		<select name="allfile" onchange="newfile();
		GetPresets(); " size="40">
			<?
			for ($i=0; $i<$nrows; $i++) {
				if ($fileId[$i]==$allfile ) $s[$i]='selected'; else $s[$i]='';
				echo "<option value=$fileId[$i] $s[$i]>".substr($file[$i],0,strlen($file[$i])-4)."\n"; 
			} 
			?> 
		</select>
	</td>
<? $v1height = ($v1view=="off") ? ' height="16" ' : ' height="256" ' ?>
	<td vAlign="top" <?=$v1height?>>
<?
require('inc/view1.inc');
?>
	</td>
	<td height="462" width="778" rowspan="2">
<?
require('inc/mainview.inc');
?>
	</td>
      </tr>
      <tr vAlign="top">
	<td vAlign="top" height="256">
<?
require('inc/view2.inc');
?>
	</td>
      </tr>
    </table>
</form>
</body>
</html>
