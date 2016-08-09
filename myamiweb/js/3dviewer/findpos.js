// http://stackoverflow.com/a/4853048/148668
function Pos()
{
  this.x = 0;
  this.y = 0;
}

function findpos(obj) {
  var pos = new Pos();

    if (obj.offsetParent) {
        do {
            pos.x += obj.offsetLeft;
            pos.x -= obj.scrollLeft;
            pos.y += obj.offsetTop;
            pos.y -= obj.scrollTop;
        } while (obj = obj.offsetParent);

        return pos;
    }
}

function find_true_mouse(event,object)
{
  var pos = findpos(object);
  // Not sure if this will work on Opera
  // This does not work if canvas is in overflow auto container
  document.mouseDiffX = event.screenX - (event.pageX - pos.x); //pageX gives scroll
  document.mouseDiffY = event.screenY - (event.pageY - pos.y);
  document.oldMouseX = event.pageX - pos.x;
  document.oldMouseY = event.pageY - pos.y;
  var mouse_pos = new Pos();
  mouse_pos.x = event.screenX - document.mouseDiffX;
  mouse_pos.y = event.screenY - document.mouseDiffY;
  return mouse_pos;
}
