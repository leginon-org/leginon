// Send mesh processing request to server
//
// Inputs:
//   server_path  path to server "processor"
//   mesh  input mesh object
//   process  processing to conduct
//   callback  function to call after async request has returned
function mesh_request(server_path,mesh,process,callback)
{
  // Serialize mesh
  var input_serial = "input="+encodeURIComponent(JSON.stringify({"V":mesh.V,"F":mesh.F}));
  var request = new XMLHttpRequest();
  request.open("POST",server_path);
  request.setRequestHeader('Content-type','application/x-www-form-urlencoded');
  //request.setRequestHeader("Content-length", mesh_serial.length);
  //request.setRequestHeader("Connection", "close");

  //// Hack so that resource is always reloaded
  //// http://ajaxpatterns.org/XMLHttpRequest_Call#How_will_caching_be_controlled.3F
  // Posts are never cached
  request.onreadystatechange = function () 
  {
    if (request.readyState != 4) return;
    if (request.status != 200 && request.status != 304) {
        alert('HTTP error ' + request.status);
        return;
    }
    callback(mesh,process,request);
  }
  request.send(input_serial+"&process="+process);
  loading.textContent = "request sent";
  loading.style.backgroundColor = "#afb";
  return false;
}

// Generic request handler. Update vertices of mesh
//
// Inputs:
//   server_path  path to server "processor"
//   mesh  input mesh object
//   process  processing to conduct
//   request  request that's just been returned
function update_vertices(mesh,process,request)
{
  //loading.textContent = request.responseText;
  loading.textContent = "Response received...";
  loading.style.backgroundColor = "#5f4";

  var output = JSON.parse(request.responseText);
  if(output["V"])
  {
    if(output["V"].length==mesh.V.length)
    {
      mesh.V = output["V"];
      handleLoadedMesh(mesh);
      loading.textContent = "";
    }else
    {
      alert("New vertices have wrong length!");
    }
  }
}
