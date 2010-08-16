<?php
/**
 *	This aform class attempts to ease boring forms...
 *
 *	D. Fellmann
 */

class form {

	var $jspath="js/";
	var $str_required='<font color="red">&nbsp;*&nbsp;</font>';
	var $fieldnb=0;
	var $formfields=array();
	var $fieldkeys=array();
	var $defaults=array();
	var $fields=false;
	var $onsubmit=false;
	var $action=false;
	var $fieldprefix="f";
	var $alert=false;

  function form($name="") {
    $this->name=$name;
		$this->formclass="aform";
  }

	function setPrefix($prefix) {
		$this->fieldprefix=$prefix;
	}

	function setDefaults($data) {
		$this->defaults=(array)$data;
	}

	function getFieldKeys() {
		return $this->fieldkeys;
	}

	function add($str) {
		$this->formfields[]=$str;
		return $str;
	}

	function display($keys=array()) {
		$formfields=$this->_get_from_keys($this->formfields, $keys);
		$str='<form method="post" enctype="multipart/form-data" ';
		if ($this->name) {
			$str.='name="'.$this->name;
		}
		if ($this->action) {
			$str.='action="'.$this->action;
		}
		if ($this->onsubmit) {
			$str.='" onSubmit="'.$this->onsubmit;
		}
		$str.='"><ul class="aform" >';
		$str.=implode("\n",$formfields);
		$str.='</form>';
		return $this->_contain($str);
	}

	function _get_from_keys($data, $keys) {
		$ndata=$data;
		if ($keys && is_array($keys)) {
			$ndata=array();
			foreach ($keys as $k) {
				$ndata[]=$data[$k];
			}
		}
		return $ndata;
	}

	function _contain($str) {
		return '<div id="aform">'
					.$str
					.'</div>';
	}

	function _field_key_inc() {
		$fieldnb = ++$this->fieldnb;
		$key=$this->fieldprefix.$fieldnb;
		return $key;
	}

  function addSubmit($name, $value) {
		$field=$this->_field_key_inc();
		$str='<input class="bt1" type="submit" name="'.$name.'" value="'.$value.'" />';
		$this->formfields[$field]=$str;
		$this->fieldkeys[]=$field;
		return $str;
  }

	function addHiddenField($name, $value) {
		$field=$this->_field_key_inc();
		$str='<input type="hidden" name="'.$name.'" value="'.$value.'" />';
		$this->formfields[$field]=$str;
		$this->fieldkeys[]=$field;
		return $str;
	}

	function addLabel($label, $value) {
		$field=$this->_field_key_inc();
		$str='<li class="'.$this->formclass.'" id="'.$fieldsection.'">'
		.'<label class="fieldlabel">'.$label;
		if ($description) {
			$str.='<a class="info" href="#"><img src="img/info.png" border="0">'
			.'<span class="infobox" >'.$description
			.'</span></a>';
		}
		$str.='</label>'
			.$value
			.'</li>';
		$this->formfields[$field]=$str;
		$this->fieldkeys[]=$field;
		return $str;
	}

	function addDate($label, $size, $required=false, $description=false) {
		$field=$this->_field_key_inc();
		$fieldsection="s_".$field;
		$value=$this->defaults[$field];
		if (!$value)
			$value="mm/dd/yy";

		if ($required) {
			$label.=$this->str_required;
		}
		$required=($required)? "1" : "0";

		$str='<li class="'.$this->formclass.'" id="'.$fieldsection.'">'
		.'<label class="fieldlabel">'.$label;
		if ($description) {
			$str.='<a class="info" href="#"><img src="img/info.png" border="0">'
			.'<span class="infobox" >'.$description
			.'</span></a>';
		}
		$str.='</label>';
		$str.='<input class="'.$this->formclass.'" '
		.'type="text" '
		.'name="'.$field.'" id="'.$field.'" '
		.'size="'.$size.'" value="'.$value.'" maxlength="12" '
		.'onclick="event.cancelBubble=true;sc(this);" onfocus="sc(this);" '
		.'>';
		$str.='<iframe src="'.$this->jspath.'jscal/calx.php" style="visibility: hidden; position: absolute; width: 299px; height: 186px; z-index: 100; display: block; " id="CalFrame" name="CalFrame" marginheight="0" marginwidth="0" noresize="" frameborder="0" scrolling="no"></iframe>';
		$str.='</li>';

		$strjs=$this->validatejsField($field, $fieldsection, 'date', $required);

		$this->formfields[$field]=$str;
		$this->fieldkeys[]=$field;
		$this->jsformfields[$field]=$strjs;
		return $field;
	}

	function addTime($label, $size, $required=false, $description=false) {
		$field=$this->_field_key_inc();
		$fieldsection="s_".$field;
		$value=$this->defaults[$field];
		if (!$value)
			$value="hh:mm";

		if ($required) {
			$label.=$this->str_required;
		}
		$required=($required)? "1" : "0";

		$str='<li class="'.$this->formclass.'" id="'.$fieldsection.'">'
		.'<label class="fieldlabel">'.$label;
		if ($description) {
			$str.='<a class="info" href="#"><img src="img/info.png" border="0">'
			.'<span class="infobox" >'.$description
			.'</span></a>';
		}
		$str.='</label>';
		$str.='<input class="'.$this->formclass.'" '
		.'type="text" '
		.'name="'.$field.'" id="'.$field.'" '
		.'size="'.$size.'" value="'.$value.'" maxlength="5" '
		.'>';
		$str.='</li>';

		$strjs=$this->validatejsField($field, $fieldsection, 'time', $required);

		$this->formfields[$field]=$str;
		$this->fieldkeys[]=$field;
		$this->jsformfields[$field]=$strjs;
		return $field;
	}

	function addList($label, $data, $size=1, $required=false, $description=false, $action=false) {
		$field=$this->_field_key_inc();
		$fieldsection="s_".$field;
		$value=$this->defaults[$field];
		$js=($action) ? "onChange='this.form.submit()'" : "";

		$label.= ($required) ? $this->str_required : "&nbsp;&nbsp;";
		$required=($required)? "1" : "0";

		$str='<li class="'.$this->formclass.'" id="'.$fieldsection.'">'
		.'<label class="fieldlabel">'.$label;
		if ($description) {
			$str.='<a class="info" href="#"><img src="img/info.png" border="0">'
			.'<span class="infobox" >'.$description
			.'</span></a>';
		}
		$str.='</label><select class="'.$this->formclass.'" '
		.'name="'.$field.'" id="'.$field.'" '
		.'size="'.$size.'" '.$js.' >';
		foreach ((array)$data as $k=>$v) {
			$s=($k==$value) ? "selected" : "";
			$str.='<option value="'.$k.'" '.$s.' >'.$v.'</option>'."\n";
		}
		$str.='</select>'
		.'</li>';

		$this->formfields[$field]=$str;
		$this->fieldkeys[]=$field;
		$this->jsformfields[$field]=$strjs;
		return $field;
	}
	
	function addField($label, $size, $required=false, $description=false) {
		$field=$this->_field_key_inc();
		$fieldsection="s_".$field;
		$value=$this->defaults[$field];

		if ($required) {
			$label.=$this->str_required;
		}
		$required=($required)? "1" : "0";

		$str='<li class="'.$this->formclass.'" id="'.$fieldsection.'">'
		.'<label class="fieldlabel">'.$label;
		if ($description) {
			$str.='<a class="info" href="#"><img src="img/info.png" border="0">'
			.'<span class="infobox" >'.$description
			.'</span></a>';
		}
		$str.='</label><input class="'.$this->formclass.'" '
		.'type="text" '
		.'name="'.$field.'" id="'.$field.'" '
		.'size="'.$size.'" value="'.$value.'"></li>';

		$strjs=$this->validatejsField($field, $fieldsection, 'text', $required);

		$this->formfields[$field]=$str;
		$this->fieldkeys[]=$field;
		$this->jsformfields[$field]=$strjs;
		return $field;
	}

  function addTextarea($label, $rows, $cols, $required=false, $description=false) {
		$field=$this->_field_key_inc();
		$fieldsection="s_".$field;
		$value=$this->defaults[$field];

		if ($required) {
			$label.=$this->str_required;
			$required="1";
		} else {
			$required="0";
		}

		$str='<li class="'.$this->formclass.'" id="'.$fieldsection.'">'
		.'<label class="fieldlabel">'.$label;
		if ($description) {
			$str.='<a class="info" href="#"><img src="img/info.png" border="0">'
			.'<span class="infobox" >'.$description
			.'</span></a>';
		}
		$str.='</label><textarea class="'.$this->formclass.'" '
		.'name="'.$field.'" id="'.$field.'" '
		.'rows="'.$rows.'" cols="'.$cols.'" >'
		.$value
		.'</textarea></li>';

		$strjs=$this->validatejsField($field, $fieldsection, 'textarea', $required);

		$this->formfields[$field]=$str;
		$this->fieldkeys[]=$field;
		$this->jsformfields[$field]=$strjs;
		return $field;
  }

	function validatejsField($field, $fieldsection, $type, $required) {
		$strjs='if (validateField("'.$field.'","'.$fieldsection.'","'.$type.'",'.$required.') == false)';
		$strjs.="\n	retVal=false\n";
		return $strjs;
	}

	function getjsValidate($keys=array()) {
		$jsformfields=$this->_get_from_keys($this->jsformfields, $keys);
		$str="function validate() { \n"
				."	retVal=true\n"
				.implode("\n", $jsformfields);
		if ($this->alert) {
				$str.="if(retVal == false) {\n"
				."	alert('Please correct the errors.  Fields marked with an asterisk (*) are required')\n"
				."	return false \n"
				."	}\n";
		}
		$str.="return retVal\n"
		."}\n";
		return $str;
	}

	function getFormValidation($keys=array()) {
		$str="<script> \n"
				."function validateField(fieldId, fieldsectionId, fieldType, required) {\n"
				."	fieldsection = document.getElementById(fieldsectionId)\n"
				."	fieldObj = document.getElementById(fieldId)\n"
				."	if (required ==1 && fieldType == 'time' ) { \n"
				."		if (!isTime(fieldObj.value)) { \n"
				."			fieldObj.focus()\n"
				."			return false \n"
				."		}	\n"
				."	}	\n"
				."	if (required ==1 && fieldType == 'date' ) { \n"
				."		if (!isDate(fieldObj.value)) { \n"
				."			fieldObj.focus()\n"
				."			return false \n"
				."		}	\n"
				."	}	\n"
				."	if(fieldType == 'text'  ||  fieldType == 'textarea'  ||  fieldType == 'password'  ||  fieldType == 'file' || fieldType == 'date' || fieldType == 'time' ) {\n"
				."	if(required == 1 && fieldObj.value == '') {\n"
				."		fieldObj.style.background='#EDDEDE'\n"
				."		fieldObj.focus()\n"
				."	return false \n"
				."	} else {\n"
				."		fieldObj.style.background='#FFFFFF'\n"
				."	}\n"
				."}\n"
				."}\n"
				."function sc(el) { \n"
				."		ShowCalendar(el,el,null,'','') \n"
				."} \n"
				."function isTime(strtime) {  \n"
				."	var re = /^\d{1,2}:\d{1,2}$/  \n"
				."	if (re.test(strtime)) {  \n"
				."		var dArr = strtime.split(':')  \n"
/*				."		var dobj = new Date(strtime)  \n"
				."		h = dobj.getHour() \n"
				."		m = dobj.getMinute() \n"
				."		if (dArr[0]!=h || dArr[1]!=m) \n"
				."			return false \n"
*/
				."		return true \n"
				."	}  \n"
				."	return false \n"
				."}  \n"
				."function isDate(strdate) {  \n"
				."	var re = /^\d{1,2}\/\d{1,2}\/\d{2,4}$/  \n"
				."	if (re.test(strdate)) {  \n"
				."		var dArr = strdate.split('/')  \n"
				."		var dobj = new Date(strdate)  \n"
				."		d = dobj.getDate() \n"
				."		m = dobj.getMonth()+1 \n"
				."		y = dobj.getFullYear() \n"
				."		if (dArr[0]!=m || dArr[1]!=d || dArr[2]!=y) \n"
				."			return false \n"
				."		return true \n"
				."	}  \n"
				."	return false \n"
				."}  \n"
				.$this->getjsValidate($keys)
				."</script> \n"
				."<script src='".$this->jspath."jscal/cal.js'></script> \n"
				."<script src='".$this->jspath."jscal/calx.js'></script> \n";

		return $str;
	}
}
?>
