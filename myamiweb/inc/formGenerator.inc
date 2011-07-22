<?php

class FormGeneratorLib
{
	public function insertLabel( $name, $label='', $helpkey='' )
	{
		if (!empty( $label )) {
			// If a help key is provided, use it, other wise use the parameter name
			$helpkey = ( $helpkey === '') ? $name : $helpkey;
			return docpop( $helpkey, $label );
		}
	}
	
	public function insertNote( $note='' )
	{
		if (!empty( $note )) {
			return "<font size='-2'>$note</font>\n";
		}
	}
	
	public function insertHeader( $label )
	{
		$html = "
	    <br />
	    <H4 >$label</H4>
	    <hr />";	

		return $html;
	}
	
	public function insertTextArea( $name, $label='', $value='', $rows=3, $cols=65, $enable='', $note='', $helpkey='' )
	{
		$html.= $this->insertLabel( $name, $label, $helpkey );		
		$html.= "<br/>\n";
		$html.= "<TEXTAREA NAME='$name' ROWS='$rows' COLS='$cols' $enable >$value</TEXTAREA>\n";		
		$html.= $this->insertNote( $note );
		$html.= "<br/>\n";
				
		return $html;
	}
	
	public function insertTextField( $name, $label='', $value='', $size=20, $enable='', $note='', $helpkey='' )
	{
		$html.= $this->insertTextFieldInRow( $name, $label, $value, $size, $enable, $note, $helpkey );
		$html.= "<br/>\n";
		
		return $html;
	}
	
	public function insertTextFieldInRow( $name, $label='', $value='', $size=20, $enable='', $note='', $helpkey='' )
	{
		$html.= "<INPUT TYPE='text' NAME='$name' $enable SIZE='$size' VALUE='$value'>\n";
		$html.= $this->insertLabel( $name, $label, $helpkey );				
		$html.= $this->insertNote( $note );
				
		return $html;
	}
	
	public function insertStackedTextField( $name, $label='', $value='', $size=20, $enable='', $note='', $helpkey='' )
	{
		$html.= $this->insertLabel( $name, $label, $helpkey );		
		$html.= "<br/>\n";
		$html.= "<INPUT TYPE='text' NAME='$name' $enable SIZE='$size' VALUE='$value'>\n";
		$html.= $this->insertNote( $note );
		$html.= "<br/>\n";
		
		return $html;
	}
	
	public function insertCheckboxField( $name, $label='', $value='', $enable='', $note='', $helpkey='' )
	{
		$html.= "<INPUT TYPE='checkbox' NAME='$name' $enable $value >\n";
		$html.= $this->insertLabel( $name, $label, $helpkey );				
		$html.= $this->insertNote( $note );
		$html.= "<br/>\n";
		
		return $html;
	}

	public function insertRadioField( $name, $label='', $value='', $checked='', $enable='', $note='', $helpkey='' )
	{
		$html.= "<INPUT TYPE='radio' NAME='$name' $enable VALUE='$value' $checked >\n";
		$html.= $this->insertLabel( $name, $label, $helpkey );				
		$html.= $this->insertNote( $note );
		$html.= "<br/>\n";
		
		return $html;
	}
}

?>