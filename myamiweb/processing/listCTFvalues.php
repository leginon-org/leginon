<?php
/**
 *      For terms of the license agreement
 *      see  http://ami.scripps.edu/software/leginon-license
 */

# specify a directory that the web server can write to
$scratchdir = "/tmp";

require "inc/particledata.inc";
require "inc/leginon.inc";
require "inc/project.inc";

$expId = $_GET['expId'];
$stackId = $_GET['sId'];
$frealign = $_GET['frealign'];

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
		$res = $particle->getCtfInfoFromImageId($img);
		$imgids[$img]=$res[0];
		# get image dimension & kev
	}
}
$page = $_SERVER['PHP_SELF']."?expId=$expId&sId=$stackId";
if (!$frealign) {
	$page.="&frealign=True";
	echo "<span style='font-size:10pt; font-family:arial;'><a href='$page'>[format for FREALIGN]</a></font></br>\n";
}
else {
	echo "<span style='font-size:10pt; font-family:arial;'><a href='$page'>[original list]</a></font></br>\n";
}

$labelline = "particle  defocus1   defocus2    astig  keV   cs  ampcst";
$lastimgid=$s[0]['imgid'];
# for tracking helices or image numbers
$lasthelix=$s[0]['helixnum'];
$toth=1;
if ($lasthelix) $labelline.= "   hnum   angle";

$fname = "ctfvals-$expId-$stackId.txt";
$fpath = "$scratchdir/$fname";
unlink($fpath);

if (!$frealign)
	$format = "%7d  %9.6f  %9.6f  %7.3f  %3d  %3.1f  %6.4f %s\n";
else
	$format = "%7d%8.3f%8.3f%8.3f%8.3f%8.3f%9.1f%5d%9.1f%9.1f%8.2f%7.2f%8.2f\n";

$errornum=0;

foreach ($s as $part) {
	$p = $part['particle'];
	$img = $part['imgid'];
	$df1 = abs($imgids[$img]['defocus1'])*1e6;
	$df2 = abs($imgids[$img]['defocus2'])*1e6;
	$ang = -$imgids[$img]['angle_astigmatism'];
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

	if ($frealign) 
		$l = sprintf($format,$p,0,0,0,0,0,10000,$toth,$df1*1e4,$df2*1e4,$ang,0,0);
	else {
		$l = sprintf($format,$p,$df1,$df2,$ang,$kev,$cs,$amp,$helixStuff);
	}
	if ($df1 == 0) {
		file_put_contents($fpath,"ERROR\n",FILE_APPEND | LOCK_EX);
		$errornum++;
	}
	else file_put_contents($fpath,$l,FILE_APPEND | LOCK_EX);
}
	$downloadLink = "(<a href='download.php?file=$fpath&expId=$expId'>\n";
echo "<br><b>".$downloadLink."Download the file</a></b><br>\n";
if ($errornum>0) echo "<br>Warning! File contains $errornum errors\n";
?>

