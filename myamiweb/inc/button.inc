<?php
class button {

	var $crlf="\n";
	var $path='img/';
	var $link=false;

	function button($name,$type) {
		$this->name = $name."_bt";
		$this->type = $type."_bt";
	}

	function getJavascript() {
		$javascript = ''.$this->crlf
		.$this->name.'_off=new Image();'.$this->crlf
		.$this->name.'_off.src=path+"'.$this->type.'_off.gif";'.$this->crlf
		.$this->name.'_over_off=new Image();'.$this->crlf
		.$this->name.'_over_off.src=path+"'.$this->type.'_over_off.gif";'.$this->crlf
		.$this->name.'_on=new Image();'.$this->crlf
		.$this->name.'_on.src=path+"'.$this->type.'_on.gif";'.$this->crlf
		.$this->name.'_over_on=new Image();'.$this->crlf
		.$this->name.'_over_on.src=path+"'.$this->type.'_over_on.gif";'.$this->crlf
		.''.$this->crlf;
		return $javascript;
	}

	function setLink($link, $target="") {
		$this->link=$link;
		$this->target = ($target) ? 'target="'.$target.'"' : "";
	}

	function onClick($jsaction) {
		$this->jsaction = 'javascript:'.$jsaction.'()';
	}

	function display() {
		$iconwidth=15;
		$name = $this->name;
		$imgname = $this->name.'img';
		$llink=$this->link;
		$laction=$this->jsaction;
		if (!$llink)
			$llink=$laction;
		else
			$onclick='onClick="'.$laction.'" '.$this->crlf;
		$htmlbutton = '<a id="'.$this->name.'href" '.$this->target.' href="'.$llink.'"'.$this->crlf
				.'onmouseover="imageonfocus(\''.$imgname.'\', \''.$this->name.'\', \'_over\')"'.$this->crlf
				.'onmouseout="imageoff(\''.$imgname.'\', \''.$this->name.'\', \'\')"'.$this->crlf 
				.'onmouseup="imageoff(\''.$imgname.'\', \''.$this->name.'\', \'\')"'.$this->crlf 
				.'onmousedown="imageon(\''.$imgname.'\', \''.$this->name.'\', \'\')"'.$this->crlf 
				.$onclick
				.'><img name="'.$imgname
				.'" src="'.$this->path.$this->type.'_off.gif"'.$this->crlf
				.'alt="'.$this->type.'"'
				.'border="0" height="15" vspace="0"></a>'.$this->crlf;
		return $htmlbutton;
	}
}

class togglebutton {

	var $crlf="\n";
	var $path='img/';
	var $link=false;
	var $defaultstate = 'false';

	function togglebutton($name, $imgoff, $imgon="") {
		$this->name = $name."_bt";
		$this->imgoff = $imgoff."_bt";
		$this->imgon = ($imgon) ? $imgon."_bt" : $this->imgoff;
		$this->toggle = 'javascript:setstate(\''.$this->name.'img\', \''.$this->name.'\');';
	}

	function getJavascript() {
		$bt_imgon = ($this->imgon) ? $this->imgon : $this->imgoff;
		$javascript = ''.$this->crlf
		.'var '.$this->name.'_st='.$this->defaultstate.';'.$this->crlf
		.$this->name.'_off=new Image();'.$this->crlf
		.$this->name.'_off.src=path+"'.$this->imgoff.'_off.gif";'.$this->crlf
		.$this->name.'_over_off=new Image();'.$this->crlf
		.$this->name.'_over_off.src=path+"'.$this->imgoff.'_over_off.gif";'.$this->crlf
		.$this->name.'_on=new Image();'.$this->crlf
		.$this->name.'_on.src=path+"'.$bt_imgon.'_on.gif";'.$this->crlf
		.$this->name.'_over_on=new Image();'.$this->crlf
		.$this->name.'_over_on.src=path+"'.$bt_imgon.'_over_on.gif";'.$this->crlf
		.''.$this->crlf;
		return $javascript;
	}

	function onToggle($jsaction) {
		$this->jsaction = $jsaction.'('.$this->name.'_st'.')';
	}

	function getjsAction() {
		return $this->jsaction;
	}

	function getjsToggle() {
		return $this->toggle;
	}

	function setLink($link, $target="") {
		$this->link=$link;
		$this->target = ($target) ? 'target="'.$target.'"' : "";
	}

	function display() {

		$imgdefault = $this->imgoff.'_off.gif';
		$iconwidth=15;
		$name = $this->name;
		$imgname = $this->name.'img';
		$llink=$this->link;
		$laction=$this->jsaction;
		if(!$llink) {
			$llink="javascript:".$laction;
			$laction="";
		}
		$htmlbutton = '<a id="'.$this->name.'href" '.$this->target.' href="'.$llink.'"'.$this->crlf
				.'onmouseover="imageonfocus(\''.$imgname.'\', \''.$this->name.'\', \'_over\')"'.$this->crlf
				.'onmouseout="imageonfocus(\''.$imgname.'\', \''.$this->name.'\', \'\')"'.$this->crlf
				.'onclick="'
				.$this->toggle.' '.$laction.'"'.$this->crlf 
				.'><img name="'.$imgname
				.'" src="'.$this->path.$imgdefault.'"'.$this->crlf
				.'alt="'.$this->imgoff.'"'
				.'border="0" height="15" vspace="0"></a>'.$this->crlf;
		return $htmlbutton;
	}
}
?>
