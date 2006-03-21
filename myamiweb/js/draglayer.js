
function getAbsLeft(o) {
	oLeft = o.offsetLeft
	while(o.offsetParent!=null) {
		oParent = o.offsetParent
		oLeft += oParent.offsetLeft
		o = oParent
	}
	return oLeft
}

function getAbsTop(o) {
	oTop = o.offsetTop
	while(o.offsetParent!=null) {
		oParent = o.offsetParent
		oTop += oParent.offsetTop
		o = oParent
	}
	return oTop
}

function setLeft(o,oLeft) {
	o.style.left = oLeft + "px"
}

function setTop(o,oTop) {
	o.style.top = oTop + "px"
}

function setPosition(o,oLeft,oTop) {
	setLeft(o,oLeft)
	setTop(o,oTop)
}
