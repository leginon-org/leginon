<?php
class html_elements {
	function justifiedInputTableRow($doc_str,$doc_label,$post_name,$value_name,$size) {
		$text = "<tr><td>\n";
		$text .= docpop($doc_str, $doc_label);
		$text .= "</td><td align='right'>\n";
		$text .= "<input type='text' name='".$post_name."' value='".$tiltlist."' size='".$size."' style='text-align:center'>\n";
		$text .= "</td></tr>\n";
		return $text;
	}
}
?>
