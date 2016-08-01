var gl;
var WHITE = [1,1,1,1];
var DARK_BLUE = [0.3, 0.3, 0.5, 1.0];
var DARK_BLUE_HOVER = [0.4, 0.4, 0.6, 1.0];
var GO_GREEN = [0.3125, 1.0, 0.25, 1.0];
var back = DARK_BLUE.slice(0);
var old_back = back.slice(0);
var loading;
var zoom_z = 20;
var zoom_scroll_hover = false;
var rot = quat.fromValues(0,0,0,1);
var down_rot;
var trackball_down = false;
// sqrt(Number of anti-aliasing samples per pixel)
var aas = 4;

function initGL(canvas) {
    try {
      gl = WebGLDebugUtils.makeDebugContext(canvas.getContext("experimental-webgl",{antialias : true}));
      //var w = window.innerWidth/1.5;
      //var h = window.innerHeight/1.5;
      var w = parseInt(canvas.style.width);
      var h = w*9/16;
      // hack to get anti-aliasing http://stackoverflow.com/a/12574702/148668
      canvas.width  = w*aas;
      canvas.height = h*aas;
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";
      gl.viewportWidth = canvas.width;
      gl.viewportHeight = canvas.height;
    } catch (e) {
    }
    if(!gl) 
    {
      alert("Could not initialise WebGL, sorry :-(");
    }
}


function getShader(gl, id) {
    var shaderScript = document.getElementById(id);
    if (!shaderScript) {
        return null;
    }

    var str = "";
    var k = shaderScript.firstChild;
    while (k) {
        if (k.nodeType == 3) {
            str += k.textContent;
        }
        k = k.nextSibling;
    }

    var shader;
    if (shaderScript.type == "x-shader/x-fragment") {
        shader = gl.createShader(gl.FRAGMENT_SHADER);
    } else if (shaderScript.type == "x-shader/x-vertex") {
        shader = gl.createShader(gl.VERTEX_SHADER);
    } else {
        return null;
    }

    gl.shaderSource(shader, str);
    gl.compileShader(shader);

    if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
        alert(gl.getShaderInfoLog(shader));
        return null;
    }

    return shader;
}


var shaderProgram;

function initShaders() {
    var fragmentShader = getShader(gl, "per-fragment-lighting-fs");
    var vertexShader = getShader(gl, "per-fragment-lighting-vs");

    shaderProgram = gl.createProgram();
    gl.attachShader(shaderProgram, vertexShader);
    gl.attachShader(shaderProgram, fragmentShader);
    gl.linkProgram(shaderProgram);

    if (!gl.getProgramParameter(shaderProgram, gl.LINK_STATUS)) {
        alert("Could not initialise shaders");
    }

    gl.useProgram(shaderProgram);

    // Shader attributes
    shaderProgram.vertexPositionAttribute = gl.getAttribLocation(shaderProgram, "aVertexPosition");
    gl.enableVertexAttribArray(shaderProgram.vertexPositionAttribute);
    shaderProgram.vertexNormalAttribute = gl.getAttribLocation(shaderProgram, "aVertexNormal");
    gl.enableVertexAttribArray(shaderProgram.vertexNormalAttribute);
    shaderProgram.textureCoordAttribute = gl.getAttribLocation(shaderProgram, "aTextureCoord");
    gl.enableVertexAttribArray(shaderProgram.textureCoordAttribute);

    // Shader uniforms
    shaderProgram.pMatrixUniform = gl.getUniformLocation(shaderProgram, "uPMatrix");
    shaderProgram.mvMatrixUniform = gl.getUniformLocation(shaderProgram, "uMVMatrix");
    shaderProgram.nMatrixUniform = gl.getUniformLocation(shaderProgram, "uNMatrix");
    shaderProgram.samplerUniform = gl.getUniformLocation(shaderProgram, "uSampler");
    shaderProgram.materialShininessUniform = gl.getUniformLocation(shaderProgram, "uMaterialShininess");
    shaderProgram.showSpecularHighlightsUniform = gl.getUniformLocation(shaderProgram, "uShowSpecularHighlights");
    shaderProgram.useTexturesUniform = gl.getUniformLocation(shaderProgram, "uUseTextures");
    shaderProgram.useLightingUniform = gl.getUniformLocation(shaderProgram, "uUseLighting");
    shaderProgram.ambientColorUniform = gl.getUniformLocation(shaderProgram, "uAmbientColor");
    shaderProgram.pointLightingLocationUniform = gl.getUniformLocation(shaderProgram, "uPointLightingLocation");
    shaderProgram.pointLightingSpecularColorUniform = gl.getUniformLocation(shaderProgram, "uPointLightingSpecularColor");
    shaderProgram.pointLightingDiffuseColorUniform = gl.getUniformLocation(shaderProgram, "uPointLightingDiffuseColor");
}


function handleLoadedTexture(texture) {
    gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL, true);
    gl.bindTexture(gl.TEXTURE_2D, texture);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, texture.image);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_NEAREST);
    gl.generateMipmap(gl.TEXTURE_2D);

    gl.bindTexture(gl.TEXTURE_2D, null);
}


var earthTexture;
var galvanizedTexture;

function initTextures() {
    earthTexture = gl.createTexture();
    earthTexture.image = new Image();
    earthTexture.image.onload = function () {
        handleLoadedTexture(earthTexture)
    }
    earthTexture.image.src = "earth.jpg";

    galvanizedTexture = gl.createTexture();
    galvanizedTexture.image = new Image();
    galvanizedTexture.image.onload = function () {
        handleLoadedTexture(galvanizedTexture)
    }
    galvanizedTexture.image.src = "arroway.de_metal+structure+06_d100_flat.jpg";
}

var mvMatrix = mat4.create();
var mvMatrixStack = [];
var pMatrix = mat4.create();

function mvPushMatrix() {
    var copy = mat4.create();
    mat4.set(mvMatrix, copy);
    mvMatrixStack.push(copy);
}

function mvPopMatrix() {
    if (mvMatrixStack.length == 0) {
        throw "Invalid popMatrix!";
    }
    mvMatrix = mvMatrixStack.pop();
}

function setMatrixUniforms() {
    gl.uniformMatrix4fv(shaderProgram.pMatrixUniform, false, pMatrix);
    gl.uniformMatrix4fv(shaderProgram.mvMatrixUniform, false, mvMatrix);

    var normalMatrix = mat3.create();
    mat3.normalFromMat4(normalMatrix,mvMatrix);
    gl.uniformMatrix3fv(shaderProgram.nMatrixUniform, false, normalMatrix);
}

function degToRad(degrees) {
    return degrees * Math.PI / 180;
}

function Mesh()
{
  // Original data
  this.V;
  this.centroid;
  this.min;
  this.max;
  this.scale;
  this.F;
  this.N;
  this.FN;
  this.VN;
  this.TC;
  this.FTC;
  // VBO data
  this.VBOs = [];
}

function VBO()
{
  this.V = [];
  this.N = [];
  this.TC = [];
  this.F = [];
  this.PositionBuffer = null;
  this.NormalBuffer = null;
  this.TextureCoordBuffer = null;
  this.IndexBuffer = null;
}

var mesh = new Mesh();


function handleLoadedTeapot(teapotData,mesh) {
  mesh.V = teapotData.vertexPositions;
  mesh.N = teapotData.vertexNormals;
  mesh.TC = teapotData.vertexTextureCoords;
  mesh.F = teapotData.indices;
  handleLoadedMesh(mesh);
}

function handleLoadedMesh(mesh)
{
  // Scale and shift
  mesh.centroid = vec3.create([0,0,0]);
  mesh.min = [Number.MAX_VALUE,Number.MAX_VALUE,Number.MAX_VALUE];
  mesh.max = [Number.MIN_VALUE,Number.MIN_VALUE,Number.MIN_VALUE];
  for(var v = 0; v<mesh.V.length/3;v++)
  {
    for(var d = 0; d<3;d++)
    {
     mesh.centroid[d] += mesh.V[v+d];
     mesh.min[d] = Math.min(mesh.V[v+d],mesh.min[d]);
     mesh.max[d] = Math.max(mesh.V[v+d],mesh.max[d]);
    }
  }
  vec3.scale(mesh.centroid, mesh.centroid,-3.0/mesh.V.length);
  mesh.scale = 0;
  for(var d = 0; d<3;d++)
  {
    mesh.scale = Math.max(mesh.scale,mesh.max[d]-mesh.min[d])
  }

  // Compute per vertex normals
  if(mesh.N.length == 0)
  {
    mesh.FN = per_face_normals(mesh.V,mesh.F);
    mesh.VN = per_vertex_normals(mesh.V,mesh.F,mesh.FN);
  }else
  {
    // To respect these normals we'll have to separate shared vertices
    // Instead just keep them if they are already per vertex normals
    if(mesh.N.length == mesh.V.length)
    {
      mesh.VN = mesh.N;
    }else
    {
      mesh.FN = per_face_normals(mesh.V,mesh.F);
      mesh.VN = per_vertex_normals(mesh.V,mesh.F,mesh.FN);
    }
  }

  mesh.VBOs = [];
  if(mesh.V.length/3 >= 65535)
  {
    // need to split up
    var F = mesh.F.slice(0);
    while(F.length > 0)
    {
      var vbo = new VBO();
      var end = Math.min(65535,F.length);
      var temp_F = F.splice(0,end);
      var IM = [];
      remove_unreferenced(mesh.V,temp_F,vbo.V,IM);
      // remap normals
      vbo.N = new Array(vbo.V.length);
      for(var v = 0;v<mesh.V.length/3;v++)
      {
        if(IM[v]>=0 && IM[v]<vbo.N.length/3)
        {
          for(var d = 0;d<3;d++)
          {
            vbo.N[3*IM[v]+d] = mesh.VN[3*v+d];
          }
        }
      }
      // remap face indices
      vbo.F = new Array(temp_F.length);
      for(var f = 0;f<temp_F.length;f++)
      {
        vbo.F[f] = IM[temp_F[f]];
      }
      mesh.VBOs.push(vbo);
    }
  }else
  {
    mesh.VBOs.push(new VBO());
    mesh.VBOs[0].V = mesh.V;
    mesh.VBOs[0].N = mesh.VN;
    mesh.VBOs[0].TC = mesh.TC;
    mesh.VBOs[0].F = mesh.F;
  }

  // Assumes browser is calling deleteBuffer
  // Loop over vbos in mesh
  for(var v = 0;v<mesh.VBOs.length;v++)
  {
    var vbo = mesh.VBOs[v];
    if(vbo.V.length/3 != vbo.N.length/3)
    {
      vbo.N = vbo.V;
    }
    vbo.NormalBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo.NormalBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(vbo.N), gl.STATIC_DRAW);
    vbo.NormalBuffer.itemSize = 3;
    vbo.NormalBuffer.numItems = vbo.N.length / 3;

    if(vbo.V.length/3 != vbo.TC.length/2)
    {
      vbo.TC = vbo.V;
    }
    vbo.TextureCoordBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo.TextureCoordBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(vbo.TC), gl.STATIC_DRAW);
    vbo.TextureCoordBuffer.itemSize = 2;
    vbo.TextureCoordBuffer.numItems = vbo.TC.length / 2;

    vbo.PositionBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, vbo.PositionBuffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(vbo.V), gl.STATIC_DRAW);
    vbo.PositionBuffer.itemSize = 3;
    vbo.PositionBuffer.numItems = vbo.V.length / 3;

    vbo.IndexBuffer = gl.createBuffer();
    gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, vbo.IndexBuffer);
    gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint16Array(vbo.F), gl.STATIC_DRAW);
    vbo.IndexBuffer.itemSize = 1;
    vbo.IndexBuffer.numItems = vbo.F.length;
  }
}


var teapotAngle = 180;

function drawScene() {
    gl.viewport(0, 0, gl.viewportWidth, gl.viewportHeight);
    gl.clearColor(back[0], back[1], back[2], 1.0);
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

    //mat4.perspective(45, gl.viewportWidth / gl.viewportHeight, 0.1, 100.0, pMatrix);
    mat4.perspective(pMatrix,45, gl.viewportWidth / gl.viewportHeight, 0.1, 100.0);

    if(mesh.VBOs.length == 0)
    {
      return;
    }

    var specularHighlights = 1;
    gl.uniform1i(shaderProgram.showSpecularHighlightsUniform, specularHighlights);

    var lighting = 1;
    gl.uniform1i(shaderProgram.useLightingUniform, lighting);
    if (lighting) {
        gl.uniform3f(
            shaderProgram.ambientColorUniform,
            0.2,
            0.2,
            0.2
        );

        gl.uniform3f(
            shaderProgram.pointLightingLocationUniform,
            -10.,
            4.,
            200.
        );

        gl.uniform3f(
            shaderProgram.pointLightingSpecularColorUniform,
            0.8,
            0.8,
            0.8
        );

        gl.uniform3f(
            shaderProgram.pointLightingDiffuseColorUniform,
            0.8,
            0.8,
            0.8
        );
    }

    var texture = "none";
    gl.uniform1i(shaderProgram.useTexturesUniform, texture != "none");

    mat4.identity(mvMatrix);

    mat4.translate(mvMatrix,mvMatrix,[0, 0, -40]);
    //mat4.rotate(mvMatrix, degToRad(teapotAngle), [0, 1, 0]);
    //mat4.multiply(mvMatrix,quat.toMat4(rot));
    mat4.multiply(mvMatrix,mvMatrix,mat4.fromQuat(mat4.create(),rot));
    //mat4.scale(mvMatrix, 1.0/mesh.scale, 1.0/mesh.scale, 1.0/mesh.scale);
    mat4.scale(mvMatrix,mvMatrix,[zoom_z/mesh.scale, zoom_z/mesh.scale, zoom_z/mesh.scale]);
    mat4.translate(mvMatrix, mvMatrix, mesh.centroid);
    //mat4.rotate(mvMatrix, degToRad(23.4), [1, 0, -1]);

    gl.activeTexture(gl.TEXTURE0);
    if (texture == "earth") {
        gl.bindTexture(gl.TEXTURE_2D, earthTexture);
    } else if (texture == "galvanized") {
        gl.bindTexture(gl.TEXTURE_2D, galvanizedTexture);
    }
    gl.uniform1i(shaderProgram.samplerUniform, 0);

    gl.uniform1f(shaderProgram.materialShininessUniform, 32.0);

    // loop over vbos
    for(var v = 0;v<mesh.VBOs.length;v++)
    {
      var vbo = mesh.VBOs[v];
      if(vbo.PositionBuffer == null || 
         vbo.NormalBuffer == null || 
         vbo.TextureCoordBuffer == null || 
         vbo.IndexBuffer == null) 
      {
        return;
      }

      gl.bindBuffer(gl.ARRAY_BUFFER, vbo.PositionBuffer);
      gl.vertexAttribPointer(shaderProgram.vertexPositionAttribute, vbo.PositionBuffer.itemSize, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ARRAY_BUFFER, vbo.TextureCoordBuffer);
      gl.vertexAttribPointer(shaderProgram.textureCoordAttribute, vbo.TextureCoordBuffer.itemSize, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ARRAY_BUFFER, vbo.NormalBuffer);
      gl.vertexAttribPointer(shaderProgram.vertexNormalAttribute, vbo.NormalBuffer.itemSize, gl.FLOAT, false, 0, 0);

      gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, vbo.IndexBuffer);
      setMatrixUniforms();
      gl.drawElements(gl.TRIANGLES, vbo.IndexBuffer.numItems, gl.UNSIGNED_SHORT, 0);
    }
}


var lastTime = 0;

function animate() {
    var timeNow = new Date().getTime();
    if (lastTime != 0) {
        var elapsed = timeNow - lastTime;

        teapotAngle += 0.05 * elapsed;
    }
    lastTime = timeNow;
}


function tick() {
    requestAnimFrame(tick);
    drawScene();
    animate();
}

function init_stats()
{
  // Set up stats
  var stats = new Stats();
  stats.setMode(0); // 0: fps, 1: ms
  
  // Align top-left
  stats.domElement.style.position = 'absolute';
  stats.domElement.style.left = '0px';
  stats.domElement.style.top = '0px';
  stats.domElement.style.overflow = 'hidden';
  
  document.body.appendChild( stats.domElement );
  
  setInterval( function () {
   stats.begin();
   stats.end();
  }, 1000 / 60 );
}

// Sets up canvas object to fire mouseDown, mouseDrag and mouseUp
// events even if drag leaves canvas object. 
// Input:
//   c  canvas object that implements:
//        mouseDown(x,y)
//        mouseDrag(x,y,dx,dy)
//        mouseUp(x,y)
//      returning true if object c accepts the event.
//
// Ideally this should be extended to accept a list of any objects
// that implement the above functions.
//
// Source:
// http://bytes.com/topic/javascript/answers/837372-follow-mousemove-events-outside-browser
function setupCanvasMousing(c)
{
  //add these vars to document
  document.mouseDiffX = 0; 
  document.mouseDiffY = 0;
  document.oldMouseX = 0;
  document.oldMouseY = 0;
  document.down_object = null;
  document.hover_object = c;

  // Tell object c what to do when it hears a mouse down event
  c.mouseDownHandler = function(event) 
  {
    var pos = document.getAbsolutePosition(this);
    // Not sure if this will work on Opera
    document.mouseDiffX = event.screenX - (event.pageX - pos.x); //pageX gives scroll
    document.mouseDiffY = event.screenY - (event.pageY - pos.y);
    document.oldMouseX = event.pageX - pos.x;
    document.oldMouseY = event.pageY - pos.y;
    this.shift_down = event.shiftKey;
    var mouse_pos = find_true_mouse(event,c);

    // Call object c's mouseDown(x,y) function
    if (this.mouseDown(mouse_pos.x,mouse_pos.y))
    {
      // If object c accepted the mouse then tell the document to:
      // disallow selection
      document.disableMouseSelection();
      // any mouse moves are now drags
      document.removeEventListener("mousemove", document.mouseMoveHandler, false);
      document.addEventListener("mousemove", document.mouseDragHandler, false);
      // any mouse ups should be handled specially
      document.addEventListener("mouseup", document.mouseUpHandler, false);
      // tell the document who was clicked
      document.down_object = c;
      this.prev_mouse_pos = mouse_pos;
    }
  };

  // Tell the document how to handle drags
  document.mouseDragHandler = function(event) 
  {
    //var realx = event.screenX - this.mouseDiffX;
    //var realy = event.screenY - this.mouseDiffY;
    if(this.down_object)
    {
      var mouse_pos = find_true_mouse(event,this.down_object);
      // tell the object that recieved the original click to drag
      this.down_object.mouseDrag(
          mouse_pos.x, 
          mouse_pos.y, 
          mouse_pos.x - this.down_object.prev_mouse_pos.x, 
          mouse_pos.y - this.down_object.prev_mouse_pos.y);
      this.down_object.prev_mouse_pos = mouse_pos;
    }
    //this.oldMouseX = realx;
    //this.oldMouseY = realy;
  };

  document.mouseMoveHandler = function(event)
  {
    if(this.hover_object)
    {
      //var pos = document.getAbsolutePosition(this.hover_object);
      var mouse_pos = find_true_mouse(event,this.hover_object);

      this.shift_down = event.shiftKey;

      this.hover_object.mouseMove(
          mouse_pos.x, 
          mouse_pos.y, 
          0,0);
    }
  }

  // Tell the document how to handle the up event
  document.mouseUpHandler = function(event) 
  {
    this.removeEventListener("mousemove", this.mouseDragHandler, false);
    this.addEventListener("mousemove", this.mouseMoveHandler, false);
    this.removeEventListener("mouseup", this.mouseUpHandler, false);
    if(this.down_object)
    {
      this.down_object.mouseUp(
          event.screenX-this.mouseDiffX, 
          event.screenY-this.mouseDiffY);
    }
    // reset down_object to null, so that any time this.down_object
    // contains null unless something's being dragged
    this.down_object = null;
    this.enableMouseSelection();
  };

  // Get the absolute position of a screen element
  // Input:
  //   element  screen element in question
  // Return:
  //   (x,y) coordinates of top left corner of element
  document.getAbsolutePosition = function(element) 
  {
    var r = { x: element.offsetLeft, y: element.offsetTop };
    if (element.offsetParent) {
      var tmp = this.getAbsolutePosition(element.offsetParent);
      r.x += tmp.x;
      r.y += tmp.y;
    }
    return r;
  };

  // Turn off selection
  document.disableMouseSelection = function() 
  {
    this.onselectstart = function() { return false; };
  };

  // Turn on selection
  document.enableMouseSelection = function() 
  {
    this.onselectstart = function() { return true; };
  };

  // Hook up c's mousedown event to the mouseDownHandler we just
  // defined
  c.addEventListener("mousedown", c.mouseDownHandler, false);
  document.addEventListener("mousemove", document.mouseMoveHandler, false);
}

function init_mouse(canvas)
{
  canvas.mouseDown = function (x,y)
  {
    //loading.textContent = ""+x+","+y+"!";
    // Antialiasing trick means these (x,y) don't match canvas.width or
    // gl.viewportWidth
    x = x*aas;
    y = y*aas;
    this.down_x = x;
    this.down_y = y;
    if(this.down_y>=0 && this.down_y<=canvas.height)
    {
      if(
        this.down_x>(canvas.width-100*aas) && 
        this.down_x<=canvas.width && 
        this.down_y>=0 && this.down_y<=canvas.height)
      {
        zoom_scroll_hover = true;
        trackball_down = false;
      }else
      {
        zoom_scroll_hover = false;
        trackball_down = true;
        down_rot = quat.clone(rot);
      }
    }
    return true;
  }
  canvas.mouseUp = function (x,y) 
  {
    //loading.textContent = ""+x+","+y+"^";
    x = x*aas;
    y = y*aas;
  }
  canvas.mouseDrag = function (x,y,dx,dy) 
  {
    //loading.textContent = ""+x+","+y+"?>";
    x = x*aas;
    y = y*aas;
    dx = dx*aas;
    dy = dy*aas;
    if(zoom_scroll_hover)
    {
      zoom_z = Math.min(160,Math.max(1,zoom_z+dy));
    }else if(trackball_down)
    {
      rot = trackball(
        gl.viewportWidth/aas,
        gl.viewportHeight/aas,
        4,
        down_rot,
        this.down_x/aas,
        this.down_y/aas,
        x/aas,
        y/aas)
    }
  }
  canvas.mouseMove = function(x,y,dx,dy)
  {
    //loading.textContent = ""+x+","+y; 
    x = x*aas;
    y = y*aas;
    if(
      x>(canvas.width-100*aas) && 
      x<=canvas.width && 
      y>=0 && y<=canvas.height)
    {
      if(!zoom_scroll_hover)
      {
        old_back = back.slice(0);
        back[0] = (1-(1-back[0])*0.9);
        back[1] = (1-(1-back[1])*0.9);
        back[2] = (1-(1-back[2])*0.9);
      }
      zoom_scroll_hover = true;
    }else
    {
      zoom_scroll_hover = false;
      back = old_back.slice(0);
    }
  }
}

function submitLocalFile(file)
{
  // obtain input element through DOM  
  handleFiles(document.getElementById('file').files);
}

function handleFiles(files)
{
  // only handle one
  var file = files[0];
  if(file)
  {
    var reader;
    try
    {
      reader = new FileReader();
    }catch(e)
    {
      alert("Error: seems File API is not supported on your browser");
      return;
    }
    // Read file into memory as UTF-8      
    reader.readAsText(file, "UTF-8");
    // Handle progress, success, and errors
    reader.onprogress = function(evt)
    {
      if (evt.lengthComputable)
      {
        // evt.loaded and evt.total are ProgressEvent properties
        var loaded = (evt.loaded / evt.total);
        if (loaded < 1)
        {
          loading.textContent = "Reading local file ("+Math.round(loaded*100)+"%)...";
          loading.style.backgroundColor = "#54f";
        }
      }
    }
    reader.onload = function(evt)
    {
      setTimeout(function(){
        readOBJ_from_string(evt.target.result,mesh);
        setTimeout(function(){handleLoadedMesh(mesh);loading.textContent="";},0);
        loading.textContent = "Handling OBJ...";
        loading.style.backgroundColor = "#fab";
      },0);
      loading.textContent = "Loading OBJ...";
      loading.style.backgroundColor = "#5f4";
    }
    reader.onerror = function(evt)
    {
      if(evt.target.error.code == evt.target.error.NOT_READABLE_ERR)
      {
        // The file could not be read
        alert("Error reading file...");
      }
    }
  }
}

function init_drag_and_drop(canvas)
{
  canvas.addEventListener("dragenter", 
    function (evt){
      evt.stopPropagation();
      evt.preventDefault();
      old_back = back.slice(0);
      back = GO_GREEN.slice(0);
    }, false);
  canvas.addEventListener("dragleave", 
    function (evt){
      evt.stopPropagation();
      evt.preventDefault();
      back = old_back.slice(0);
    }, false);
  canvas.addEventListener("dragover", function(evt){}, false);
  canvas.addEventListener("drop",
    function(evt){
      evt.stopPropagation();
      evt.preventDefault();
      back = old_back.slice(0);
      var files = evt.dataTransfer.files;
      var count = files.length;
      // Only call the handler if 1 or more files was dropped.
      if(count > 0)
      {
        handleFiles(files);
      }
    }, false);
}


