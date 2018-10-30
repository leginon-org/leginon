// Applies a trackball drag to a given rotation
// Inputs:
//   w  width of the trackball context
//   h  height of the trackball context
//   speed_factor  controls how fast the trackball feels, 1 is normal
//   down_q  rotation at mouse down, i.e. the rotation we're applying the
//     trackball motion to (as quaternion)
//   down_x  x position of mouse down
//   down_y  y position of mouse down
//   x  current x position of mouse
//   y  current y position of mouse
// Outputs:
//   quat  the resulting rotation (as quaternion)
//
// This is largely the trackball as implemented in AntTweakbar. Much of the
// code is straight from its source in TwMgr.cpp
// http://www.antisphere.com/Wiki/tools:anttweakbar
function trackball(w,h,speed_factor,down_q,down_x,down_y,x,y)
{
  var qrot = trackball_helper(w,h,speed_factor,down_x,down_y,x,y);
  var nqorig = quat.length(down_q);

  if(Math.abs(nqorig)>DOUBLE_EPS)
  {
      var qorig = quat.fromValues(
        down_q[0]/nqorig,
        down_q[1]/nqorig,
        down_q[2]/nqorig,
        down_q[3]/nqorig);
      quat.multiply(qrot,qrot,qorig);
  }
  return qrot;
}

function trackball_helper(w,h,speed_factor,down_x,down_y,x,y)
{
  var original_x = 
    quatIX(speed_factor*(down_x-w/2)+w/2, w, h);
  var original_y = 
    quatIY(speed_factor*(down_y-h/2)+h/2, w, h);

  var x = quatIX(speed_factor*(x-w/2)+w/2, w, h);
  var y = quatIY(speed_factor*(y-h/2)+h/2, w, h);

  var z = 1;
  var n0 = Math.sqrt(original_x*original_x + original_y*original_y + z*z);
  var n1 = Math.sqrt(x*x + y*y + z*z);
  var out = quat.create();
  if(n0>DOUBLE_EPS && n1>DOUBLE_EPS)
  {
    var v0 = vec3.fromValues(original_x/n0, original_y/n0, z/n0);
    var v1 = vec3.fromValues(x/n1, y/n1, z/n1 );
    var axis = vec3.create();
    vec3.cross(axis,v0,v1);
    var sa = Math.sqrt(vec3.dot(axis, axis));
    var ca = vec3.dot(v0, v1);
    var angle = Math.atan2(sa, ca);
    if( x*x+y*y>1.0 )
    {
      angle *= 1.0 + 0.2*(Math.sqrt(x*x+y*y)-1.0);
    }
    quat.setAxisAngle(out,axis,angle);
    quat.normalize(out,out);
  }
  return out;
}
// Utility IGL_INLINE functions
function quatD(w,h)
{
  return (Math.abs(w) < Math.abs(h) ? Math.abs(w) : Math.abs(h)) - 4;
}
function quatIX(x,w,h)
{
  return (2.0*x - w - 1.0)/quatD(w,h);
}
function quatIY(y,w,h)
{
  return (-2.0*y + h - 1.0)/quatD(w, h);
}
