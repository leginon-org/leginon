<?php

/**
 *	The Leginon software is Copyright 2003 
 *	The Scripps Research Institute, La Jolla, CA
 *	For terms of the license agreement
 *	see  http://ami.scripps.edu/software/leginon-license
 */

require_once "basicForm.inc";


class DDStackForm extends BasicForm
{
	function __construct( $ddstackval='',$param_label='',$selection_helpkey='' ) 
	{
		parent::__construct();
		$params = $this->getFormParams();
				
		$this->ddstack = $ddstackval;
		$this->selection_helpkey=$selection_helpkey;
		$params->addParam( "ddstack", '',$param_label,true, false );
	}
	
	public function generateForm()
	{
		// if the form is being reloaded, make sure we keep anything the user already set.
		// does not seem to work in this case
		$this->updateFormParams();

		$html =  $this->addDDStackSelector();
		$html.= "<br/>\n";

		return $html;
	}

	// Returns the html to display a stack selector
	// stackInfos input contains ddstack run id and runname.
	function addDDStackSelector() 
	{
		$particle = new particledata();
		$stackInfos = $particle->getDDStackRunIdsAlign($_GET['expId']);
		$stackidval = $this->ddstack;

		/*
		$html = "<SELECT NAME='ddstack'";
		$html .= "onchange='this.form.submit()'";
		$html .= ">\n";
		*/
		// default to not specifying ddstack

		if (empty($stackInfos)) return '';

		array_unshift($stackInfos,array('stackid'=>'','runname'=>'no-ddstack-specified'));
		
		$ddselect_options = array();
		foreach ( $stackInfos as $stackinfo ) {
			$option = $stackinfo['stackid'];
			$idtext =  ($stackinfo['stackid'] === '') ? '':'ID: '.$stackinfo[stackid];
			$desc = $stackinfo['runname'].' '.$idtext;
			$ddselect_options[$option] = $desc;
		}
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$html = $this->formParams->insertSelectField( 'ddstack', $options=$ddselect_options, $note='', $this->selection_helpkey );
		return $html;
	}

}
?>
