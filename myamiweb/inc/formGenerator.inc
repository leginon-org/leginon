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
	
	// Generates <input type='HIDDEN' NAME='$name' value='$value'>\n";
	public function insertHiddenField( $name, $value='' )
	{
		$html.= "<input type='HIDDEN' NAME='$name' value='$value'>\n";		
		
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
	
	public function insertSubmitField( $name, $label='', $value='', $helpkey='' )
	{
		$html.= $this->insertLabel( $name, $label, $helpkey );		
		$html.= "<br/>\n";
		$html.= "<input type='submit' name='$name' value='$value'>\n";
		$html.= "<br/>\n";
		
		return $html;
	}
	
	public function insertCheckboxField( $name, $label='', $value='', $checked='', $enable='', $note='', $helpkey='', $onchange='' )
	{
		$changeString = '';
		if ( $onchange ) $changeString = " onchange='".$onchange."'";  
		
		$html.= "<INPUT TYPE='checkbox' NAME='$name' $enable $changeString VALUE='$value' $checked >\n";
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
	public function insertSelectField( $name, $label='', $value='', $options='', $enable='', $note='', $helpkey='', $onchange='' )
	{
		$html.= $this->insertUnlabeledSelectField( $name, $value, $options, $enable, $onchange );

		$html.= $this->insertLabel( $name, $label, $helpkey );				
		$html.= $this->insertNote( $note );
		$html.= "<br/>\n";
		
		return $html;
	}

	//Options may be a dictionary, to allow a more descriptive string to be shown to the user for each option. 
	public function insertStackedSelectField( $name, $label='', $value='', $options='', $enable='', $note='', $helpkey='', $onchange='' )
	{
		$html.= $this->insertLabel( $name, $label, $helpkey );				
		$html.= $this->insertNote( $note );
		$html.= "<br/>\n";
		$html.= $this->insertUnlabeledSelectField( $name, $value, $options, $enable, $onchange );

		$html.= "<br/>\n";
		
		return $html;
	}
	
	// Options MUST be a dictionary, to allow a more descriptive string to be shown to the user for each option, if desired.
	// If the option value and description should be the same, then that value should be both the key and the value.
	// $options = array( "first" => "first", "second" => "second description"...) The key is what gets kept in the POST array. 
	public function insertUnlabeledSelectField( $name, $value='', $options='', $enable='', $onchange='' )
	{
		$changeString = '';
		if ( $onchange ) $changeString = " onchange='".$onchange."'";  
		
		$html .=  "<SELECT NAME='$name' $enable $changeString>\n";
		
		foreach ($options as $option => $desc) {
			// determine if this entry is currently selected
			$selected = ( $value == $option ) ? " SELECTED" : "";
			
			// add the entry to the option list
			$html .=  "<OPTION VALUE='$option' $selected>$desc</OPTION>\n";
		}
		$html .=  "</SELECT>\n";		
		
		return $html;
	}
}

?>
