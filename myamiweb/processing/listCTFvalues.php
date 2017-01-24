<?php
/**
 *      For terms of the license agreement
 *      see  http://leginon.org
 */

# specify a directory that the web server can write to
$scratchdir = "/tmp";

require_once "inc/particledata.inc";
require_once "inc/leginon.inc";
require_once "inc/project.inc";

$expId = $_GET['expId'];
$stackId = $_GET['sId'];
$acerunId = ($_GET['ctfrunId']) ? $_GET['ctfrunId']:'';
$ff = ($_GET['ff']) ? $_GET['ff'] : 'FREALIGN';

$particle = new particledata();
$leginon = new leginondata();

$cs = $leginon->getCsValueFromSession($expId);
$apix=$particle->getStackPixelSizeFromStackId($stackId)*1e10;
## get all the particle pick information for each stack particle
$s=$particle->getParticlePicksFromStack($stackId);
## create a list of all imgids in stack
$imgids = array();

## get image info from first particle, assume all the same
$imginfo = $leginon->getImageInfo($s[0]['imgid']);
$pixelsize = $imginfo['pixelsize']*1e10;
$kev = $imginfo['high tension']/1000;
$dimx = $imginfo['dimx'];
$dimy = $imginfo['dimy'];

foreach ($s as $part) {
	$img=$part['imgid'];
#	if ($img < 693213) continue;
	if (!array_key_exists($img,$imgids)) {
		# CTF information
		$res = $particle->getCtfInfoFromImageId($img,false,'',$acerunId);
		$imgids[$img]=$res[0];
		# get image dimension & kev
	}
}
$page = $_SERVER['PHP_SELF']."?expId=$expId&sId=$stackId&ff";
if ($ff!='FREALIGN') {
	echo "<span style='font-size:10pt; font-family:arial;'><a href='$page=FREALIGN'>[format for FREALIGN]</a></font></br>\n";
}
if ($ff!='RELION') {
	echo "<span style='font-size:10pt; font-family:arial;'><a href='$page=RELION'>[format for RELION]</a></font></br>\n";
}
if ($ff!='EMAN2') {
	echo "<span style='font-size:10pt; font-family:arial;'><a href='$page=EMAN2'>[format for EMAN2]</a></font></br>\n";
}

$labelline = "particle  defocus1   defocus2    astig  keV   cs  ampcst";
$lastimgid=$s[0]['imgid'];
# for tracking helices or image numbers
$lasthelix=$s[0]['helixnum'];
$toth=1;
if ($lasthelix) $labelline.= "   hnum   angle";

$fname = "ctf$ff-$expId-$stackId.txt";
$fpath = "$scratchdir/$fname";
if (file_exists($fpath)) unlink($fpath);

if ($ff=='FREALIGN')
	$format = "%7d%8.3f%8.3f%8.3f%8.3f%8.3f%9.1f%5d%9.1f%9.1f%8.2f%7.2f%8.2f\n";
elseif ($ff=='RELION')
	$format = "%d@start.mrcs mic%d %5d %5d %7.2f %3d %3.1f %6.4f\n";
elseif ($ff=='EMAN2')
	$format = "%7d  %9.6f  %9.6f  %7.3f  %3d  %3.1f  %6.4f %s\n";

$errornum=0;

#for relion header
if ($ff=='RELION') {
	$l = "data_\nloop_\n_rlnImageName #1\n_rlnMicrographName #2\n_rlnDefocusU #3\n";
	$l.= "_rlnDefocusV #4\n_rlnDefocusAngle #5\n_rlnVoltage #6\n";
	$l.= "_rlnSphericalAberration #7\n_rlnAmplitudeContrast #8\n";
	file_put_contents($fpath,$l,FILE_APPEND | LOCK_EX);
}

foreach ($s as $part) {
	$p = $part['particle'];
	$img = $part['imgid'];
	$df1 = abs($imgids[$img]['defocus1'])*1e6;
	$df2 = abs($imgids[$img]['defocus2'])*1e6;
	$ang = $imgids[$img]['angle_astigmatism'];
	$amp = $imgids[$img]['amplitude_contrast'];
	$tiltaxis = $imgids[$img]['tilt_axis_angle'];
	$tiltangle = $imgids[$img]['tilt_angle'];
	# if tilted, get df based on position in micrograph
	# NOTE THAT TILTS ARE BASED ON CTFTILT < v1.7
	if ($tiltaxis or $tiltangle) {
		$CX = $dimx/2;
		$CY = $dimy/2;

		if ($tiltaxis) {
			$N1 = -1.0*sin(deg2rad($tiltaxis));
			$N2 = cos(deg2rad($tiltaxis));
		}
		else {
			$N1=0.0;
			$N2=1.0;
		}

		$NX = $part['xcoord'];
		$NY = $part['ycoord'];

		# flip Y axis due to reversed y coords
		# THIS IS ALSO ASSUMING CTFTILT < v1.7
		$NY = $dimy-$NY;

		$DX = $CX - $NX;
		$DY = $CY - $NY;
		$DF = 1e-4 * ($N1*$DX + $N2*$DY) * $pixelsize * tan(deg2rad($tiltangle));
		$df1 = $df1+$DF;		
		$df2 = $df2+$DF;		
	}	
	$helixStuff='';
	if ($lasthelix) {
		$hnum = $part['helixnum'];
		$angle = $part['angle'];
		if ($lastimgid!=$img || $lasthelix!=$hnum) $toth++;
		$helixStuff = sprintf(" %5d %7.2f",$toth,$angle);
		$lasthelix=$hnum;
	}
	elseif ($lastimgid!=$img) $toth++;
	$lastimgid=$img;

	if ($ff=='FREALIGN')
		$l = sprintf($format,$p,0,0,0,0,0,10000,$toth,$df1*1e4,$df2*1e4,$ang,0,0);
	elseif ($ff=='RELION')
		$l = sprintf($format,$p,$toth,$df1*1e4,$df2*1e4,$ang,$kev,$cs,$amp);
	elseif ($ff=='EMAN2')
		$l = sprintf($format,$p,$df1,$df2,$ang,$kev,$cs,$amp,$helixStuff);

	if ($df1 == 0) {
		file_put_contents($fpath,"ERROR: $img\n",FILE_APPEND | LOCK_EX);
		$errornum++;
	}
	else file_put_contents($fpath,$l,FILE_APPEND | LOCK_EX);
}
	$downloadLink = "<a href='download.php?file=$fpath&expId=$expId'>\n";
echo "<br><b>".$downloadLink."Download the $ff file</a></b><br>\n";
if ($errornum>0) echo "<br>Warning! File contains $errornum errors\n";
?>

