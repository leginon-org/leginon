// REMOVE_UNREFERENCED Removes any rows in V that are not referenced in R
//
// Inputs:
//   V  #V by dim list of "vertex positions"
//   F  #F by anything list of indices into V (will be treated as F(:))
// Outputs:
//  RV  #V by dim vertex positions, order such that if the jth vertex is
//    some face in F, and the kth vertex is not then j comes before k
//  IM  #V by 1 list of indices such that: RF = IM(F) and RT = IM(T)
//    and RV(IM,:) = V
// 
// 
//
// Examples:
//   % Tet mesh in (V,T,F)
//   [V,I] = remove_unreferenced(V,[T(:);F(:)]);
//   T = I(T);
//   F = I(F);
//
function remove_unreferenced(V,F,RV,IM)
{
  var mark = new Array(V.length/3);
  for(var m=0;m<mark.length;m++)
  {
    mark[m] = false;
  }
  for(var f = 0;f<F.length;f++)
  {
    mark[F[f]] = true;
  }
  var newsize = 0;
  for(var m=0;m<mark.length;m++)
  {
    if(mark[m])
    {
      newsize++;
    }
  }
  RV.length = newsize*3;
  IM.length = V.length/3;
  var count = 0;
  for(var m=0;m<mark.length;m++)
  {
    if(mark[m])
    {
      RV[3*count+0] = V[3*m+0];
      RV[3*count+1] = V[3*m+1];
      RV[3*count+2] = V[3*m+2];
      IM[m] = count;
      count++;
    }
    else
    {
      IM[m] = -1;
    }
  }
}
