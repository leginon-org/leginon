<?

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once("config.php");
require_once("inc/util.inc");
require_once('inc/mysql.inc');

$VIEWNB=0;

class viewer {

	var $crlf="\n";
	var $nbview=0;

	function viewer() {
	}

	function setSessionId($sessionId) {
		$this->sessionId=$sessionId;
	}

	function setImageId($imageId) {
		$this->imageId=$imageId;
	}

	function addSessionSelector($sessions=array()) {
		$selector = '<select name="sessionId" onchange="newexp()">'.$this->crlf;
		foreach ($sessions as $session) {
			if ($session[id]==$this->sessionId) $s='selected'; else $s='';
			$selector .= '<option value='.$session[id].' '.$s.' >'.$session[name].$this->crlf; 
		}
		$selector .= '</select>';
		$this->addsessionsel = $selector;
	}

	function addFileSelector($filenames=array(), $size=40) {
		if ($size) $htmlsize = "size=$size";
		$selector = '<select name="imageId" '.$htmlsize
				.' onchange="setimgId();updateviews()">'.$this->crlf;
		$default = ($this->imageId) ? $this->imageId : $filenames[0][id];
		foreach ($filenames as $filename) {
			$filestr = ereg_replace('[[:alnum:]]+_(.*)', '\1', $filename[name]);
			$filestr = ereg_replace('00', '', $filestr);
			if ($filename[id]==$default) $s='selected'; else $s='';
         		$selector .= '<option value='.$filename[id].' '.$s.' >'.$filestr.$this->crlf; 
		}
		$selector .= '</select>';
		$this->addfilesel = $selector;
	}

	function getJavascript() {
		$str = '<script src="js/viewer.js"></script>'.$this->crlf;
		$str .= '<script>'.$this->crlf;
		if ($this->sessionId)
			$str .= 'var jsSessionId = '.$this->sessionId.";".$this->crlf;
		$str .= 'var jsimgId;'.$this->crlf;
		$str .= ''.$this->crlf
		.'</script>'.$this->crlf;
		return $str;
	}

	function getJavascriptInit() {
		$init = '<script>'.$this->crlf;
		$initbuttons="";
		foreach ($this->views as $v) 
			$init .= $v->getJavaScript().$this->crlf;
			$init .= 'function updateviews() { '.$this->crlf;
			$init .= ''.$this->crlf;
		foreach ($this->views as $v) {
			$name = $v->getName();
			$init .= '	newfile("'.$name.'");'.$this->crlf;
			$initbuttons .= $v->getJavaScriptInit().$this->crlf;
		}
		$init .= '}'.$this->crlf;
		$init .= ''.$this->crlf;
		$init .= 'function init() { '.$this->crlf;
		$init .= $initbuttons.$this->crlf;
		$init .= '	setimgId();'.$this->crlf;
		$init .= '	updateviews();'.$this->crlf;
		$init .= '}'.$this->crlf;
		$init .= ''.$this->crlf;
		$init .= '</script>'.$this->crlf;
		return $init;
	}

	function add($view) {
		$this->views[] = $view;
		$this->nbview++;
	}

	function display() {
		$nbviewperrow = ($this->nbviewperrow) ? $this->nbviewperrow : '3';
		$n=1;
		$display = '<form method="post" name="viewerform"  '.
				'action="'.$PHP_SELF.'">'.$this->crlf;
		$display .= '<table border="0">';
		if ($this->addsessionsel) {
			$display .= '<tr>';
			$display .= '<td colspan=2>';
			$display .= $this->addsessionsel;
			$display .= '</td>';
			$display .= '</tr>';
		}
		$display .= '<tr>';
		if ($this->addfilesel) {
			$display .= '<td valign="top">';
			$display .= $this->addfilesel;
			$display .= '</td>';
		}
		$display .= '<td>';
		$display .= '<table border="0"><tr>';
		$viewoff = array();
		foreach ($this->views as $v) {
			if ($v->getViewState()== "on" ) {	
				$display .= '<td '.$v->getSpan().' valign="top">'.$v->display().'</td>';
			} else {
				$display .= '<td>&nbsp;<td>';
				$viewoff[]=$v;
			}
					if ($n % $nbviewperrow == 0) {
						$display .= '</tr><tr>';
					}
			$n++;
		}
		$display .= '</tr></table>';
		$display .= '</td>';
		$display .= '</tr></table>';
		$nbv=1;
		$display .= '<table border="0"><tr>';
		foreach($viewoff as $voff) {
			$voff->setSize(150);
			$display .= '<td>'.$voff->display().'</td>';
			if ($nbv % 3 == 0)
				$display .= "</tr><tr>";
			$nbv++;
		}
		$display .= '</tr></table>';
		$display .= '</form>';
		echo $display;
	}

	function setNbViewPerRow($n) {
		$this->nbviewperrow=$n;
	}

}

class view {

	var $crlf="\n";
	var $size=256;
	var $displayview='on';

	function view($title, $name) {
		global $VIEWNB;
		$this->viewnb = $VIEWNB++;
		$this->title = $title;
		$this->name = $name;
		$this->displayname = $this->name.'view';
		$this->displayPresets(true);
	}

	function setSize($size) {
		$this->size = $size;
	}

	function getSize() {
		return $this->size;
	}

	function setSpan($r='', $c='') {
		$span  = ($r) ? "rowspan=$r" : "";
		$span  .= ($c) ? " colspan=$c" : "";
		$this->span = $span;
	}

	function getSpan() {
		return $this->span;
	}


	function setControl() {
		$this->ismaster = true;
	}

	function getName() {
		return $this->name;
	}

	function setDataTypes($datatypes) {
		$this->datatypes = $datatypes;
	}

	function setImageId($imgId) {
		$this->imageId=$imageId;
	}

	function displayPresets($state) {
		$this->displaypreset= $state;
	}

	function getJavascript() {
		$javascript = ''.$this->crlf
			.'var '.$this->name.'target_bt_st=false;'.$this->crlf
			.'var '.$this->name.'scale_bt_st=false;'.$this->crlf
			.'var '.$this->name.'fft_bt_st=false;'.$this->crlf
			.'var '.$this->name.'close_bt_st=false;'.$this->crlf
			.'var '.$this->name.'size='.$this->size.';'.$this->crlf
			.'var jsvfile'.$this->name.'=1;'.$this->crlf
			.'var jsmin'.$this->name.';'.$this->crlf
			.'var jsmax'.$this->name.';'.$this->crlf
			.''.$this->crlf;
		return $javascript;
	}

	function getJavascriptInit() {
		$javascript = ''.$this->crlf;
		if ($_POST[$this->displayname]=='off')
			$javascript .= 'toggleimage(\''.$this->name.'close_bt\', \'close_bt\');'.$this->crlf;
		// --- set Scale, targets buttons on 
		$javascript .= 'toggleimage(\''.$this->name.'target_bt\', \'target_bt\');'.$this->crlf;
		$javascript .= 'toggleimage(\''.$this->name.'scale_bt\', \'scale_bt\');'.$this->crlf;
		return $javascript;
	}

	function getViewState() {
		$this->displayview = ($_POST[$this->displayname]) ? $_POST[$this->displayname] : 'on';
		return $this->displayview;
	}

	function display() {
		$iconwidth=15;
		$datatypes = $this->datatypes;
		$displayname = $this->displayname;
		$name = $this->name;
		$imgname = $this->name.'img';
		$prename = $this->name.'pre';
		$prememo = $this->name.'prem';
		$defaultpre = ($_POST[$prememo]) ? $_POST[$prememo] : $datatypes[0];
		$selpre = ($_POST[$prename]) ? $_POST[$prename] : $defaultpre;
		$displayview = $this->getViewState();
		$htmlframe = '
		<input type="hidden" name="'.$displayname.'" value="'.$displayview.'">
		<input type="hidden" name="'.$prename.'m" value="'.$selpre.'"> ';
		if ($this->ismaster)
			$htmlframe .= '
		<input type="hidden" name="controlpre" value="'.$prename.'"> 
			';
		$htmlframe .= '
		<table class="bgcolor1" border="0" cellspacing="0" cellpadding="1">
		 <tr>
			<td width="15">
			<a href="javascript:t = toggleimage(\''.$this->name.'close_bt\', \'close_bt\');setview(\''.$displayname.'\',t); newexp() "
				onmouseover="imageonfocus(\''.$this->name.'close_bt\', \'close_bt\', \'_over\')" 
				onmouseout="imageonfocus(\''.$this->name.'close_bt\', \'close_bt\', \'\')" 
				>
				<img name="'.$this->name.'close_bt" src="img/close_bt_off.gif"
				border="0" height="15" vspace="0"></a>
			</td>
			<td nowrap="nowrap" >'.$this->title.'</td>
			<td align="right">
			<table class="bgcolor1" border="0" cellspacing="1" cellpadding="0">
			<tr>
			<td width="15">
			<a href="javascript:toggleimage(\''.$this->name.'fft_bt\', \'fft_bt\');newfile(\''.$name.'\'); "
				onmouseover="imageonfocus(\''.$this->name.'fft_bt\', \'fft_bt\', \'_over\')" 
				onmouseout="imageonfocus(\''.$this->name.'fft_bt\', \'fft_bt\', \'\')" 
				>
				<img name="'.$this->name.'fft_bt" src="img/fft_bt_off.gif"
				border="0" height="15" vspace="0"></a>
			</td>
			<td width="15">
			<a href="javascript:toggleimage(\''.$this->name.'target_bt\', \'target_bt\');newfile(\''.$name.'\'); "
				onmouseover="imageonfocus(\''.$this->name.'target_bt\', \'target_bt\', \'_over\')" 
				onmouseout="imageonfocus(\''.$this->name.'target_bt\', \'target_bt\', \'\')" 
				>
				<img name="'.$this->name.'target_bt" src="img/target_bt_off.gif"
				border="0" height="15" vspace="0"></a>
			</td>
			<td width="15">
			<a href="javascript:toggleimage(\''.$this->name.'scale_bt\', \'scale_bt\');newfile(\''.$name.'\'); "
				onmouseover="imageonfocus(\''.$this->name.'scale_bt\', \'scale_bt\', \'_over\')" 
				onmouseout="imageonfocus(\''.$this->name.'scale_bt\', \'scale_bt\', \'\')" 
				>
				<img name="'.$this->name.'scale_bt" src="img/scale_bt_off.gif"
				border="0" height="15" vspace="0"></a>
			</td>
			</tr>
			</table>
		 </tr>
		 <tr>
			<td colspan="5">	';
		if ($displayview=="on") {
		$htmlframe .='
			<table class="bgcolor0" border="0" cellspacing="0" cellpadding="0">
			 <tr>
				<td height="1" width="'.$this->size.'">
					<select name="'.$prename.'" onchange="newexp()" > 
		';
		if (is_array($datatypes))
		foreach ($datatypes as $k=>$v) {
			if ($k==$selpre) $s='selected'; else $s=''; 	
			$htmlframe .= "<option value=\"$v\" $s>$k \n"; 
		}
		$param = "left=0,top=".($this->viewnb*100).",height=35,width=370";
		$url = "adjust.php?name=$name&displayname=$this->title";
		$htmlframe .='
					</select>
			<a href="javascript:popUpAdjust(\''.$url.'\',\''.$name.'\',\''.$param.'\');">adjust&raquo;</a>
				</td>
			 </tr>
			 <tr>
				<td>
		';
		if ($this->displaypreset) {
		$htmlframe .= '
		<iframe name="'.$this->name.'if" 
                        src="getpreset.php"
			frameborder="0" width="100%" height="50"
			marginheight="1" marginwidth="5"
			scrolling="no" ></iframe>
		';
		$htmlframe .= '
				</td>
			 </tr>
			 <tr>
				<td>
		';
		} else $htmlframe .="&nbsp;";

		$htmlframe .= '
			<a href="javascript:void(0)" id="'.$this->name.'href">
			<img name="'.$this->name.'img" src="img/empty.gif" border="0" hspace="0" vspace="0" width="'.$this->size.'" height="'.$this->size.'"></a>';

		$htmlframe .= '
				</td>
			 </tr>
			</table>';
		}
		$htmlframe .= '
			</td>
		 </tr>
		</table> 
		';	
		return $htmlframe;
	}
}

?>
