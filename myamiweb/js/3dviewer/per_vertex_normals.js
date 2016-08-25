// Compute vertex normals via vertex position list, face list
// Inputs:
//   V  #V by 3 eigen Matrix of mesh vertex 3D positions
//   F  #F by 3 eigen Matrix of face (triangle) indices
//   FN  #F by 3 eigen Matrix of mesh face 3D normals
// Output:
//   N  #V by 3 eigen Matrix of mesh vertex 3D normals
function per_vertex_normals(V,F,FN)
{
  var N = new Array(V.length);
  // initialize to 0s
  for(var n = 0;n<N.length;n++)
  {
    N[n] = 0;
  }
  // loop over faces
  for(var f = 0;f<F.length/3;f++)
  {
    // throw normal at each corner
    for(var c = 0;c < 3;c++)
    {
      for(var d = 0;d < 3;d++)
      {
        N[F[3*f+c]*3+d] += FN[3*f+d];
      }
    }
  }
  // Normalize each row to average
  for(var n = 0;n<N.length/3;n++)
  {
    var len = 0;
    for(var d = 0;d < 3;d++)
    {
      len += N[n*3+d]*N[n*3+d];
    }
    len = Math.sqrt(len);
    if(len>0)
    {
      for(var d = 0;d < 3;d++)
      {
        N[n*3+d] /= len;
      }
    }
  }
  return N;
}
