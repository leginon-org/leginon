if(document.all){
var s='';if(document.getElementById){
if(navigator.userAgent.indexOf('Mac')!=-1){
s+='BODY{ margin:0px; }\n';}
}
if(s!=''){
document.write('<style type="text/css">\n'+s+'<\/style>\n');}
}
function Bs_Slider() {
this.objectName;this.fieldName;this.direction       = 0;this.width           = 100;this.height          = 20;this.minVal          = 0;this.maxVal          = 100;this.valueDefault      = 0;this.arrowAmount     = 1;this.colorbar;this.baseZindex      = 1000;this.moveX = 0;this.moveY = 0;this.imgBasePath     = '/_bsJavascript/components/slider/img/';this.bgImgSrc;this.bgImgRepeat;this.sliderImgSrc;this.sliderImgWidth;this.sliderImgHeight;this.styleContainerClass;this.styleValueFieldClass = 'smalltxt spanSliderField';this.styleValueTextClass  = 'smalltxt spanSliderText';this.bgColor;this.arrowIconLeftSrc;this.arrowIconLeftWidth   = 0;this.arrowIconLeftHeight  = 0;this.arrowIconRightSrc;this.arrowIconRightWidth  = 0;this.arrowIconRightHeight = 0;this.valueInterval   = 1;this.useInputField = 2;this.inputTextFieldEvent = 'over';this.ctrl;this._valueInternal;this._display         = 2;this._arrowLeftId;this._arrowLeftObj;this._arrowRightId;this._arrowRightObj;this._pointerId;this._pointerObj;this._valueFieldId;this._valueFieldObj;this._valueTextId;this._valueTextObj;this._slideBarId;this._slideBarObj;this._colorbarId;this._colorbarObj;this._posUpperLeftX;this._posUpperLeftY;this._posSlideStart;this._posSlideEnd;this._slideWidth;this._attachedEvents;this.eventOnChange;this.slideStartCB;this.slideStartCD;this.slideMoveCB;this.slideMoveCD;this.slideEndCB;this.slideEndCD;this._checkup = function() {
if (typeof(this.minVal)     == 'undefined') this.minVal     = 0;if (typeof(this.maxVal)     == 'undefined') this.maxVal     = 10;if (typeof(this.valueDefault) == 'undefined') this.valueDefault = this.minVal;this._valueInternal = this.valueDefault;}
this.render = function(divName) {
this._checkup();this.attachOnArrow('bsSliderArrow');this.attachOnInputChange('bsSliderChangeByInput');this.attachOnInputBlur('bsSliderChangeByInputBlur');this._containerId  = 'co'  + divName;this._pointerId    = 'po'  + divName;this._arrowLeftId  = 'al'  + divName;this._arrowRightId = 'ar'  + divName;this._valueFieldId = 'vf'  + divName;if (this.fieldName == 'undefined') this.fieldName = this._valueFieldId;this._valueTextId  = 'vt'  + divName;this._slideBarId   = 'bar' + divName;this._colorbarId   = 'cb'  + divName;var divWidth  = this.width;var divHeight = this.height;var completeWidth   = this.width + this.arrowIconLeftWidth + this.arrowIconRightWidth + this.sliderImgWidth +15;var out      = new Array();var outI     = 0;var localOffset = 0;out[outI++] = '<div id="' + this._containerId + '"';if (this.styleContainerClass) {
out[outI++] = ' class="' + this.styleContainerClass + '"';}
out[outI++] = ' style="position:relative;';if (this._display == 0) {
out[outI++] = ' display:none;';} else if (this._display == 1) {
out[outI++] = ' visibility:hidden;';}
out[outI++] = '">';out[outI++] = '<div style="position:absolute; left:' + this.moveX + '; top:' + this.moveY + ';">';out[outI++] = '<div style="position:absolute; display:none; z-index:5000;" id="' + this._pointerId     + '">';out[outI++] = '<img name="bsslidericonname" src="' + this.imgBasePath + this.sliderImgSrc + '" border=0 width=' + this.sliderImgWidth + ' height=' + this.sliderImgHeight + '>';out[outI++] = '</div>';if ((this.arrowAmount > 0) && this.arrowIconLeftSrc) {
out[outI++] = '<div style="position:absolute; left:' + localOffset + '; top:0;"><a href="javascript:void(false);" onClick="' + this.objectName + '.onChangeByArrow(false);"><img src="' + this.imgBasePath + this.arrowIconLeftSrc + '" border=0 width=' + this.arrowIconLeftWidth + ' height=' + this.arrowIconLeftHeight + '></a></div>';localOffset += this.arrowIconLeftWidth;}
if (this.colorbar) {
out[outI++] = '<div id="' + this._colorbarId + '" onClick="' + this.objectName + '.onChangeByClick(event);"';if (this.colorbar['cssClass']) {
out[outI++] = ' class="' + this.colorbar['cssClass'] + '"';}
out[outI++] = ' style="position:absolute; z-index:4000; width:0;';if (this.colorbar['color']) {
out[outI++] = ' background-color:' + this.colorbar['color'] + ';';} else if (!this.colorbar['cssClass']) {
out[outI++] = ' background-color:orange;';}
if (this.colorbar['offsetLeft']) {
out[outI++] = ' left:' + (localOffset + this.colorbar['offsetLeft']) + ';';}
if (this.colorbar['offsetTop']) {
out[outI++] = ' top:' + this.colorbar['offsetTop'] + ';';}
if (this.colorbar['height']) {
out[outI++] = ' height:' + this.colorbar['height'] + ';';}
out[outI++] = '">';out[outI++] = '<img src="/_bsImages/spacer.gif" width="1" height="5"></div>';}
out[outI++] = '<div id="' + this._slideBarId + '" onClick="' + this.objectName + '.onChangeByClick(event);" style="position:absolute; left:' + localOffset + '; top:0; width:' + this.width + '; height: ' + divHeight + '; clip:rect(0 ' + divWidth + '  ' + divHeight + ' 0);';if (this.bgColor) {
out[outI++] = 'background-color:' + this.bgColor + '; layer-background-color:' + this.bgColor + ';';}
if (this.bgImgSrc) {
out[outI++] = ' background: url(' + this.imgBasePath + this.bgImgSrc + ') ' + this.bgImgRepeat + ';';}
out[outI++] = '"></div>';localOffset += this.width;if ((this.arrowAmount > 0) && this.arrowIconRightSrc) {
out[outI++] = '<div style="position:absolute; left:' + localOffset + '; top:0;"><a href="javascript:void(false);" onClick="' + this.objectName + '.onChangeByArrow(true);"><img src="' + this.imgBasePath + this.arrowIconRightSrc + '" border=0 width=' + this.arrowIconRightWidth + ' height=' + this.arrowIconRightHeight + '></a></div>';localOffset += this.arrowIconRightWidth;}
var styleValueFieldClass = (this.styleValueFieldClass) ? ' class="' + this.styleValueFieldClass + '"' : '';var styleValueTextClass  = (this.styleValueTextClass)  ? ' class="' + this.styleValueTextClass  + '"' : '';out[outI++] = '<div style="position:absolute; left:' + localOffset + '; top:0px;">';if (this.useInputField == 1) {
out[outI++] = '<span' + styleValueTextClass + ' id="' + this._valueTextId + '">' + this.valueDefault  + '</span>';out[outI++] = '<input type="hidden" name="' + this.fieldName + '" id="' + this._valueFieldId + '" value="' + this.valueDefault + '">';} else if (this.useInputField == 2) {
out[outI++] = '<input type="text"' + styleValueFieldClass + ' onMouseOver="bsFormFieldSetFocusAndSelect(this, false);" name="' + this.fieldName + '" id="' + this._valueFieldId + '" value="' + this.valueDefault + '" size="2"';if (styleValueFieldClass == '') {
out[outI++] = ' style="vertical-align:text-top; width:30; height:' + this.height + ';"';}
out[outI++] = ' onKeyUp="' + this.objectName + '.onChangeByInput(this.value, false);" onBlur="' + this.objectName + '.onChangeByInput(this.value, true);">';} else if (this.useInputField == 3) {
out[outI++] = '<input type="text"' + styleValueFieldClass + ' onMouseOver="bsFormFieldSetFocusAndSelect(this, false);" name="' + this.fieldName + '" id="' + this._valueFieldId + '" value="' + this.valueDefault + '" size="2"';if (styleValueFieldClass == '') {
out[outI++] = ' style="display:none; vertical-align:text-top; width:30; height:' + this.height + ';"';} else {
out[outI++] = ' style="display:none;"';}
out[outI++] = ' onKeyUp="' + this.objectName + '.onChangeByInput(this.value, false);" onBlur="' + this.objectName + '.onChangeByInput(this.value, true); ' + this.objectName + '.textboxEdit(false)">';out[outI++] = '<span' + styleValueTextClass + ' style="" id="' + this._valueTextId   + '" ';if (this.inputTextFieldEvent == 'click') {
out[outI++] = 'onClick="' + this.objectName + '.textboxEdit(true);"';} else {
out[outI++] = 'onMouseOver="' + this.objectName + '.textboxEdit(true);"';}
out[outI++] = '>' + this.valueDefault  + '</span>';} else {
out[outI++] = '<input type="hidden" name="' + this.fieldName + '" id="' + this._valueFieldId + '" value="' + this.valueDefault + '">';}
out[outI++] = '</div>';out[outI++] = '</div>';out[outI++] = '</div>';document.getElementById(divName).innerHTML = out.join('');this._containerObj  = document.getElementById(this._containerId);this._pointerObj    = document.getElementById(this._pointerId);this._arrowLeftObj  = document.getElementById(this._arrowLeftId);this._arrowRightObj = document.getElementById(this._arrowRightId);this._valueFieldObj = document.getElementById(this._valueFieldId);this._valueTextObj  = document.getElementById(this._valueTextId);this._slideBarObj   = document.getElementById(this._slideBarId);this._colorbarObj   = document.getElementById(this._colorbarId);this._posSlideStart = getDivLeft(this._slideBarObj);this._slideWidth    = this.width - this.sliderImgWidth;this._posSlideEnd   = this._posSlideStart + this._slideWidth;this._currentRelSliderPosX = this._posSlideStart;if (this.valueDefault > this.minVal) {
var hundertPercent = this.maxVal - this.minVal;var myPercent      = this.valueDefault * 100 / hundertPercent;this._currentRelSliderPosX += (myPercent * this._slideWidth / 100);this._updateColorbar(this._currentRelSliderPosX);}
this._pointerObj.style.left = this._currentRelSliderPosX;this._pointerObj.style.display = 'block';temp = ech_attachMouseDrag(this._pointerObj, slideStart,null, slideMove,null, slideEnd,null, null,null);temp = temp.linkCtrl(getDivImage('','bsslidericonname'));this.ctrl           = temp;this.ctrl.sliderObj = this;var x = getDivLeft(this._pointerObj);var y = getDivTop(this._pointerObj);y = 0;if (this.direction == 0) {
this.ctrl.minX = this._posSlideStart;this.ctrl.maxX = this._posSlideEnd;this.ctrl.minY = y; this.ctrl.maxY = y;} else {
alert('not implemented');}
}
this.draw = function(divName) {
this.render(divName);}
this.attachEvent = function(trigger, yourEvent) {
if (typeof(this._attachedEvents) == 'undefined') {
this._attachedEvents = new Array();}
if (typeof(this._attachedEvents[trigger]) == 'undefined') {
this._attachedEvents[trigger] = new Array(yourEvent);} else {
this._attachedEvents[trigger][this._attachedEvents[trigger].length] = yourEvent;}
}
this.hasEventAttached = function(trigger) {
return (this._attachedEvents && this._attachedEvents[trigger]);}
this.fireEvent = function(trigger) {
if (this._attachedEvents && this._attachedEvents[trigger]) {
var e = this._attachedEvents[trigger];if ((typeof(e) == 'string') || (typeof(e) == 'function')) {
e = new Array(e);}
for (var i=0; i<e.length; i++) {
if (typeof(e[i]) == 'function') {
e[i](this);} else if (typeof(e[i]) == 'string') {
eval(e[i]);}
}
}
}
this.attachOnChange = function(func) {
this.eventOnChange = func;}
this.attachOnSlideStart = function(func) {
this.slideStartCB = func;this.slideStartCD = 1;}
this.attachOnSlideMove = function(func) {
this.slideMoveCB = func;this.slideMoveCD = 2;}
this.attachOnSlideEnd = function(func) {
this.slideEndCB = func;this.slideEndCD = 3;}
this.attachOnArrow = function(functionName) {
this.eventOnArrow = functionName;}
this.attachOnInputChange = function(functionName) {
this.eventOnInputChange = functionName;}
this.attachOnInputBlur = function(functionName) {
this.eventOnInputBlur = functionName;}
this.setSliderIcon = function(src, width, height) {
this.sliderImgSrc    = src;this.sliderImgWidth  = width;this.sliderImgHeight = height;}
this.setArrowIconLeft = function(src, width, height) {
this.arrowIconLeftSrc    = src;this.arrowIconLeftWidth  = width;this.arrowIconLeftHeight = height;}
this.setArrowIconRight = function(src, width, height) {
this.arrowIconRightSrc    = src;this.arrowIconRightWidth  = width;this.arrowIconRightHeight = height;}
this.setBackgroundImage = function(src, repeat) {
this.bgImgSrc        = src;this.bgImgRepeat     = repeat;}
this.setDisplay = function(display) {
this._display = display;if (this._containerObj) {
switch (display) {
case 0:
this._containerObj.style.display = 'none';break;case 1:
this._containerObj.style.visibility = 'hidden';break;case 2:
this._containerObj.style.visibility = 'visible';this._containerObj.style.display = 'block';break;default:
}
}
}
this.getValue = function() {
return this._valueInternal;}
this.getSliderPos = function() {
return this.direction==0?
((getDivLeft(this.ctrl.div) - this.ctrl.minX) * (this.maxVal - this.minVal) / this.width + this.minVal):
((getDivTop (this.ctrl.div) - this.ctrl.minY) * (this.maxVal - this.minVal) / this.width + this.minVal);}
this.onChangeBySlide = function(ctrl) {
var newPos = this._getNewLocationFromCursor();var val = this._getValueByPosition(newPos);val = this._roundToGrid(val);if (val != this._valueInternal) {
this._valueInternal = val;this.updatePointer(newPos);this.updateValueField(val);this.updateValueText(val);this._updateColorbar(newPos);if ('undefined' != typeof(this.eventOnChange)) this.eventOnChange(this, val, newPos);this.fireEvent('onChange');}
}
this.onChangeByClick = function(event) {
var newPos = 0;if ('undefined' != typeof(event.offsetX)) {
newPos = event.offsetX + this._posSlideStart;} else if ('undefined' != typeof(event.layerX)) {
newPos = event.layerX + this._posSlideStart;} else {
return;}
var val = this._getValueByPosition(newPos);val = this._roundToGrid(val);if (val != this._valueInternal) {
this._valueInternal = val;this.updatePointer(newPos);this.updateValueField(val);this.updateValueText(val);this._updateColorbar(newPos);if ('undefined' != typeof(this.eventOnChange)) this.eventOnChange(this, val, newPos);this.fireEvent('onChange');}
}
this.onChangeByInput = function(val, isBlur) {
if (val == '') {
val = this.minVal;}
val = this._roundToGrid(val);var newPos = this._getPositionByValue(val);if (val != this._valueInternal) {
this._valueInternal = val;this.updatePointer(newPos);this._updateColorbar(newPos);if ('undefined' != typeof(this.eventOnChange)) this.eventOnChange(this, val, newPos);this.fireEvent('onChange');if (isBlur) {
this.updateValueField(val);this.updateValueText(val);}
} else if (isBlur) {
this.updateValueField(val);this.updateValueText(val);}
}
this.onChangeByArrow = function(leftOrRight) {
var val = this._valueInternal;if (leftOrRight) {
val += this.arrowAmount;} else {
val -= this.arrowAmount;}
val = this._roundToGrid(val);if (val != this._valueInternal) {
this._valueInternal = val;var newPos = this._getPositionByValue(val);this.updatePointer(newPos);this.updateValueField(val);this.updateValueText(val);this._updateColorbar(newPos);if ('undefined' != typeof(this.eventOnChange)) this.eventOnChange(this, val, newPos);this.fireEvent('onChange');}
}
this.onChangeByApi = function(val) {
var gridValue = this._roundToGrid(val);var newPos = this._getPositionByValue(gridValue);if (val != this._valueInternal) {
this._valueInternal = val;this.updatePointer(newPos);this._updateColorbar(newPos);if ('undefined' != typeof(this.eventOnChange)) this.eventOnChange(this, val, newPos);this.fireEvent('onChange');this.updateValueField(val);this.updateValueText(val);}
}
this._updateColorbar = function(newPos) {
if (this._colorbarObj) {
var newWidth = newPos + this.colorbar['widthDifference'];if (newWidth < 0) newWidth = 0;this._colorbarObj.style.width = newWidth;}
}
this._getValueByPosition = function(pos) {
pos -= this.ctrl.minX;var hundertPercent = this.ctrl.maxX - this.ctrl.minX;var myPercent      = pos / hundertPercent;var val            = this.minVal + ((this.maxVal - this.minVal) * myPercent);return val;}
this._getPositionByValue = function(val) {
val = val - this.minVal;var hundertPercent = this.maxVal - this.minVal;var myPercent      = val / hundertPercent;var pos            = this.ctrl.minX + ((this.ctrl.maxX - this.ctrl.minX) * myPercent);return pos;}
this._roundToGrid = function(val) {
val = parseFloat(val);if (isNaN(val)) return this.minVal;val = Math.round(val / this.valueInterval) * this.valueInterval;val = localRound(val);if (val < this.minVal) val = this.minVal;if (val > this.maxVal) val = this.maxVal;return val;}
this._getNewLocationFromCursor = function() {
var ox = this._posEventSlideStartX;var oy = this._posEventSlideStartY;switch(this.direction) {
case 0:
var t = this.ctrl.pageX - ox;var x = parseInt(this._posObjSlideStartX) + t;if (x > this.ctrl.maxX) x = this.ctrl.maxX;if (x < this.ctrl.minX) x = this.ctrl.minX;return x;if (this.ctrl.pageX > this.ctrl.maxX) {
x=this.ctrl.maxX;} else if (this.ctrl.pageX < this.ctrl.minX) {
x=this.ctrl.minX;} else {
x = this.ctrl.pageX;if (x < this.ctrl.minX) x = this.ctrl.minX;if (x > this.ctrl.maxX) x = this.ctrl.maxX;}
return x;break;case 1:
if(this.ctrl.pageY>this.ctrl.maxY)      y=this.ctrl.maxY;else if(this.ctrl.pageY<this.ctrl.minY) y=this.ctrl.minY;else {
y+=this.ctrl.pageY-this.ctrl.curY;if(y<this.ctrl.minY) y=this.ctrl.minY;if(y>this.ctrl.maxY) y=this.ctrl.maxY;}
return y;break;}
}
this.updatePointer = function(newPos) {
this._currentRelSliderPosX = newPos;this.ctrl.div.style.left = newPos;return;switch(this.direction) {
case 0:
moveDivTo(this.ctrl.div, newPos, getDivTop(this.ctrl.div));break;case 1:
moveDivTo(this.ctrl.div, getDivTop(this.ctrl.div), newPos);break;}
}
this.updateValueField = function(val) {
if (this._valueFieldObj) {
this._valueFieldObj.value = val;}
}
this.updateValueText = function(val) {
if (this._valueTextObj) {
this._valueTextObj.innerHTML = val;}
}
this.arrowOnClick = function() {
}
this.onChange = function(val) {
this.updateInputBox(val);if ('undefined' != typeof(this.eventOnChange)) this.eventOnChange(this, val);this.fireEvent('onChange');}
this.updateInputBox = function(val) {
val = localRound(val);if ('undefined' != typeof(this.localInput)) {
this.localInput.value = val;}
if ('undefined' != typeof(this.localText)) {
this.localText.innerHTML = val;}
}
this.textboxEdit = function(editMode) {
if (editMode) {
if ('undefined' != typeof(this._valueFieldObj)) {
this._valueTextObj.style.display = 'none';this._valueFieldObj.style.display = 'block';bsFormFieldSetFocusAndSelect(this._valueFieldObj, false);}
} else {
if ('undefined' != typeof(this._valueTextObj)) {
this._valueFieldObj.style.display = 'none';this._valueTextObj.style.display  = 'block';}
}
}
}
function localRound(val) {
return Math.round(val*100)/100;}
function slideStart(ctrl,client) {
ctrl.sliderObj._posEventSlideStartX = ctrl.startX;ctrl.sliderObj._posEventSlideStartY = ctrl.startY;ctrl.sliderObj._posObjSlideStartX = ctrl.sliderObj._pointerObj.style.left;ctrl.sliderObj._posObjSlideStartY = ctrl.sliderObj._pointerObj.style.top;var pos = ctrl.sliderObj.getSliderPos();ctrl.sliderObj.onChange(pos);if ('undefined' != typeof(ctrl.sliderObj.slideStartCB)) {
ctrl.sliderObj.slideStartCB(ctrl.sliderObj, ctrl.sliderObj.slideStartCD, pos);}
}
function slideMove(ctrl, client) {
ctrl.sliderObj.onChangeBySlide(ctrl);}
function slideEnd(ctrl,client){
return;}
function dout(str) {
var d = document.getElementById('debugWindow');if (d) d.innerText = str + "\n" + d.innerText;}
