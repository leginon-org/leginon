<?

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
			array($a11, $a12),
			array($a21, $a22)
		);
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

function format_sci_number($data) {

	$decimal = @func_get_arg(1);
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
		$data = sprintf("%0.".$decimal."fx10<sup>-".$power."</sup>", $data);

	} elseif ($data > 10) {
		while ($data > 10) {
			$data /= 10;
			$power++;
		}
		$data = sprintf("%0.".$decimal."fx10<sup>".$power."</sup>", $data);
	}
	if ($power==1)
		$data = sprintf("%0.".$decimal."f", abs($data_org));
	if ($neg)
		$data = "-".$data;
return $data;

}

function format_micro_number($data) {
	return number_format(($data/1e-6), 4,'.','').' µm';
}

function format_nano_number($data) {
	return number_format(($data/1e-9), 4,'.','').' nm';
}

function formatHtmlRow($k, $v) {
	if($k) $k .= ":";
	return '<tr><td><span class="datafield0">'
		.$k.'</span></td><td>'
		.$v.'</td></tr>'."\n";
}

?>
