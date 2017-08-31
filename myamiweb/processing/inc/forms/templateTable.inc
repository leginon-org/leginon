<?php

/**
 *	The Leginon software is Copyright under 
 *	Apache License, Version 2.0
 *	For terms of the license agreement
 *	see  http://leginon.org
 */

require_once "basicForm.inc";
require_once "inc/particledata.inc";
//require_once "inc/processing.inc";

// Template Table parameters for template correlator picker
class TemplateSelectionTable extends BasicForm
{
	protected $availableTemplate;			// an array of templateinfo availble in the project

	function __construct( $availableTemplates=array(), $angles=true )
	{
		parent::__construct();
		
		// Get the form parameters that have been created by the parent class
		$params = $this->getFormParams();
		
		// The help section corresponds to the array key for these parameters found in help.js for popup help.
		$params->setHelpSection( "appion" );

		$this->particle = new particledata;
		$this->angles = $angles;

		// assign private variable
		$this->availableTemplates = $availableTemplates;

		// add parameters
		$params->addParam( "template_list", $templatelistv, "Template list" );
		if ($this->angles == true) {
			$params->addParam( "range_list", $rangelistv, "Rotation search range for each template" );
		}

		$numtemplates = count($this->availableTemplates);
		for ($i = 1; $i <= $numtemplates; $i++) {
			$this->addSingleTemplateParams($this->availableTemplates[$i-1], $i);
		}

	}
			
	private function addSingleTemplateParams($templateinfo, $i)
	{
		$params = $this->getFormParams();

		if (is_array($templateinfo)) {
			$filename = $templateinfo[path] ."/".$templateinfo[templatename];
			$checkboxname='template'.$i;
			$templaterundata = $this->particle->getRecentTemplateRunFromId($templateinfo[DEF_id]);
			//print_r($templaterundata);
			$startval = (int) $templaterundata[range_start];
			$endval = (int) $templaterundata[range_end];
			$incrval = (int) $templaterundata[range_incr];
			if ($endval==0 || $endval==10) $endval='';
			if ($incrval==0 || $incrval==20) $incrval='';
			if ($startval==0 && $endval=='') $startval='';

			$params->addParam( "templateId".$i, $templateinfo[DEF_id], "template id" );
			$params->addParam( $checkboxname, '', "Use Template ".$i );
			$params->addParam( $checkboxname."strt", $startval, "Starting Angle" );
			$params->addParam( $checkboxname."end", $endval, "Ending Angle" );
			$params->addParam( $checkboxname."incr", $incrval, "Angular Increment" );
		}
		$this->updateFormParams();
	}

	public function generateForm($enable=true)
	{
		$this->updateFormParams();
		$params = $this->getFormParams();
		
		$fieldSize = 20;
		
		$html.=  "<!-- BEGIN Template Table Param -->\n";
		$availableTemplates = $this->availableTemplates;
		if ( !$enable ) {
			// template table params are disabled after selection
			$indices = $this->getUsedTemplateIndices();
			$html.= $this-> generateUsedTemplateForm($indices);
		} else {
			$indices = range(1,count($availableTemplates));
		}
		if ($availableTemplates) {
			if ( $enable ) {
				$html .= "<CENTER>".$params->insertSubmitField( "viewerform", "Use These Templates" )."</CENTER>\n";
				$html.= "<br/>\n";
			}
			$javafunctions="<script type='text/javascript'>\n";
			$templatetable="<table class='tableborder' border='1' cellpadding='5'>\n";
			$numtemplates = count($availableTemplates);
			$i=1;
			foreach($indices as $index) {
				$templateinfo = $availableTemplates[$index-1];
				// arrange templates in 2 columns
				if ($i%2 == 1)
					//first column
					$templatetable.="<tr><td align='left'>\n";
				else
					//second column
					$templatetable.="<td align='left'>\n";
				$htmljava_array = $this->singleTemplate($templateinfo, $index, $enable);
				$templatetable.=$htmljava_array[0];
				$javafunctions.=$htmljava_array[1];
				$i++;
				if ($i%2 == 1)
					$templatetable.="</td></tr>\n";
				else
					$templatetable.="</td>\n";
			}
			$javafunctions.="</SCRIPT>\n";
			$templatetable.="</table>\n";
			if ( $enable )
				// at the end of template table
				$templatetable .= "<CENTER>".$params->insertSubmitField( "viewerform", "Use These Templates" )."</CENTER>\n";
		} else {
			$html .= "<b>Project does not contain any templates.</b>\n";
		}
		$javafunctions.="<script src='../js/viewer.js'></script>\n";
	
		$html .= $templatetable;
		$html .= $javafunctions;
	
		$html.= "<br/>\n";
		$html.=  "<!-- END Template Table Param -->\n";
		return $html;	
	}	

	private function singleTemplate($templateinfo, $i, $enable=true)
	{	// extract template info
		$params = $this->getFormParams();
		$javafunctions="";
		$templatetable="";

		$checkboxname='template'.$i;

		if ( !$enable ) {
		// Does not allow value change. It also has the side effect of not posting the values
			$params->disableParam($checkboxname);
			$params->disableParam($checkboxname.'strt');
			$params->disableParam($checkboxname.'end');
			$params->disableParam($checkboxname.'incr');
			$templatetable.= $params->insertHiddenField( $checkboxname );
			$templatetable.= $params->insertHiddenField( $checkboxname.'strt' );
			$templatetable.= $params->insertHiddenField( $checkboxname.'end' );
			$templatetable.= $params->insertHiddenField( $checkboxname.'incr' );
		}

		if (is_array($templateinfo)) {
			$filename = $templateinfo[path] ."/".$templateinfo[templatename];
			$templaterundata = $this->particle->getRecentTemplateRunFromId($templateinfo[DEF_id]);

			// create the javascript functions to enable/disable the templates
			$javafunctions.="function enable".$checkboxname."() {
				if (document.viewerform.$checkboxname.checked){
					document.viewerform.".$checkboxname."strt.disabled=false;
					document.viewerform.".$checkboxname."end.disabled=false;
					document.viewerform.".$checkboxname."incr.disabled=false;
				}
				else {
					document.viewerform.".$checkboxname."strt.disabled=true;
						document.viewerform.".$checkboxname."end.disabled=true;
						document.viewerform.".$checkboxname."incr.disabled=true;
				}
			}\n";
				// create the image template table
			$templatetable.="<img src='loadimg.php?filename=$filename&w=120' width='120'>\n";
			$templatetable.="<br/>\n";
			$templatetable.="Template ID: <i>&nbsp;$templateinfo[DEF_id]</i><br/>\n";
			$templatetable.="Diameter:    <i>&nbsp;$templateinfo[diam] &Aring;</i><br/>\n";
			$templatetable.="Pixel Size:  <i>&nbsp;$templateinfo[apix] &Aring;</i><br/>\n";


			// Table separator
			$templatetable.="</td><td align='left'>\n";

			// set parameters
			$templatetable.= $params->insertHiddenField( "templateId".$i );	
			$templatetable.= $params->insertCheckboxField( $checkboxname );
			$templatetable.="<br/>\n";
			$templatetable.="<br/>\n";

			if ($this->angles == true) {
				$fieldSize = 3;
				$templatetable.="<b>Rotation values</b><br/>";
				$templatetable.="<i>(leave blank for no rotation)</i>:<br>\n";
				$templatetable.= $params->insertTextField( $checkboxname.'strt', $fieldSize,"" );	
				$templatetable.= $params->insertTextField( $checkboxname.'end', $fieldSize,"" );	
				$templatetable.= $params->insertTextField( $checkboxname.'incr', $fieldSize,"" );	
				$templatetable.="<br/>\n";
			}
			$templatetable.="<table width='200'><tr><td>\n";
			$templatetable.="<b>Description:</b>&nbsp;<font size='-2'>$templateinfo[description]</font>\n";
			$templatetable.="</td></tr></table>\n";
		}
		return array($templatetable,$javascripts);
	}

	// get indices in available templates that are selected for use	
	private function getUsedTemplateIndices() {
		$used_indices = array();
		$this->updateFormParams();
		$params = $this->getFormParams();
		$numtemplates = count($this->availableTemplates);
		if ( $numtemplates > 0 ) {
			for ($i = 1; $i <= $numtemplates; $i++) {
				$checkboxname='template'.$i;
				if ( $params->getParamValue($checkboxname) )
					$used_indices[]=$i;
			}
		}
		return $used_indices;
	}

	// template list and range list html form generation
	private function generateUsedTemplateForm($used_indices) {
		$params = $this->getFormParams();
		$availabletemplates = $this->availableTemplates;
		// get the list of templates
		$templateliststr = "";
		$rangeliststr = "";
		foreach ($used_indices as $num ) {
			$templateid = $params->getParamValue("templateId".$num);
			$templateliststr .= $templateid.",";
			$start = "template".$num."strt";
			$end   = "template".$num."end";
			$incr  = "template".$num."incr";

			$start_value = $params->getParamValue($start);
			$end_value = $params->getParamValue($end);
			$incr_value = $params->getParamValue($incr);
			// check for invalid range
			if ($start_value!='' && $end_value!='0' && $incr_value!='0') {
				// use user supplied values
				$rangestr = $start_value.",".$end_value.",".$incr_value;
			} else {
				// no rotation
				$rangestr = "0,10,20";
			}
			$rangeliststr .= $rangestr."x";
		}
		// remove extra commas and x's
		$templateliststr = substr($templateliststr,0,-1);
		$rangeliststr    = substr($rangeliststr,0,-1);

		//set value and then added as hidden field
		$params->setParamValue("template_list",$templateliststr);
		$html .= $params->insertHiddenField( "template_list" );
		if ($this->angles == true) {
			$params->setParamValue("range_list",$rangeliststr);
			$html .= $params->insertHiddenField( "range_list" );
		}
		return $html;
	}

	// get selected templates
	public function getUsedTemplateIds() {
		$params = $this->getFormParams();
		$templateliststr = $params->getParamValue("template_list");
		return explode(',',$templateliststr);
	}

	// get selected templates
	public function getTemplateDiameter() {
		$indices = $this->getUsedTemplateIndices();
		$max_diam = 0;
		foreach ( $indices as $i ) {
			$diam = $this->availableTemplates[$i-1]['diam'];
			if ( $diam > $max_diam ) $max_diam = $diam;
		}
		return $max_diam;
	}

	public function buildCommand($postArray) {
		$params = $this->getFormParams();
		$command .= parent::buildCommand($postArray);
		
		$numTemplates = count( $this->availableTemplates );
		//remove unwanted commands
		foreach (range(0,$numTemplates-1) as $j ) {
			// remove in reverse order so that 10 comes before 1 Issue #4212
			$i = $numTemplates - $j;
			$command = $this->removeCommandFlag( $command, 'templateId'.$i);
			$command = $this->removeCommandFlag( $command, 'template'.$i.'strt');
			$command = $this->removeCommandFlag( $command, 'template'.$i.'end');
			$command = $this->removeCommandFlag( $command, 'template'.$i.'incr');
			// Do this one last because pattern search would include the above
			$command = $this->removeCommandFlag( $command, 'template'.$i);
		}
		return $command;
	}
		
	// Override the validate function so that we can verify the Template Correlator parameters
	public function validate( $postArray )
	{
		$msg = parent::validate( $postArray );
		$indices = $this->getUsedTemplateIndices();
		if ( count($indices) == 0 )
			$msg .= "Choose a template\n";
		
		return $msg;
	}
	// No need to override the buildCommand
	
	// Non need to override the validate function
	
}

?>
