var perline = 8;
var divSet = false;
var targetdivSet = false;
var curId;
var colorArray = Array();
var targetArray = Array();
var targetImageArray = Array();
var ie = false;
var nocolor = 'none';
if (document.all) { ie = true; nocolor = ''; }
function getObj(id) {
	if (ie) { return document.all[id]; } 
	else {	return document.getElementById(id);	}
}

function setColorbyId(id, color) {
	curId = id;
	setColor(color);
}

function setTargetbyId(id, target) {
	curId = id;
	setTarget(target);
}

function setColor(color) {
	var link = getObj(curId);
	var field = getObj(curId + 'field');
	var picker;
	field.value = color;
	if (color == '') {
	 	link.style.background = nocolor;
	 	link.style.color = nocolor;
	 	color = nocolor;
	} else {
	 	link.style.background = color;
	 	link.style.color = color;
	}
 	if (picker = getObj('colorpicker')) {
		picker.style.visibility= 'hidden';
	}
	eval(getObj(curId + 'field').title);
}

function getValue(id) {	
         if (field = getObj(id+ 'field'))		 
                 return field.value;	 
         else		 
                 return False;	 
}

function setTarget(target) {
	var link = getObj(curId);
	var field = getObj(curId + 'field');
	var picker;
	var index;
	field.value = target;
	if (target) {
		for (i = 0; i < targetArray.length; i++) {
			if (targetArray[i]==target) {
				index = i;
				break;
			}
		}
	 	link.src = targetImageArray[index];
	}
 	if (picker = getObj('targetpicker'))
		picker.style.visibility = 'hidden';
	eval(getObj(curId + 'field').title);
}
	
function setDiv() {	 
	if (!document.createElement) { return; }
	var elemDiv = document.createElement('div');
	if (typeof(elemDiv.innerHTML) != 'string') { return; }
	elemDiv.id = 'colorpicker';
	elemDiv.style.position = 'absolute';
	elemDiv.style.display = 'block';
	elemDiv.style.border = '#000000 1px solid';
	elemDiv.style.background = '#FFFFFF';
	elemDiv.innerHTML = '<span style="font-family:Verdana; font-size:11px;">' 
		+ getColorTable() 
	+ '</span>';

	document.body.appendChild(elemDiv);
	divSet = true;
}

function setTargetDiv() {	 
	if (!document.createElement) { return; }
	var elemDiv = document.createElement('div');
	if (typeof(elemDiv.innerHTML) != 'string') { return; }
	elemDiv.id = 'targetpicker';
	elemDiv.style.position = 'absolute';
	elemDiv.style.display = 'block';
	elemDiv.style.border = '#000000 1px solid';
	elemDiv.style.background = '#FFFFFF';
	elemDiv.innerHTML = '<span style="font-family:Verdana; font-size:11px;">' 
		+ getTargetTable() 
	+ '</span>';

	document.body.appendChild(elemDiv);
	targetdivSet = true;
}

function pickColor(id) {
	if (!divSet) { setDiv(); }
	var picker = getObj('colorpicker');	 	
	if (id == curId && picker.style.visibility == 'visible') {
		alert(picker.style.visibility);
		picker.style.visibility = 'hidden';
		return;
	}
	curId = id;
	var thelink = getObj(id);
	picker.style.top = getAbsoluteOffsetTop(thelink) + 20;
	picker.style.left = getAbsoluteOffsetLeft(thelink);	 
	picker.style.visibility = 'visible';
}

function pickTarget(id) {
	if (!targetdivSet) { setTargetDiv(); }
	var picker = getObj('targetpicker');	 	
	if (id == curId && picker.style.visibility == 'visible') {
		picker.style.visibility = 'hidden';
		return;
	}
	curId = id;
	var thelink = getObj(id);
	picker.style.top = getAbsoluteOffsetTop(thelink) + 20;
	picker.style.left = getAbsoluteOffsetLeft(thelink);	 
	picker.style.visibility = 'visible';
}

function getColorTable() {
	 var colors = colorArray;
	 var tableCode = '';
	 tableCode += '<table border="0" cellspacing="5" cellpadding="1">';
	 for (i = 0; i < colors.length; i++) {
		if (i % perline == 0) { tableCode += '<tr>'; }
		tableCode += '<td bgcolor="#000000" width="5" height="5"><a style="outline: 1px solid #000000; color: ' 
			+ colors[i] + '; background: ' + colors[i] + ';" title="' 
			+ colors[i] + '" href="javascript:setColor(\'' + colors[i] + '\');"><div style="width: 15px; height: 15px; background: ' + colors[i] + '"></div></a></td>';
		if (i % perline == perline - 1) { tableCode += '</tr>'; }
	 }
	 if (i % perline != 0) { tableCode += '</tr>'; }
	 tableCode += '</table>';
	 return tableCode;
}

function getTargetTable() {
	 var targets = targetArray;
	 var targetimages = targetImageArray;
	 var tableCode = '';
	 tableCode += '<table border="0" cellspacing="5" cellpadding="1">';
	 for (i = 0; i < targets.length; i++) {
		if (i % perline == 0) { tableCode += '<tr>'; }
		tableCode += '<td bgcolor="#000000" width="5" height="5"><a style="background: #FFFFFF" title="' 
			+ targets[i] + '" href="javascript:setTarget(\'' + targets[i] + '\');"><img border="0" src="' + targetimages[i] + '"></a></td>';
		if (i % perline == perline - 1) { tableCode += '</tr>'; }
	 }
	 if (i % perline != 0) { tableCode += '</tr>'; }
	 tableCode += '</table>';
	 return tableCode;
}

function getAbsoluteOffsetTop(obj) {
	var top = obj.offsetTop;
	var parent = obj.offsetParent;
	while (parent != document.body) {
		top += parent.offsetTop;
		parent = parent.offsetParent;
	}
	return top;
}

function getAbsoluteOffsetLeft(obj) {
	var left = obj.offsetLeft;
	var parent = obj.offsetParent;
	while (parent != document.body) {
		left += parent.offsetLeft;
		parent = parent.offsetParent;
	}
	return left;
}
