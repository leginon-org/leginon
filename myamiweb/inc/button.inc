<?
class button {

	var $crlf="\n";
	var $path='img/';
	var $link='javascript:void(0)';

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
		.'var '.$this->name.'_bt_st=false;'.$this->crlf
		.''.$this->crlf;
		return $javascript;
	}

	function setLink($link) {
		$this->link=$link;
	}

	function display() {
		$iconwidth=15;
		$name = $this->name;
		$imgname = $this->name.'img';
		$htmlbutton = '<a href="'.$this->link.'"'.$this->crlf
				.'onmouseover="imageonfocus(\''.$imgname.'\', \''.$this->name.'\', \'_over\')"'.$this->crlf
				.'onmouseout="imageoff(\''.$imgname.'\', \''.$this->name.'\', \'\')"'.$this->crlf 
				.'onclick="imageon(\''.$imgname.'\', \''.$this->name.'\', \'\')"'.$this->crlf 
				.'><img name="'.$imgname
				.'" src="'.$this->path.$this->type.'_off.gif"'.$this->crlf
				.'" alt="'.$this->type.'"'
				.'border="0" height="15" vspace="0"></a>'.$this->crlf
				.'';	
		return $htmlbutton;
	}
}
?>

