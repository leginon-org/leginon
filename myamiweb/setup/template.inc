<?php
class template{
	
	function wizardHeader($title){

		$html = "<html><head>";
		$html .= "<meta http-equiv='Content-Type' content='text/html; charset=UTF-8' />";
		$html .= "<link href='../css/setup.css' media='all' rel='stylesheet' type='text/css' />";
		$html .= "</head><body>";
		$html .= "<div id='pageWrapper'>";
		$html .= "<div id='header'>";
		$html .= "<p>Web Tools Setup and Installation Wizard</p>";
		$html .= "</div>";
		$html .= "<div id='nav'><h3>". $title . "</h3></div>";
		$html .= "<div id='main'>";
		
		echo $html;
	}
	
	function wizardFooter(){
		$html .= "</div>";
		$html .= "<div id='footer'>";
		$html .= "<p>The Scripps Research Institute. National Resource for "; 
		$html .= "Automated Molecular Microscopy (<a href='http://nramm.scripps.edu'>NRAMM</a>)</p>";
		$html .= "</div></div></body></html>";
		
		echo $html;
	}
}

?>