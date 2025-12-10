*...under construction...*

## CCP4, MRC, and variants

  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
     byte\       word\       word\       field       type      description                    [CCP4](http://www.ccp4.ac.uk/html/maplib.html#description)   [MRC](http://www2.mrc-lmb.cam.ac.uk/research/locally-developed-software/image-processing-software/#image)   [MRC-IMOD](http://bio3d.colorado.edu/imod/doc/mrc_format.txt)
    offset     offset\      index\                                                                                                                                                                                                                                     
             (first=0)   (first=1)                                                                                                                                                                                                                                     
  -------- ----------- ----------- ----------------- --------- ------------------------------ ------------------------------------------------------------ ----------------------------------------------------------------------------------------------------------- ---------------------------------------------------------------
         0           0           1       N ~x~       int32     3-D size of data array,\                                                                                                                                                                                
                                                               fastest changing first                                                                                                                                                                                  

         4           1           2       N ~y~       int32                                                                                                                                                                                                             

         8           2           3       N ~z~       int32                                                                                                                                                                                                             

        12           3           4       mode        int32     data type:\                    additionally:\                                                                                                                                                           additionally:
                                                               0: signed 8-bit integer\       5: same as mode 0                                                                                                                                                        6: 16-bit unsigned integer
                                                               1: signed 16-bit integer\                                                                                                                                                                               16: 3x8-bit unsigned int, RGB
                                                               2: 32-bit float\                                                                                                                                                                                        NOTE: mode 0 may be signed
                                                               3: 16-bit complex integer\                                                                                                                                                                              or unsigned depending
                                                               4: 32-bit complex float                                                                                                                                                                                 on codes found at byte
                                                                                                                                                                                                                                                                       offset 152 and 156

        16           4           5     Start ~x~     int32     number of the first element\                                                                                                                                                                            
                                                               in each dimension, if this\                                                                                                                                                                             
                                                               is a sub-array of another                                                                                                                                                                               

        20           5           6     Start ~y~     int32                                                                                                                                                                                                             

        24           6           7     Start ~z~     int32                                                                                                                                                                                                             

        28           7           8   Intervals ~x~   int32     number of grid intervals\                                                                                                                                                                               
                                                               along each dimension                                                                                                                                                                                    

        32           8           9   Intervals ~y~   int32                                                                                                                                                                                                             

        36           9          10   Intervals ~z~   int32                                                                                                                                                                                                             

        40          10          11  Cell Length ~x~  float32   cell length in angstrom                                                                                                                                                                                 

        44          11          12  Cell Length ~y~  float32                                                                                                                                                                                                           

        48          12          13  Cell Length ~z~  float32                                                                                                                                                                                                           

        52          13          14   Cell Angle α    float32   cell angles in degrees         \2/3.                                                       ignored by IMOD                                                                                             

        56          14          15   Cell Angle β    float32                                                                                                                                                                                                           

        60          15          16   Cell Angle γ    float32                                                                                                                                                                                                           

        64          16          17    Column axis    int32     1 -> X\                                                                                                                                                                                                
                                                               2 -> Y\                                                                                                                                                                                                
                                                               3 -> Z                                                                                                                                                                                                 

        68          17          18     Row axis      int32                                                                                                                                                                                                             

        72          18          19   Section axis    int32                                                                                                                                                                                                             

        76          19          20  Minimum density  float32   statistics calculated\                                                                                                                                                                                  
                                                               from the data                                                                                                                                                                                           

        80          20          21  Maximum density  float32                                                                                                                                                                                                           

        84          21          22   Mean density    float32                                                                                                                                                                                                           
  ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

*...under construction...*
