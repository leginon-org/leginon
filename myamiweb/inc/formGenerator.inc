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
	
	public function insertCheckboxField( $name, $label='', $value='', $checked='', $enable='', $note='', $helpkey='' )
	{
		$html.= "<INPUT TYPE='checkbox' NAME='$name' $enable VALUE='$value' $checked >\n";
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

	//Options may be a dictionary, to allow a more descriptive string to be shown to the user for each option. 
	public function insertSelectField( $name, $label='', $value='', $options='', $enable='', $note='', $helpkey='' )
	{
		$html.= $this->insertUnlabeledSelectField( $name, $value, $options, $enable );

		$html.= $this->insertLabel( $name, $label, $helpkey );				
		$html.= $this->insertNote( $note );
		$html.= "<br/>\n";
		
		return $html;
	}

	//Options may be a dictionary, to allow a more descriptive string to be shown to the user for each option. 
	public function insertStackedSelectField( $name, $label='', $value='', $options='', $enable='', $note='', $helpkey='' )
	{
		$html.= $this->insertLabel( $name, $label, $helpkey );				
		$html.= $this->insertNote( $note );
		$html.= "<br/>\n";
		$html.= $this->insertUnlabeledSelectField( $name, $value, $options, $enable );

		$html.= "<br/>\n";
		
		return $html;
	}
	
	//Options may be a dictionary, to allow a more descriptive string to be shown to the user for each option. 
	public function insertUnlabeledSelectField( $name, $value='', $options='', $enable='' )
	{
		$html .=  "<SELECT NAME='$name' $enable>\n";
		foreach ($options as $option => $desc) {
			// determine if this entry is currently selected
			$selected = ( $value == $option ) ? " SELECTED" : "";
			
			// add the entry to the option list
			if ( $desc ) {
				$html .=  "<OPTION VALUE='$option' $selected>$desc</OPTION>\n";
			} else {
				$html .=  "<OPTION VALUE='$option' $selected>$option</OPTION>\n";
			}
		}
		$html .=  "</SELECT>\n";		
		
		return $html;
	}
}

?>
