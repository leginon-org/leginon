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
require ('inc/button.inc');

$VIEWNB=0;

class viewer {

	var $crlf="\n";
	var $nbview=0;

	function viewer() {
	}

	function setSessionId($sessionId) {
		$this->sessionId=$sessionId;
	}

	function setProjectId($projectId) {
		$this->projectId=$projectId;
	}

	function setImageId($imageId) {
		$this->imageId=$imageId;
	}

	function addProjectSelector($projects=array()) {
		$projectselector = '<select name="projectId" onchange="newexp()">'.$this->crlf;
		foreach ($projects as $project) {
			if ($project[id]==$this->projectId) $s='selected'; else $s='';
			$projectselector .= '<option value='.$project[id].' '.$s.' >'
						.$project[name].'</option>'.$this->crlf; 
		}
		$projectselector .= '</select>'.$this->crlf;
		$this->addprojectsel = $projectselector;
	}

	function addSessionSelector($sessions=array()) {
		$selector = '<select name="sessionId" onchange="newexp()">'.$this->crlf;
		foreach ($sessions as $session) {
			if ($session[id]==$this->sessionId) $s='selected'; else $s='';
			$selector .= '<option value='.$session[id].' '.$s.' >'
					.$session[name].'</option>'.$this->crlf; 
		}
		$selector .= '</select>';
		$this->addsessionsel = $selector;
	}

	function addLoiControl($refreshtime="") {
		if (empty($refreshtime))
			$refreshtime = 10;
		$btstop = new button('st1', 'stop');
		$btstop->setLink('javascript:stop()');
		$btstart = new button('st2', 'start');
		$btstart->setLink('javascript:start()');
		$loijavascript = ''
		.$btstop->getJavascript().$this->crlf
		.$btstart->getJavascript().$this->crlf
		.'var mintime=1000;'.$this->crlf
		.'var maxtime=60000;'.$this->crlf
		.'var refreshtime=10000;'.$this->crlf
		.'window.name="loi";'.$this->crlf
		.''.$this->crlf
		.'function start(){'.$this->crlf
		.'	if (cif=this.myif) {'.$this->crlf
		.'		formatrefreshtime();'.$this->crlf
		.'		cif.start(refreshtime);'.$this->crlf
		.'	}'.$this->crlf
		.'}'.$this->crlf
		.''.$this->crlf
		.'function formatrefreshtime() {'.$this->crlf
		.'	refreshtime=parseInt(document.viewerform.refreshtime.value)*1000;'.$this->crlf
		.'	if (!refreshtime || refreshtime<mintime)'.$this->crlf
		.'		refreshtime = mintime;'.$this->crlf
		.'	if (refreshtime>maxtime)'.$this->crlf
		.'		refreshtime = maxtime;'.$this->crlf
		.'	document.viewerform.refreshtime.value = refreshtime/1000;'.$this->crlf
		.'}'.$this->crlf
		.''.$this->crlf
		.'function stop() {'.$this->crlf
		.'	if (cif=this.myif) {'.$this->crlf
		.'		cif.stop();'.$this->crlf
		.'	}'.$this->crlf
		.'}'.$this->crlf
		.''.$this->crlf
		.'function reset(id) {'.$this->crlf
		.'	jsimgId=id;'.$this->crlf
		.'	updateviews();'.$this->crlf
		.'}'.$this->crlf
		.''.$this->crlf;

		$loicontrol = ''
		.'<table border=0>'.$this->crlf
		.'<tr>'.$this->crlf
		.'<td>'.$this->crlf
		.'	<label for="refreshtime">Refresh (s):</label>'.$this->crlf
		.'</td>'.$this->crlf
		.'<td>'.$this->crlf
		.'	<input class="field" type="text" name="refreshtime" size="4" value="'.$refreshtime.'">'.$this->crlf
		.'</td>'.$this->crlf
		.'<td>'.$this->crlf
		.'	'.$btstop->display().$this->crlf
		.'</td>'.$this->crlf
		.'<td>'.$this->crlf
		.'	'.$btstart->display().$this->crlf
		.'</td>'.$this->crlf
		.'<td>'.$this->crlf
		.'<iframe name="myif" '.$this->crlf
		.'	src="getlastfileid.php?session='.$this->sessionId.'"'.$this->crlf
		.'	frameborder="0" width="0" height="0"'.$this->crlf
		.'	marginheight="0" marginwidth="0"'.$this->crlf
		.'	scrolling="no" ></iframe>'.$this->crlf
		.'</td>'.$this->crlf
		.'</tr>'.$this->crlf
		.'</table>'.$this->crlf;

		$this->addloicontrol = $loicontrol;
		$this->addloijavascript = $loijavascript;
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
		$str .= '<script src="js/button.js"></script>'.$this->crlf;
		$str .= '<script>'.$this->crlf;
		if ($this->sessionId)
			$str .= 'var jsSessionId = '.$this->sessionId.";".$this->crlf;
		$jsimgId = ($this->imageId) ? ' = '.$this->imageId.';' : ';';
		$str .= 'var jsimgId'.$jsimgId.$this->crlf;
		$str .= ''.$this->crlf;
		if ($this->addloijavascript)
			$str .= $this->addloijavascript;
		$str .= '</script>'.$this->crlf;
		return $str;
	}

	function getJavascriptInit() {
		$initbuttons="";
		$nv=0;
		$init = '<script>'.$this->crlf;
		$init .= 'var jsviews = new Array();'.$this->crlf;
		foreach ($this->views as $v) 
			$init .= $v->getJavascriptvar();

		foreach ($this->views as $v) {
			$init .= $v->getJavascriptButton();
			$init .= 'jsviews['.$nv.']="'.$v->getName().'";'.$this->crlf;
			$nv++;
		}
		$init .= 'function updateviews() { '.$this->crlf;
		$init .= ''.$this->crlf;
		foreach ($this->views as $v) {
			$name = $v->getName();
			$init .= '	newfile("'.$name.'");'.$this->crlf;
			if ($v->getJavaScriptInit())
				$initbuttons .= $v->getJavaScriptInit().$this->crlf;
		}
		$init .= '}'.$this->crlf;
		$init .= ''.$this->crlf;
		$init .= 'function initviewer() { '.$this->crlf;
		if (!empty($initbuttons))
			$init .= $initbuttons.$this->crlf;
		$init .= 'setimgId();'.$this->crlf;
		$init .= 'updateviews();'.$this->crlf;
		if ($this->addloijavascript)
			$init .= '	start();'.$this->crlf;
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
		if ($debug=0) {
		$display .= '<textarea name=debug rows=10 cols=50></textarea>';
		$display .= '<input type=button value="clear" onclick="javascript:document.viewerform.debug.value=\'\'">';
		}
		$display .= '<table border="0">';
		if ($this->addloicontrol) {
			$display .= '<tr>';
			$display .= '<td colspan=2>';
			$display .= $this->addloicontrol;
			$display .= '</td>';
			$display .= '</tr>';
		}
		if ($this->addsessionsel) {
			$display .= '<tr>';
			if ($this->addprojectsel) {
				$display .= '<td>';
				$display .= $this->addprojectsel;
				$display .= '</td>';
			}
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
		$this->btdownload = new button('download'.$this->name, 'dwd');
		$this->btdownload->setLink('download.php','');
		$this->displayscaleicon = true;
		$this->btinfo = new button('info'.$this->name, 'info');
		$this->btinfo->setLink('imgreport.php','');
		$this->displayscaleicon = true;
		$this->displaytargeticon = true;
		$this->displayffticon = true;
		$this->displayfiltericon = true;
		$this->displayinfoicon = true;
		$this->displaydownloadicon = true;
		$this->displaycloseicon = true;
		$this->displayadjustlink = true;
		$this->framecolor = ' class="bgcolor1" ';
		$this->menucolor = ' class="bgcolor1" ';
		$this->presetscript = 'getpreset.php';
		$this->imagescript = 'getparentimgtarget.php';
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

	function setImageId($imageId) {
		$this->imageId=$imageId;
	}

	function displayPresets($state) {
		$this->displaypreset= $state;
	}

	function displayCloseIcon($state) {
		$this->displaycloseicon = $state;
	}

	function displayDownloadIcon($state) {
		$this->displaydownloadicon = $state;
	}

	function displayInfoIcon($state) {
		$this->displayinfoicon = $state;
	}

	function displayFilterIcon($state) {
		$this->displayfiltericon = $state;
	}

	function displayFFTIcon($state) {
		$this->displayffticon = $state;
	}

	function displayTargetIcon($state) {
		$this->displaytargeticon = $state;
	}

	function displayScaleIcon($state) {
		$this->displayscaleicon = $state;
	}

	function displayAdjustLink($state) {
		$this->displayadjustlink= $state;
	}

	function getJavascriptvar() {
		$javascript = ''
			.'var '.$this->name.'target_bt_st=false;'.$this->crlf
			.'var '.$this->name.'scale_bt_st=false;'.$this->crlf
			.'var '.$this->name.'fft_bt_st=false;'.$this->crlf
			.'var '.$this->name.'filter_bt_st=false;'.$this->crlf
			.'var '.$this->name.'close_bt_st=false;'.$this->crlf
			.'var '.$this->name.'size='.$this->size.';'.$this->crlf
			.'var jsimagescript'.$this->name.'="'.$this->imagescript.'";'.$this->crlf
			.'var jspresetscript'.$this->name.'="'.$this->presetscript.'";'.$this->crlf
			.'var jsvfile'.$this->name.'=1;'.$this->crlf
			.'var jsmin'.$this->name.';'.$this->crlf
			.'var jsmax'.$this->name.';'.$this->crlf
			.'var jsfilter'.$this->name.';'
			.'var jsbinning'.$this->name.';'
			.$this->crlf;
		return $javascript;
	}

	function getJavascriptButton() {
		$javascript = ''.$this->crlf
			.$this->btinfo->getJavascript()
			.$this->btdownload->getJavascript()
			.$this->crlf;
		return $javascript;
	}

	function getJavascriptInit() {
		$javascript = '';
		if ($_POST[$this->displayname]=='off')
			$javascript .= 'toggleimage(\''.$this->name.'close_bt\', \'close_bt\');'.$this->crlf;
		// --- set Scale, targets buttons on 
		if ($this->displaytargeticon)
			$javascript .= 'toggleimage(\''.$this->name.'target_bt\', \'target_bt\');'.$this->crlf;
		if ($this->displayscaleicon)
			$javascript .= 'toggleimage(\''.$this->name.'scale_bt\', \'scale_bt\');'.$this->crlf;
		return $javascript;
	}

	function getViewState() {
		$this->displayview = ($_POST[$this->displayname]) ? $_POST[$this->displayname] : 'on';
		return $this->displayview;
	}

	function selectDataType($type) {
		$this->selecteddatatype = $type;
	}

	function setFrameColor($color) {
		$this->framecolor = ' bgcolor="'.$color.'" ';
	}

	function setMenuColor($color) {
		$this->menucolor = ' bgcolor="'.$color.'" ';
	}

	function setPresetScript($scriptname) {
		$this->presetscript = $scriptname;
	}

	function setImageScript($scriptname) {
                $this->imagescript= $scriptname;
	}

	function display() {
		$iconwidth=15;
		$datatypes = $this->datatypes;
		$displayname = $this->displayname;
		$name = $this->name;
		$imgname = $this->name.'img';
		$prename = $this->name.'pre';
		$prememo = $this->name.'prem';
		$defaultdatatype = ($this->selecteddatatype) ? $this->selecteddatatype : $datatypes[0];
		$defaultpre = ($_POST[$prememo]) ? $_POST[$prememo] : $defaultdatatype;
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
		<table '.$this->framecolor.' border="0" cellspacing="0" cellpadding="1">
		 <tr '.$this->menucolor.'>
		';
		if ($this->displaycloseicon)
		$htmlframe .= '
			<td width="15">
			<a href="javascript:t = toggleimage(\''.$this->name.'close_bt\', \'close_bt\');setview(\''.$displayname.'\',t); newexp() "
				onmouseover="imageonfocus(\''.$this->name.'close_bt\', \'close_bt\', \'_over\')" 
				onmouseout="imageonfocus(\''.$this->name.'close_bt\', \'close_bt\', \'\')" 
				>
				<img name="'.$this->name.'close_bt" src="img/close_bt_off.gif"
				border="0" height="15" vspace="0"></a>
			</td>
		';
		$htmlframe .= '
			<td nowrap="nowrap" >'.$this->title.'</td>
			<td align="right">
			<table '.$this->menucolor.' border="0" cellspacing="1" cellpadding="0">
			<tr>
		';
		if ($this->displaydownloadicon)
		$htmlframe .= '
			<td width="15">'
			.$this->btdownload->display().$this->crlf
			.'
			</td>
		';
		if ($this->displayinfoicon)
		$htmlframe .= '
			<td width="15">'
			.$this->btinfo->display().$this->crlf
			.'
			</td>
		';
		if ($this->displayfiltericon)
		$htmlframe .= '
			<td width="15">
			<a href="javascript:'.$this->name.'filter_bt_state=toggleimage(\''.$this->name.'filter_bt\', \'filter_bt\');newfile(\''.$name.'\'); "
				onmouseover="imageonfocus(\''.$this->name.'filter_bt\', \'filter_bt\', \'_over\')" 
				onmouseout="imageonfocus(\''.$this->name.'filter_bt\', \'filter_bt\', \'\')" 
				>
				<img name="'.$this->name.'filter_bt" src="img/filter_bt_off.gif"
				border="0" height="15" vspace="0"></a>
			</td>
		';
		if ($this->displayffticon)
		$htmlframe .= '
			<td width="15">
			<a href="javascript:toggleimage(\''.$this->name.'fft_bt\', \'fft_bt\');newfile(\''.$name.'\'); "
				onmouseover="imageonfocus(\''.$this->name.'fft_bt\', \'fft_bt\', \'_over\')" 
				onmouseout="imageonfocus(\''.$this->name.'fft_bt\', \'fft_bt\', \'\')" 
				>
				<img name="'.$this->name.'fft_bt" src="img/fft_bt_off.gif"
				border="0" height="15" vspace="0"></a>
			</td>
		';
		if ($this->displaytargeticon)
		$htmlframe .= '
			<td width="15">
			<a href="javascript:toggleimage(\''.$this->name.'target_bt\', \'target_bt\');newfile(\''.$name.'\'); "
				onmouseover="imageonfocus(\''.$this->name.'target_bt\', \'target_bt\', \'_over\')" 
				onmouseout="imageonfocus(\''.$this->name.'target_bt\', \'target_bt\', \'\')" 
				>
				<img name="'.$this->name.'target_bt" src="img/target_bt_off.gif"
				border="0" height="15" vspace="0"></a>
			</td>
		';
		if ($this->displayscaleicon)
		$htmlframe .= '
			<td width="15">
			<a href="javascript:toggleimage(\''.$this->name.'scale_bt\', \'scale_bt\');newfile(\''.$name.'\'); "
				onmouseover="imageonfocus(\''.$this->name.'scale_bt\', \'scale_bt\', \'_over\')" 
				onmouseout="imageonfocus(\''.$this->name.'scale_bt\', \'scale_bt\', \'\')" 
				>
				<img name="'.$this->name.'scale_bt" src="img/scale_bt_off.gif"
				border="0" height="15" vspace="0"></a>
			</td>
		';
		$htmlframe .= '
			</tr>
			</table>
		 </tr>
		 <tr valign=bottom>
			<td colspan="5">	';
		if ($displayview=="on") {
		$htmlframe .='
			<table class="bgcolor0" border="0" cellspacing="0" cellpadding="0">
		';
		// --- begin option table
		if (is_array($datatypes) || $this->displayadjustlink || $this->displaypreset ) {
		$htmlframe .='
			 <tr>
				<td width="'.$this->size.'">
		';
		if (is_array($datatypes)) {
		$htmlframe .='
					<select name="'.$prename.'" onchange="newexp()" > 
		';
		foreach ($datatypes as $k=>$v) {
			if ($k==$selpre) $s='selected'; else $s=''; 	
			$htmlframe .= "<option value=\"$v\" $s>$k \n"; 
		}
		$htmlframe .='
					</select>
		';
		}
		$param = "left=0,top=".($this->viewnb*100).",height=35,width=370";
		$url = "adjust.php?name=$name&displayname=$this->title";
		if ($this->displayadjustlink)
		$htmlframe .='
			<a href="javascript:popUpAdjust(\''.$url.'\',\''.$name.'\',\''.$param.'\');">adjust&raquo;</a>
		';
		$htmlframe .= '
				</td>
			 </tr>';
		if ($this->displaypreset) {
		$htmlframe .= '
			 <tr>
				<td>
		<iframe name="'.$this->name.'if" 
                        src="'.$this->presetscript.'"
			frameborder="0" width="'.$this->size.'" height="50"
			marginheight="1" marginwidth="5"
			scrolling="no" ></iframe>
		';
		$htmlframe .= '</td>
			 </tr>
		';
		}
		} // --- end option row

		$htmlframe .= '<tr>
				<td width="'.$this->size.'">
			<a href="javascript:void(0)" id="'.$this->name.'href">'.
			'<img name="'.$this->name.'img" src="img/empty.gif" border="0" hspace="0" vspace="0" width="'.$this->size.'" ></a>'; 

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
