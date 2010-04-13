<?php
class template{
	
	function wizardHeader($title, $cssfile){

		$html = "<html><head>\n";
		$html .= "<title>$title</title>\n";
		$html .= "<meta http-equiv='Content-Type' content='text/html; charset=UTF-8' />\n";
		$html .= "<link href='$cssfile' media='all' rel='stylesheet' type='text/css' />\n";
		$html .= "</head><body>\n";
		$html .= "<div id='pageWrapper'>\n";
		$html .= "<div id='header'>\n";
		$html .= "<p>Web Tools Setup and Installation Wizard</p>\n";
		$html .= "</div>\n";
		$html .= "<div id='nav'><h3>". $title . "</h3></div>\n";
		$html .= "<div id='main'>\n";
		
		echo $html;
	}
	
	function wizardFooter(){
		$html .= "</div>\n";
		$html .= "<div id='footer'>\n";
		$html .= "<p>The Scripps Research Institute. National Resource for "; 
		$html .= "Automated Molecular Microscopy (<a href='http://nramm.scripps.edu'>NRAMM</a>)</p>\n";
		$html .= "</div></div></body></html>\n";
		
		echo $html;
	}

	function textEntry($title, $fieldname, $example='', $size=50){
		$value = $_POST[$fieldname] ? $_POST[$fieldname] : '';
		$html .= "<h3>$title:</h3>\n";
		if ($example)
			$html .= "<p>example: <i>$example</i></p>\n";
		$html .= "<input type='text' size='$size' name='$fieldname' value='$value'/>\n";
		$html .= "<br/><br/>\n";
		echo $html;
	}

}

?>
