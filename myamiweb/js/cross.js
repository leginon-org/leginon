
function drawcross(cx, cy, size, color, id, event) {
	if (!event)
			event=""
	var d=Math.round(size/2)
	cross='<div id="'+id+'" style="z-index:5;position:absolute;left:'+(cx-d)
			+'px;top:'+(cy-d)+'px;width:'+size+'px; height:'+size+'px; clip: rect(0pt,'+size+'px, '+size+'px, 0pt)"'
			+' '+event+' '
			+'>'
			+innercross(id, size, color)
			+'</div>'
	return cross
}


function innercross(id, size, color) {
			var d=Math.round(size/2)
			return '<div id="'+id+'" style="position: absolute; left: 0px; top: '+d+'px; width: '+size+'px; height: 1px; '
			+'clip: rect(0pt, '+size+'px, 1px, 0pt); background-color: '+color+'";"></div>'
			+'<div id="'+id+'" style="position: absolute; left: '+d+'px; top: 0px; width: 1px; height: '+size+'px; '
			+'clip: rect(0pt, 1px, '+size+'px, 0pt); background-color: '+color+';"></div>'
}
