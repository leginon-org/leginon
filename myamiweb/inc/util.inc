<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

define("USR_BROWSER_AGENT", browser('b'));
define("USR_PLATFORM_AGENT", browser('p'));
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
	var $imagepath = "";

	function addlink($link, $title, $subtitle='', $image='') {
		$this->links[] = $link;
		$this->titles[] = $title;
		$this->subtitles[] = $subtitle;
		$this->images[] = $image;
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
			  ."link".$i."_off.src = '".$this->imagepath.$this->images[$i]."_off.gif';".$crlf
			  ."link".$i."_on = new Image();".$crlf
			  ."link".$i."_on.src = '".$this->imagepath.$this->images[$i]."_on.gif';".$crlf;
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
			.'<table border=0 cellspacing=10 align=center>'.$crlf;

		$cpt=-1;

		for ($i=0; $i<count($this->links); $i++) {
			$cpt++;
			if ($cpt % $mod == 0) {
				$nrow = '<tr align=center valign=top>'.$crlf;
				$script .= ($i>1) ? "</tr>".$crlf.$nrow : $nrow;
			}
			$script .= "<td>".$crlf
				."<a class=\"header\" target=\"_blank\" href='".$this->links[$i]."'".$crlf;

			if (!empty($this->images[$i]))
			$script .= "onMouseOver='mousein(".$i.")'".$crlf
				."onMouseOut='mouseout(".$i.")'";

			$script .=">".$crlf
				.$this->titles[$i]."<br>".$crlf;

			if (!empty($this->images[$i]))
			$script	.="<img border=0 name='link".$i."' src='"
				.$this->imagepath.$this->images[$i]."_off.gif'></a>".$crlf
				."<br><small>".$this->subtitles[$i]."</small>".$crlf
				."</td>".$crlf;

		}
		$script .= "</tr>".$crlf."</table>".$crlf;
		return $script;
	}

	function Display() {
		echo $this->getScript();
		echo $this->getHtmlTableIcons(3);
	}
}
?>
