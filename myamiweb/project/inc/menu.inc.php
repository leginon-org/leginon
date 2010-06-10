<?php
class menu {

	var $blankimg = 'blank.gif';
	var $selectimg = 'item1.gif';
	var $index = 1;
	var $menudata = array();
	var $submenudata;
	var $image_path = "img/";

	function menu($blankimg='', $selectimg='', $image_path='') {
		if ($blankimg) $this->blankimg=$blankimg;
		if ($selectimg) $this->selectimg=$selectimg;
		if ($image_path) $this->image_path=$image_path;
		echo $this->getStyle();
		echo $this->getJavascript();
	}

	function getStyle() {
		return '
		<style>
			DIV.submenu {
				margin-left:		15pt;
				margin-right:		0pt;
				padding-top:		0pt;
				text-align:		left;
				text-decoration: none;
			}

			A.menu
			{
				font-family: "Arial", "Helvetica", "Sans-Serif";
				font-size: 12px;
				text-decoration: none;
			}
			A.menu
			{
				color: #006699;
			}

			A.menu:active
			{
				color: #cdefef;
			}

			A.menu:visited
			{
				color: #006699;
			}

			A.menu:hover
			{
				color: #cdbaba;
}

				

			DIV.menu {
				font-size: 10pt;
				margin-left:		3pt;
				margin-right:		0pt;
				text-align:		left;
				padding-top:		6pt;
				padding-bottom:		3pt;
			}
		</style>
		';
	}

	function getJavascript() {
		return '
		<script type="text/javascript" >
		<!--
		var path = "'.$this->image_path.'";
		loff = new Image();
		loff.src =  path + "'.$this->blankimg.'";
		lon = new Image();
		lon.src =  path + "'.$this->selectimg.'";

		function lin(num) {
		 if(document.images[eval("\"I" + num + "\"")])
			 document.images[eval("\"I" + num + "\"")].src = eval("lon.src");
		}

		function lout(num) {
		 if(document.images[eval("\"I" + num + "\"")])
			 document.images[eval("\"I" + num + "\"")].src = eval("loff.src");
		}
		//-->
		</script>
		';
	}

	function addMenu($title, $link, $target="") {
		$targetstr = (empty($target)) ? '' : ' target="'.$target.'" ';
		$menuId=md5(uniqid($title));
		$menuImgId = 'I'.$menuId;
		$this->menudata[$menuId]='
		<div class="menu">
		<a href="'.$link.'" class="menu" '.$targetstr.'
		 onMouseOver="lin(\''.$menuId.'\')"
		 onMouseOut="lout(\''.$menuId.'\')">
		 <img alt="'.$title.'" name="'.$menuImgId.'" src="'.$this->image_path.$this->blankimg.'" '.
		' align="left" width="11" height="11" border="0" hspace="4" alt="">'.
		$title.'</a>
		</div>
		';
		return $menuId;
	}

	function addSubMenu($parentId, $title, $link, $target="") {
		$targetstr = (empty($target)) ? '' : ' target="'.$target.'" ';
		$submenuId = md5(uniqid($parentId.$title));
		$submenuImgId = 'I'.$submenuId;
		
		$this->submenudata[$parentId][]='
		<a href="'.$link.'" class="menu" '.$targetstr.'" 
		onMouseOver="lin(\''.$parentId.'\'); lin(\''.$submenuId.'\')"
		onMouseOut ="lout(\''.$parentId.'\'); lout(\''.$submenuId.'\')">
		<img alt="'.$title.'" name="'.$submenuImgId.'" src="'.$this->image_path.$this->blankimg.'" '.
		' align="left" width="7" height="11" border="0" alt="">
		<img alt="square" src="'.$this->image_path.'square.gif" border="0" alt="">'.
		$title.'<br clear="all"></a>
		';
	}

	function display() {
		foreach($this->menudata as $k=>$menu) {
			echo	 $menu;
			if (is_array($this->submenudata[$k])) {
				echo '<div class="submenu">';
				foreach($this->submenudata[$k] as $submenu) 
					echo "$submenu";
				echo '</div>';
			}
		}
	}

}
?>
