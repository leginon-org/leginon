<?php

class FormGeneratorLib
{
	static public function insertHeader( $label )
	{
		$html = "
	    <br />
	    <H4 >$label</H4>
	    <hr />";	

		return $html;
	}
	
	static public function insertTextArea( $name, $label='', $value='', $rows=3, $cols=65, $enable='', $note='' )
	{
		$html .=  docpop( $name, $label )." <br/>\n";
		$html .= "<TEXTAREA NAME='$name' ROWS='$rows' COLS='$cols' $enable >$value</TEXTAREA>\n";
		//$html = "<INPUT TYPE='text' NAME='$name' $enable SIZE='$size' VALUE='$value'>\n";
		
		if (!empty( $note )) {
			$html.= "<font size='-2'>$note</font>\n";
		}
		$html.= "<br/>\n";
				
		return $html;
	}
	
	static public function insertTextField( $name, $label='', $value='', $size=20, $enable='', $note='' )
	{
		$html = "<INPUT TYPE='text' NAME='$name' $enable SIZE='$size' VALUE='$value'>\n";
		$html.=  docpop( $name, $label );
		
		if (!empty( $note )) {
			$html.= "<font size='-2'>$note</font>\n";
		}
		$html.= "<br/>\n";
		
		return $html;
	}
	
	static public function insertStackedTextField( $name, $label='', $value='', $size=20, $enable='', $note='' )
	{
		$html.=  docpop( $name, $label )." <br/>\n";
		$html.= "<INPUT TYPE='text' NAME='$name' $enable SIZE='$size' VALUE='$value'>\n";
		
		if (!empty( $note )) {
			$html.= "<font size='-2'>$note</font>\n";
		}
		$html.= "<br/>\n";
		
		return $html;
	}
	
	static public function insertCheckboxField( $name, $label='', $value='', $enable='', $note='' )
	{
		$html = "<INPUT TYPE='checkbox' NAME='$name' $enable $value >\n";
		$html.=  docpop( $name, $label );
		
		if (!empty( $note )) {
			$html.= "<font size='-2'>$note</font>\n";
		}
		$html.= "<br/>\n";
		
		return $html;
	}

	static public function insertRadioField( $name, $label='', $value='', $checked='', $enable='', $note='' )
	{
		$html = "<INPUT TYPE='radio' NAME='$name' $enable VALUE='$value' $checked >\n";
		$html.=  docpop( $name, $label );
		
		if (!empty( $note )) {
			$html.= "<font size='-2'>$note</font>\n";
		}
		$html.= "<br/>\n";
		
		return $html;
	}
}

?>