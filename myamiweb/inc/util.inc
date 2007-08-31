<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

define("USR_BROWSER_AGENT", trim(browser('b')));
define("USR_PLATFORM_AGENT", trim(browser('p')));
//--- Detect Browser, Platform
function browser($n) 
/* {{{ */
{ 
 global $HTTP_USER_AGENT, $BName, $BVersion, $BPlatform; 

 // Browser 
 if(eregi("(opera) ([0-9]{1,2}.[0-9]{1,3}){0,1}",$HTTP_USER_AGENT,$match) || eregi("(opera/)([0-9]{1,2}.[0-9]{1,3}){0,1}",$HTTP_USER_AGENT,$match)) 
 { 
 $BName = "Opera"; $BVersion=$match[2]; 
 } 
 elseif(eregi("(konqueror)/([0-9]{1,2}.[0-9]{1,3})",$HTTP_USER_AGENT,$match)) 
 { 
 $BName = "Konqueror"; $BVersion=$match[2]; 
 } 
 elseif(eregi("(lynx)/([0-9]{1,2}.[0-9]{1,2}.[0-9]{1,2})",$HTTP_USER_AGENT,$match)) 
 { 
 $BName = "Lynx "; $BVersion=$match[2]; 
 } 
 elseif(eregi("(links) \(([0-9]{1,2}.[0-9]{1,3})",$HTTP_USER_AGENT,$match)) 
 { 
 $BName = "Links "; $BVersion=$match[2]; 
 } 
 elseif(eregi("(msie) ([0-9]{1,2}.[0-9]{1,3})",$HTTP_USER_AGENT,$match)) 
 { 
 $BName = "MSIE "; $BVersion=$match[2]; 
 } 
 elseif(eregi("(netscape6)/(6.[0-9]{1,3})",$HTTP_USER_AGENT,$match)) 
 { 
 $BName = "Netscape "; $BVersion=$match[2]; 
 } 
 elseif(eregi("mozilla/5",$HTTP_USER_AGENT)) 
 { 
 $BName = "Netscape"; $BVersion="Unknown"; 
 } 
 elseif(eregi("(mozilla)/([0-9]{1,2}.[0-9]{1,3})",$HTTP_USER_AGENT,$match)) 
 { 
 $BName = "Netscape "; $BVersion=$match[2]; 
 } 
 elseif(eregi("w3m",$HTTP_USER_AGENT)) 
 { 
 $BName = "w3m"; $BVersion="Unknown"; 
 } 
 else{$BName = "Unknown"; $BVersion="Unknown";} 

 // System 
 if(eregi("linux",$HTTP_USER_AGENT)) 
 { 
 $BPlatform = "Linux"; 
 } 
 elseif(eregi("win32",$HTTP_USER_AGENT)) 
 { 
 $BPlatform = "Windows"; 
 } 
 elseif((eregi("(win)([0-9]{2})",$HTTP_USER_AGENT,$match)) || (eregi("(windows) ([0-9]{2})",$HTTP_USER_AGENT,$match))) 
 { 
 $BPlatform = "Windows $match[2]"; 
 } 
 elseif(eregi("(winnt)([0-9]{1,2}.[0-9]{1,2}){0,1}",$HTTP_USER_AGENT,$match)) 
 { 
 $BPlatform = "Windows NT $match[2]"; 
 } 
 elseif(eregi("(windows nt)(
 ){0,1}([0-9]{1,2}.[0-9]{1,2}){0,1}",$HTTP_USER_AGENT,$match)) 
 { 
 $BPlatform = "Windows NT $match[3]"; 
 } 
 elseif(eregi("mac",$HTTP_USER_AGENT)) 
 { 
 $BPlatform = "Macintosh"; 
 } 
 elseif(eregi("(sunos) ([0-9]{1,2}.[0-9]{1,2}){0,1}",$HTTP_USER_AGENT,$match)) 
 { 
 $BPlatform = "SunOS $match[2]"; 
 } 
 elseif(eregi("(beos) r([0-9]{1,2}.[0-9]{1,2}){0,1}",$HTTP_USER_AGENT,$match)) 
 { 
 $BPlatform = "BeOS $match[2]"; 
 } 
 elseif(eregi("freebsd",$HTTP_USER_AGENT)) 
 { 
 $BPlatform = "FreeBSD"; 
 } 
 elseif(eregi("openbsd",$HTTP_USER_AGENT)) 
 { 
 $BPlatform = "OpenBSD"; 
 } 
 elseif(eregi("irix",$HTTP_USER_AGENT)) 
 { 
 $BPlatform = "IRIX"; 
 } 
 elseif(eregi("os/2",$HTTP_USER_AGENT)) 
 { 
 $BPlatform = "OS/2"; 
 } 
 elseif(eregi("plan9",$HTTP_USER_AGENT)) 
 { 
 $BPlatform = "Plan9"; 
 } 
 elseif(eregi("unix",$HTTP_USER_AGENT) || eregi("hp-ux",$HTTP_USER_AGENT)) 
 { 
 $BPlatform = "Unix"; 
 } 
 elseif(eregi("osf",$HTTP_USER_AGENT)) 
 { 
 $BPlatform = "OSF"; 
 } 
 else{$BPlatform = "Unknown";} 


if ($n=='b') {
$rval=$BName;
} elseif ($n=='v') {
$rval=$BVersion;
} elseif ($n=='p') {
$rval=$BPlatform;
} elseif ($n=='t') {
$rval=$BName." ".$BVersion." ".$BPlatform;
}
return $rval;
} 
/* }}} */

// --- iconlink, a PHP class to display Icons

class iconlink {

	var $links = array();
	var $titles = array();
	var $subtitles = array();
	var $images = array();
	var $targets = array();
	var $imagepath = "";
	var $align = 'center';
	var $cols = 3;
	var $onimg = "_on.gif";
	var $offimg = "_off.gif";

	function addlink($link, $title, $subtitle='', $image='', $target='_blank') {
		$this->links[] = $link;
		$this->titles[] = $title;
		$this->subtitles[] = $subtitle;
		$this->images[] = $image;
		$this->targets[] = $target;
	}

	function setImagePath($path) {
		$this->imagepath=$path;
	}

	function getScript() {
		$crlf="\n";
		$script = "<script><!-- \n";
		for ($i=0; $i<count($this->links); $i++) {
			if (!empty($this->images[$i]))
			  $script .= "link".$i."_off = new Image();".$crlf
			  ."link".$i."_off.src = '".$this->imagepath.$this->images[$i].$this->offimg."';".$crlf
			  ."link".$i."_on = new Image();".$crlf
			  ."link".$i."_on.src = '".$this->imagepath.$this->images[$i].$this->onimg."';".$crlf;
		}
		$script .= $crlf
		. 'function mousein(num) { '.$crlf
	 	. ' document.images[eval("\"link" + num + "\"")].src = eval("link" + num + "_on.src");'.$crlf
		. '}'.$crlf
		. $crlf
		. 'function mouseout(num) { '.$crlf
		. ' document.images[eval("\"link" + num + "\"")].src = eval("link" + num + "_off.src");'.$crlf
		. '}'.$crlf
		. ' // --> </script>'.$crlf;
		return $script;
	}

	function getHtmlTableIcons($mod) {
		$crlf = "\n";
		$script = $crlf
			.'<table border=0 cellspacing=10 align='.$this->align.'>'.$crlf;

		$cpt=-1;

		for ($i=0; $i<count($this->links); $i++) {
			$cpt++;
			if ($cpt % $mod == 0) {
				$nrow = '<tr align='.$this->align.' valign=top>'.$crlf;
				$script .= ($i>1) ? "</tr>".$crlf.$nrow : $nrow;
			}
			$script .= "<td>".$crlf
				."<a class=\"header\" target=\"".$this->targets[$i]."\" href='".$this->links[$i]."'".$crlf;

			if (!empty($this->images[$i]))
			$script .= "onMouseOver='mousein(".$i.")'".$crlf
				."onMouseOut='mouseout(".$i.")'";

			$script .=">".$crlf
				.$this->titles[$i]."<br>".$crlf;

			if (!empty($this->images[$i]))
			$script	.="<img border=0 name='link".$i."' src='"
				.$this->imagepath.$this->images[$i].$this->offimg."'></a>".$crlf
				."<br><small>".$this->subtitles[$i]."</small>".$crlf
				."</td>".$crlf;

		}
		$script .= "</tr>".$crlf."</table>".$crlf;
		return $script;
	}

	function Display() {
		echo $this->getScript();
		echo $this->getHtmlTableIcons($this->cols);
	}
	
}

class dropdown {

	var $alignment='rightbottom';
	var $height=80;
	var $width=80;
	var $closeval="x";

	function dropdown($menuname, $id="") {
		$this->menuname=$menuname;
		$this->menunameid=($id) ? $id : md5($menuname);
	}

	function setContent($content){
		$this->html="<a onClick=\"return overlay(this, '".$this->menunameid
				."', '".$this->alignment."')\">"
				.$this->menuname."</a>";
		$this->html.='<div id="'.$this->menunameid.'" '
			.' style="position:absolute; display:none; '
			.'border: 1px solid black;'
			.$this->__dimension()
			.'background-color: white; padding: 4px">'
			.$this->__close()
			.$content
			.'</div>';
	}

	function setClose($val) {
		$this->closeval=$val;
	}

	function display(){
		return $this->html;
	}

	function __dimension() {
		$dim="";
		if ($this->height) {
			$dim.="height:".$this->height."px;";
		}
		if ($this->width) {
			$dim.="width:".$this->width."px;";
		}
		return $dim;
	}

	function __close() {
			return '<div align="right" ><a href="#" onClick="overlayclose(\''.$this->menunameid.'\'); return false">'
			.$this->closeval
			.'</a></div>';
	}
}

function divtitle($title) {
	$htmlstr = '
	<div style="padding: 4px; border-style:solid; border-width:1; border-color:black; background-color:#CCCCFF">
	<b>'.$title.'</b> 
	</div>
	';
	return $htmlstr;
}

function getFileSize($filename, $precision, $unit="") {
	if (!is_file($filename))
		return false;
	
	if (!($bytes=filesize($filename)) || $bytes < 0)
	       return false;

	$units = array (
		0 => 'Bytes',
		1 => 'kB',
		2 => 'MB',
		3 => 'GB',
		4 => 'TB',
		'B' => '0',
		'kB' => '1',
		'MB' => '2',
		'GB' => '3',
		'TB' => '4'
		);

	$setlevel=($unit) ? $units[$unit] : -1;

	$bytes_org = $bytes;
	for ($level = 0; $bytes >= 1024 ; $level++) {
		if ($setlevel==$level)
			break;
		$bytes /= 1024;     
	}
  
  
	if (!$ext=$units[$level]) {
		$bytes=$bytes_org; 
		$ext=$units[0]; 
	}
	return round($bytes, $precision).' '.$ext;
}

function getmicrotime()
{
   list($usec, $sec) = explode(" ", microtime());
   return ((float)$usec + (float)$sec);
}

function matrix($a11, $a12, $a21, $a22) {
	return array(
			'1'=>array('1'=>$a11, '2'=>$a12),
			'2'=>array('1'=>$a21, '2'=>$a22)
		);
}

function matrix_inverse($matrix) {
	$a11 = $matrix[1][1];
	$a12 = $matrix[1][2];
	$a21 = $matrix[2][1];
	$a22 = $matrix[2][2];
	$d = $a11*$a22-$a12*$a21;
	return matrix($a22/$d, -$a12/$d, -$a21/$d, $a11/$d);
	
}

function matrix_multiply($matrix, $vector) {
	$vect=array();
	foreach ($matrix as $i=>$row) {
		$k=0;
		foreach ($row as $v) {
			$vect[$i] += $v * $vector[$k];
			$k++;
		}
	}
	return $vect;
}

function displayMatrix($matrix) {
	$html='
		<table border="0" cellspacing="0" cellpadding="0">
			<tr>
				<td class="bgcolor3" height="1" width="1"></td>
				<td class="bgcolor3" height="1" width="3"></td>
				<td class="bgcolor0" height="1" width="20"></td>
				<td class="bgcolor3" height="1" width="3"></td>
				<td class="bgcolor3" height="1" width="1"></td>
			</tr>
			<tr>
				<td class="bgcolor3" width="1"></td>
				<td colspan=3 class="bgcolor0"  >
				<table cellspacing="5" cellpadding="5">
	';
	if (is_array($matrix))
		foreach ($matrix as $m) {
			$cells = (is_array($m)) ? $m : array($m);
			$html .= '			<tr>'."\n";
			foreach ($cells as $cell) 
				$html .= '				<td>'.$cell.'</td>'."\n";
			$html .= '			</tr>'."\n";
		}
	$html .= '
				</table>
				</td>
				<td class="bgcolor3" width="1">
				</td>
			</tr>
			<tr>
				<td class="bgcolor3" height="1" width="1"></td>
				<td class="bgcolor3" height="1" width="3"></td>
				<td class="bgcolor0" height="1" width="40"></td>
				<td class="bgcolor3" height="1" width="3"></td>
				<td class="bgcolor3" height="1" width="1"></td>
			</tr>
		</table>
	<br>
	';
	return $html;
}

function format_filename_str($filename) {
	$filestr = ereg_replace('[[:alnum:]]+_(.*)', '\1', $filename);
	$filestr = ereg_replace('00', '', $filestr);
	return $filestr;
}

function format_sci_number($data) {

	$decimal = @func_get_arg(1);
	$nohtmlsup = @func_get_arg(2);
	$sup1 = ($nohtmlsup) ? 'E' : 'x10<sup>';
	$sup2 = ($nohtmlsup) ? '' : '</sup>';
	if (!$data) return $data;
	$data_org = $data;
	$neg = ($data<0) ? true : false;
	if ($neg)
		$data *= -1;
	if (!isset($decimal)) { $decimal = 2; }
	if ($data < 1) {
		while ($data < 1) {
			$data *= 10;
			$power++;
		}
		$data = sprintf("%0.".$decimal."f".$sup1."-".$power.$sup2, $data);

	} elseif ($data > 10) {
		while ($data > 10) {
			$data /= 10;
			$power++;
		}
		$data = sprintf("%0.".$decimal."f".$sup1.$power.$sup2, $data);
	}
	if ($power==1)
		$data = sprintf("%0.".$decimal."f", abs($data_org));
	if ($neg)
		$data = "-".$data;
return $data;

}

function format_angle_degree($data) {
	return number_format(($data), 1,'.','').'&deg;';
}

function format_micro_number($data) {
	return number_format(($data/1e-6), 4,'.','').' µm';
}

function format_nano_number($data) {
	return number_format(($data/1e-9), 4,'.','').' nm';
}

function sec2time($second) {
	$h=floor($second/3600);
	$m=floor(($second-$h*3600)/60);
	$s=$second-$h*3600-$m*60;
	$s=str_pad($s, 2, "0", STR_PAD_LEFT);
	$m=str_pad($m, 2, "0", STR_PAD_LEFT);
	$time="$h:$m:$s";
	return $time;
}

function formatHtmlRow($k, $v) {
	if($k) $k .= ":";
	return '<tr><td><span class="datafield0">'
		.$k.'</span></td><td>'
		.$v.'</td></tr>'."\n";
}

function formatArrayHtmlRow($cols) {
	$row = "<tr>";
	$i = 0;
	foreach ($cols as $col) {
		$row .= "<td>".$col."</td>";
	}
	$row .= "</tr>\n";
	return $row;
}

function formatPath($path) {
	$npath = ereg_replace('[\\]','/',$path);
	$npath = ereg("/$", $npath) ? $npath : $npath."/";
	return $npath;
}

function dumpData($data, $keys="") {
	if (!is_array($data))
		return;
	$crlf = "\n";
	$sep = "	";
	$dump = "<pre>";
	$first = current($data);
	$keys = ($keys) ? $keys : (is_array($first) ? array_keys($first) : '0');
	if (is_array($keys))
		$dump .= implode($sep, $keys).$crlf;
	foreach ($data as $d) {
		$f=array();
		if (is_array($keys)) {
		foreach ($keys as $k)
			$f[] = $d[$k];
		} else {
			$f[] = $d;
		}
		$dump .= implode($sep, $f).$crlf;
	}
	$dump .= "</pre>";
	return $dump;
}

function downloadfromfile($tmpfile, $filename="") {
	if (empty($filename))
		$filename = $tmpfile;

	$mime_type = (USR_BROWSER_AGENT == 'MSIE' || USR_BROWSER_AGENT == 'OPERA')
	? 'application/octetstream'
	: 'application/octet-stream';
	$mime_type = "application/force-download";

	$now = gmdate('D, d M Y H:i:s') . ' GMT';

	header('Content-Type: ' . $mime_type);
	header('Expires: ' . $now);
	header("Cache-Control: no-store, no-cache, must-revalidate");
	if (USR_BROWSER_AGENT == 'MSIE') {
		header('Content-Disposition: inline; filename="' . $filename . '"');
		header('Cache-Control: must-revalidate, post-check=0, pre-check=0');
		header('Pragma: public');
	} else {
		header('Content-Disposition: attachment; filename="' . $filename . '"');
		header('Pragma: no-cache');
	}
	readfile($tmpfile);
}

function display_table($title, $content) {
	$html = '
<table border="0" cellpadding="1" cellspacing="1">
		 <tr  class="bgimg1" height="20"> 
			<td>'.$title.'
			</td> 
		</tr>
		 <tr>
		<td>
		<div class="textarea">'.$content.'</div>
		</td>
		 </tr>
		</table> 
	';
	return $html;
}

function getPathFromString($str) {
	//--- return path from a string
	$parts = explode('/',$str);
	if (!is_array($parts))
		return $str;
	array_pop($parts);
	return implode('/',$parts);
}

function ls($dir, $filter="") {
	$files = array();
	if (!$filter)
		$filter=".*";
	if ($dh = opendir($dir)) {
    while (($file = readdir($dh)) !== false) {
     if (ereg($filter,$file)) {
			 $files[]=$file;
     }
		}
		closedir($dh);
	}
	return $files;
}

function array_stats($a) {
	sort($a, SORT_NUMERIC);
	$min = $a[0];
	$len = count($a);
	$max = $a[$len-1];
	if(($len % 2) == 1) { //$len is odd
		$median = $a[$len/2];
	} else { //$len is even
		$median = ($a[intval($len/2.0-0.5)] + $a[intval($len/2.0+0.5)])/2.0;
	}
	$sum = 0.0;
	$sumsq = 0.0;
	$len = count($a);
	if($len > 12) {
		$err = 0.10;
		$bot = $len*$err;
		$top = ($len-1.0)*(1.0 - $err);
	} else {
		$top = $len-1;
		$bot = 0;
	}
	for ($i = intval($bot); $i < intval($top); $i++) {
		//echo $a[$i]."<BR>";
		$sum += $a[$i];
		$sumsq += $a[$i]*$a[$i];
	}
	$mean = $sum/$len;
	$var = ($sumsq - $len*$mean*$mean) / ($len-1);
	$stddev = sqrt($var);
	//echo "med=$median  max=$max  min=$min  sum=$sum  mean=$mean  len=$len std=$stddev<BR>";
	$results['median'] = $median;
	$results['max'] = $max;
	$results['min'] = $min;
	$results['mean'] = $mean;
	$results['stddev'] = $stddev;
	return $results;
}

?>
