function hexstr = file2hexstr(filename)
%file2hexstr:   Return a hexadecimal string
%               of a file
    fid = fopen(filename, 'r');
    data = fread(fid, 'uchar');
    fclose(fid);
    hexstr = [ reshape(dec2hex(data)', 1,[]) ];
end
