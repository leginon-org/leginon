// Read a *TRIANGLE* mesh from an OBJ file
//
// Inputs:
//   server_path  path to .obj file on server
//   mesh  mesh object
//   callback  function to call after async reading
// Returns mesh struct with:
//   .V  3d vertex posistions
//   .F  triangle indices into positions
//   .N  3d normal vectors
//   .FN  triangle indices into normals
//   .TC  2d texture coordinates
//   .FTC  triangle indices into texture coordinates
// Throws an error
function readOBJ_from_server(server_path,mesh,callback)
{
  var request = new XMLHttpRequest();
  // Hack so that resource is always reloaded
  // http://ajaxpatterns.org/XMLHttpRequest_Call#How_will_caching_be_controlled.3F
  request.open("GET",server_path);
  request.onreadystatechange = function () 
  {
    if (request.readyState == 4)
    {
      readOBJ_from_string(request.responseText,mesh);
      callback(mesh);
    }
  }
  request.send();
}

// Same as above but read from string synchronously
function readOBJ_from_string(string,mesh)
{
  mesh.V =   new Array();
  mesh.N =   new Array();
  mesh.TC =  new Array();
  mesh.F =   new Array();
  mesh.FN =  new Array();
  mesh.FTC = new Array();
  var lines = string.split("\n");
  for(var l = 0;l<lines.length;l++)
  {
    var data= lines[l].trim().split(" ");
    var key = data.shift();
    switch(key)
    {
      case "v":
        if(data.length != 3)
        {
          throw new Error("readOBJ_from_string: bad format");
        }
        mesh.V.push.apply(mesh.V,data.map(Number));
        break;
      case "vn":
        if(data.length != 3)
        {
          throw new Error("readOBJ_from_string: bad format");
        }
        mesh.N.push.apply(mesh.N,data.map(Number));
        break;
      case "vt":
        if(data.length < 2)
        {
          throw new Error("readOBJ_from_string: bad format");
        }
        mesh.TC.push.apply(mesh.TC,data.slice(0,2).map(Number));
        break;
      case "f":
        if(data.length != 3)
        {
          throw new Error("readOBJ_from_string: only triangles are supported");
        }
        for(var d = 0;d<data.length;d++)
        {
          var items = data[d].split("/");
          if(items[0].length > 0)
          {
            mesh.F.push((+items[0])-1);
          }
          if(items.length>=2 && items[1].length > 0)
          {
            mesh.FTC.push((+items[1])-1);
          }
          if(items.length>=3 && items[2].length > 0)
          {
            mesh.FN.push((+items[2])-1);
          }
        }
        if(
          (mesh.F.length != mesh.FN.length && mesh.FN.length > 0) || 
          (mesh.F.length != mesh.FTC.length && mesh.FTC.length > 0))
        {
          throw new Error("readOBJ_from_string: bad format");
        }
        break;
      case "":
        // ignore empty lines
        break;
      default:
        throw new Error("readOBJ_from_string: Unknown OBJ key: \""+key+"\"");
        break;
    }
  }
}
