#!/usr/bin/python

import argparse
import sys
import os
import itertools

import numpy as np
from sklearn.cluster import DBSCAN
from scipy.spatial import distance
from scipy import ndimage
from PIL import Image, ImageDraw
import counter
#from collections import Counter

from appionlib import apImage
from pyami import mrc
#from EMAN2 import *

def main():

    parser = argparse.ArgumentParser(description="Create masks for images")
    parser.add_argument('--ifile',metavar='ifile',type=str,help='Input file to mask')
    parser.add_argument('--ofile',metavar='ofile',type=str,help="Output mask file")
    parser.add_argument('--epsilon',metavar='epsilon',type=int,default='15',help='Epsilon for DBSCAN')
    parser.add_argument('--min_samp',metavar='min_samp',type=int,default='10',help="Minimum samples per cluster")
    parser.add_argument('--perc_threshold',metavar='perc_threshold',type=int,default='99',help='Threshold for initial binary mask')

    parser.add_argument('-first', action='store_true',default=False,help='ignore, for testing')

    args = parser.parse_args()

#    data = Image.open(args.ifile)
    data = ndimage.imread(args.ifile)
    data = np.asarray(data)    
    print data
#    data = mrc.read(args.ifile)
#    data  = apImage.binImg(data,4) 


    data.flags.writeable = True
    '''imgs = EMData.read_images(args.file_base)
    img = imgs[0]

    data = img.get_2dview()'''

    threshold = float(np.percentile(data,args.perc_threshold))
#    threshold = (np.percentile(data,args.perc_threshold))
   
#    data /=threshold 

    inds = np.where(data > 1.0)
    print inds
    inds = np.array(zip(inds[0],inds[1]),dtype=float)

    X = inds

    db = DBSCAN(eps=args.epsilon,min_samples=args.min_samp).fit(X)
    core_samples_mask = np.zeros_like(db.labels_, dtype=bool)
    core_samples_mask[db.core_sample_indices_] = True
    labels = db.labels_

    # Number of clusters in labels, ignoring noise if present.
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)

    #cnts = Counter(labels).most_common(5)
    cnts = counter.Counter(labels).most_common(5)
    
    for (key,junk) in cnts:
        if key == -1:
            continue
        else:
            break

    coords = X[labels==key]
    #coords = np.append(coords,np.array(data.shape).reshape(1,2),0)

    max_x = data.shape[1]
    x_int = max_x/5
    x_res = max_x/20

    max_y = data.shape[0]
    y_int = max_y/5
    y_res = max_y/20

    top_corner_bool = coords[:,1] > max_y-y_int
    bot_corner_bool = coords[:,1] < y_int
    lft_corner_bool = coords[:,0] < x_int
    rht_corner_bool = coords[:,0] > max_x-x_int

    top_bool = coords[:,1] > max_y-y_res
    bot_bool = coords[:,1] < y_res
    lft_bool = coords[:,0] < x_res
    rht_bool = coords[:,0] > max_x-x_res

    top_edge = coords[top_bool,]
    bot_edge = coords[bot_bool,]
    lft_edge = coords[lft_bool,]
    rht_edge = coords[rht_bool,]

    top_rht = np.any(np.logical_and(top_corner_bool, rht_corner_bool))
    bot_rht = np.any(np.logical_and(bot_corner_bool, rht_corner_bool))
    top_lft = np.any(np.logical_and(top_corner_bool, lft_corner_bool))
    bot_lft = np.any(np.logical_and(bot_corner_bool, lft_corner_bool))

    x_int = x_int/2
    y_int = y_int/2

    mask = []
    
    left_curve = None
    right_curve = None
    bot_curve = None
    top_curve = None

        
    if top_rht and top_lft:
        if not bot_curve:

            try:
                bot_curve = [[0,min(lft_edge[:,1])]]
            except ValueError:
                bot_curve = []
            for x in xrange(x_int/2, max_x, x_int):

                lower_bd = x - x_res
                upper_bd = x + x_res

                slice_mask = np.logical_and(coords[:,0] < upper_bd, coords[:,0] > lower_bd)

                curve_slice = coords[slice_mask,1]

                try:
                    y = min(curve_slice[curve_slice > (5*max_y/6)])
                except ValueError:
                    pass
                else:
                    bot_curve.append([x,y])

            try:
                bot_curve.append([max_x,min(rht_edge[:,1])])
            except ValueError:
                pass

            for i in xrange(len(bot_curve) - 1 ):

                first_pt = bot_curve[i]
                secnd_pt = bot_curve[i+1]

                slope = (secnd_pt[1] - first_pt[1]*1.0) / (secnd_pt[0] - first_pt[0])
                
                y_max = first_pt[1]

                for x in range(int(first_pt[0]),int(secnd_pt[0])):
                    mask.extend([[x,y] for y in range(int(y_max),max_y)])
                    y_max += slope



    if top_lft and bot_lft:
        if not right_curve:
            #right_curve = [bot_edge[np.argmax(bot_edge[:,0]),]] # most right of the bottom edge

            try:
                right_curve = [[max(bot_edge[:,0]),0]]
            except ValueError:
                right_curve = []

            for y in xrange(y_int/2, max_y, y_int):
            
                lower_bd = y-y_res
                upper_bd = y+y_res
        
                slice_mask = np.logical_and(coords[:,1] < upper_bd, coords[:,1] > lower_bd)

                curve_slice = coords[slice_mask,0]
        
                try: 
                    x = max(curve_slice[curve_slice < (5*max_x / 6)])
                except ValueError:
                    pass
                else:
                    right_curve.append([x,y])

            try:
                right_curve.append([max(top_edge[:,0]),max_y]) # most right of the top edge
            except ValueError:
                pass

            for i in xrange(len(right_curve)-1):
            
                first_pt = right_curve[i]
                secnd_pt = right_curve[i+1]

                slope = (secnd_pt[0] - first_pt[0])*1.0 / (secnd_pt[1] - first_pt[1])
                
                x_max = first_pt[0]

                for y in range(int(first_pt[1]),int(secnd_pt[1])):
                    mask.extend([[x,y] for x in range(int(x_max))])
                    x_max += slope


    if bot_lft and bot_rht:
        if not top_curve:

            try:
                top_curve = [[0,max(lft_edge[:,1])]]
            except ValueError:
                top_curve = []
        
            for x in xrange(x_int/2,max_x,x_int):

                lower_bd = x-x_res
                upper_bd = x+x_res

                slice_mask = np.logical_and(coords[:,0] < upper_bd, coords[:,0] > lower_bd)

                curve_slice = coords[slice_mask,1]

                try:
                    y = max(curve_slice[curve_slice < (5*max_y/6)])
                except ValueError:
                    pass
                else:
                    top_curve.append([x,y])

            try:
                top_curve.append([max_x,max(rht_edge[:,1])])
            except ValueError:
                pass
    
            for i in xrange(len(top_curve)-1):
            
                first_pt = top_curve[i]
                secnd_pt = top_curve[i+1]

                slope = (secnd_pt[1] - first_pt[1])*1.0 / (secnd_pt[0] - first_pt[0])

                y_max = first_pt[1]

                for x in range(int(first_pt[0]),int(secnd_pt[0])):
                    mask.extend([[x,y] for y in range(int(y_max))])
                    y_max += slope


                    
    if bot_rht and top_rht:
        if not left_curve:

            try:
                left_curve = [[min(bot_edge[:,0]),0]]
            except ValueError:
                left_curve = []

            for y in xrange(y_int/2,max_y,y_int):
            
                lower_bd = y-y_res
                upper_bd = y+y_res

                slice_mask = np.logical_and(coords[:,1] < upper_bd, coords[:,1] > lower_bd)

                curve_slice = coords[slice_mask,0]

                try:
                    x = min(curve_slice[curve_slice > (5*max_x/6)])
                except ValueError:
                    pass
                else:
                    left_curve.append([x,y])

            try:
                left_curve.append([min(top_edge[:,0]),max_y])
            except ValueError:
                pass
        
            for i in xrange(len(left_curve) - 1):
                
                first_pt = left_curve[i]
                secnd_pt = left_curve[i+1]
                
                slope = (secnd_pt[0] - first_pt[0]*1.0) / (secnd_pt[1] - first_pt[1])

                x_max = first_pt[0]

                for y in range(int(first_pt[1]),int(secnd_pt[1])):
                    mask.extend([[x,y] for x in range(int(x_max),max_x)])
                    x_max += slope
        

    
    if top_rht and not top_lft and not bot_rht:
        if not left_curve:

            try:
                left_curve = [[min(bot_edge[:,0]),0]]
            except ValueError:
                left_curve = []

            for y in xrange(y_int/2,max_y,y_int):
            
                lower_bd = y-y_res
                upper_bd = y+y_res

                slice_mask = np.logical_and(coords[:,1] < upper_bd, coords[:,1] > lower_bd)

                curve_slice = coords[slice_mask,0]

                try:
                    x = min(curve_slice[curve_slice > (5*max_x/6)])
                except ValueError:
                    pass
                else:
                    left_curve.append([x,y])

            try:
                left_curve.append([min(top_edge[:,0]),max_y])
            except ValueError:
                pass
        
            for i in xrange(len(left_curve) - 1):
                
                first_pt = left_curve[i]
                secnd_pt = left_curve[i+1]
                
                slope = (secnd_pt[0] - first_pt[0]*1.0) / (secnd_pt[1] - first_pt[1])

                x_max = first_pt[0]

                for y in range(int(first_pt[1]),int(secnd_pt[1])):
                    mask.extend([[x,y] for x in range(int(x_max),max_x)])
                    x_max += slope
                    
        if not bot_curve:
            
            try:
                bot_curve = [[0,min(lft_edge[:,1])]]
            except ValueError:
                bot_curve = []
                
            for x in xrange(x_int/2, max_x, x_int):

                lower_bd = x - x_res
                upper_bd = x + x_res

                slice_mask = np.logical_and(coords[:,0] < upper_bd, coords[:,0] > lower_bd)

                curve_slice = coords[slice_mask,1]

                try:
                    y = min(curve_slice[curve_slice > (5*max_y/6)])
                except ValueError:
                    pass
                else:
                    bot_curve.append([x,y])

            try:
                bot_curve.append([max_x,min(rht_edge[:,1])])
            except ValueError:
                pass

            for i in xrange(len(bot_curve) - 1 ):

                first_pt = bot_curve[i]
                secnd_pt = bot_curve[i+1]

                slope = (secnd_pt[1] - first_pt[1]*1.0) / (secnd_pt[0] - first_pt[0])
                
                y_max = first_pt[1]

                for x in range(int(first_pt[0]),int(secnd_pt[0])):
                    mask.extend([[x,y] for y in range(int(y_max),max_y)])
                    y_max += slope
                
            
    if top_lft and not top_rht and not bot_lft:

        if not bot_curve:

            try:
                bot_curve = [[0,min(lft_edge[:,1])]]
            except ValueError:
                bot_curve = []
            for x in xrange(x_int/2, max_x, x_int):

                lower_bd = x - x_res
                upper_bd = x + x_res

                slice_mask = np.logical_and(coords[:,0] < upper_bd, coords[:,0] > lower_bd)

                curve_slice = coords[slice_mask,1]

                try:
                    y = min(curve_slice[curve_slice > (5*max_y/6)])
                except ValueError:
                    pass
                else:
                    bot_curve.append([x,y])

            try:
                bot_curve.append([max_x,min(rht_edge[:,1])])
            except ValueError:
                pass

            for i in xrange(len(bot_curve) - 1 ):

                first_pt = bot_curve[i]
                secnd_pt = bot_curve[i+1]

                slope = (secnd_pt[1] - first_pt[1]*1.0) / (secnd_pt[0] - first_pt[0])
                
                y_max = first_pt[1]

                for x in range(int(first_pt[0]),int(secnd_pt[0])):
                    mask.extend([[x,y] for y in range(int(y_max),max_y)])
                    y_max += slope

        if not right_curve:
            #right_curve = [bot_edge[np.argmax(bot_edge[:,0]),]] # most right of the bottom edge

            try:
                right_curve = [[max(bot_edge[:,0]),0]]
            except ValueError:
                right_curve = []
            
            for y in xrange(y_int/2, max_y, y_int):
            
                lower_bd = y-y_res
                upper_bd = y+y_res
        
                slice_mask = np.logical_and(coords[:,1] < upper_bd, coords[:,1] > lower_bd)

                curve_slice = coords[slice_mask,0]
        
                try: 
                    x = max(curve_slice[curve_slice < (5*max_x / 6)])
                except ValueError:
                    pass
                else:
                    right_curve.append([x,y])

            try:
                right_curve.append([max(top_edge[:,0]),max_y]) # most right of the top edge
            except ValueError:
                pass

            for i in xrange(len(right_curve)-1):
            
                first_pt = right_curve[i]
                secnd_pt = right_curve[i+1]

                slope = (secnd_pt[0] - first_pt[0])*1.0 / (secnd_pt[1] - first_pt[1])
                
                x_max = first_pt[0]

                for y in range(int(first_pt[1]),int(secnd_pt[1])):
                    mask.extend([[x,y] for x in range(int(x_max))])
                    x_max += slope

    
    if bot_lft and not bot_rht and not top_lft:
        
        if not right_curve:
            #right_curve = [bot_edge[np.argmax(bot_edge[:,0]),]] # most right of the bottom edge
            
            try:
                right_curve = [[max(bot_edge[:,0]),0]]
            except ValueError:
                right_curve = []

            for y in xrange(y_int/2, max_y, y_int):
            
                lower_bd = y-y_res
                upper_bd = y+y_res
        
                slice_mask = np.logical_and(coords[:,1] < upper_bd, coords[:,1] > lower_bd)

                curve_slice = coords[slice_mask,0]
        
                try: 
                    x = max(curve_slice[curve_slice < (5*max_x/6)])
                except ValueError:
                    pass
                else:
                    right_curve.append([x,y])

            try:
                right_curve.append([max(top_edge[:,0]),max_y]) # most right of the top edge
            except ValueError:
                pass

            for i in xrange(len(right_curve)-1):
            
                first_pt = right_curve[i]
                secnd_pt = right_curve[i+1]

                slope = (secnd_pt[0] - first_pt[0])*1.0 / (secnd_pt[1] - first_pt[1])
                
                x_max = first_pt[0]

                for y in range(int(first_pt[1]),int(secnd_pt[1])):
                    mask.extend([[x,y] for x in range(int(x_max))])
                    x_max += slope

        if not top_curve:
            try:
                top_curve = [[0,max(lft_edge[:,1])]]
            except ValueError:
                top_curve = []
        
            for x in xrange(x_int/2,max_x,x_int):

                lower_bd = x-x_res
                upper_bd = x+x_res

                slice_mask = np.logical_and(coords[:,0] < upper_bd, coords[:,0] > lower_bd)

                curve_slice = coords[slice_mask,1]

                try:
                    y = max(curve_slice[curve_slice < (5*max_y/6)])
                except ValueError:
                    pass
                else:
                    top_curve.append([x,y])

            try:
                top_curve.append([max_x,max(rht_edge[:,1])])
            except ValueError:
                pass
    
            for i in xrange(len(top_curve)-1):
            
                first_pt = top_curve[i]
                secnd_pt = top_curve[i+1]

                slope = (secnd_pt[1] - first_pt[1])*1.0 / (secnd_pt[0] - first_pt[0])

                y_max = first_pt[1]

                for x in range(int(first_pt[0]),int(secnd_pt[0])):
                    mask.extend([[x,y] for y in range(int(y_max))])
                    y_max += slope
                

    if bot_rht and not top_rht and not bot_lft:

        if not top_curve:
            try:
                top_curve = [[0,max(lft_edge[:,1])]]
            except ValueError:
                top_curve = []
        
            for x in xrange(x_int/2,max_x,x_int):

                lower_bd = x-x_res
                upper_bd = x+x_res

                slice_mask = np.logical_and(coords[:,0] < upper_bd, coords[:,0] > lower_bd)

                curve_slice = coords[slice_mask,1]

                try:
                    y = max(curve_slice[curve_slice < (5*max_y/6)])
                except ValueError:
                    pass
                else:
                    top_curve.append([x,y])

            try:
                top_curve.append([max_x,max(rht_edge[:,1])])
            except ValueError:
                pass
    
            for i in xrange(len(top_curve)-1):
            
                first_pt = top_curve[i]
                secnd_pt = top_curve[i+1]

                slope = (secnd_pt[1] - first_pt[1])*1.0 / (secnd_pt[0] - first_pt[0])

                y_max = first_pt[1]

                for x in range(int(first_pt[0]),int(secnd_pt[0])):
                    mask.extend([[x,y] for y in range(int(y_max))])
                    y_max += slope

        if not left_curve:
            
            try:
                left_curve = [[min(bot_edge[:,0]),0]]
            except ValueError:
                left_curve = []

            for y in xrange(y_int/2,max_y,y_int):
            
                lower_bd = y-y_res
                upper_bd = y+y_res

                slice_mask = np.logical_and(coords[:,1] < upper_bd, coords[:,1] > lower_bd)

                curve_slice = coords[slice_mask,0]

                try:
                    x = min(curve_slice[curve_slice > (5*max_x/6)])
                except ValueError:
                    pass
                else:
                    left_curve.append([x,y])

            try:
                left_curve.append([min(top_edge[:,0]),max_y])
            except ValueError:
                pass
        
            for i in xrange(len(left_curve) - 1):
                
                first_pt = left_curve[i]
                secnd_pt = left_curve[i+1]
                
                slope = (secnd_pt[0] - first_pt[0]*1.0) / (secnd_pt[1] - first_pt[1])

                x_max = first_pt[0]

                for y in range(int(first_pt[1]),int(secnd_pt[1])):
                    mask.extend([[x,y] for x in range(int(x_max),max_x)])
                    x_max += slope


    mask_array = np.zeros((max_x,max_y),dtype='uint8')
    
    
    x_coords = map(lambda x: x[0],mask)
    y_coords = map(lambda x: x[1],mask)

    mask_array[x_coords,y_coords] = 255

    img = Image.fromarray(mask_array,mode='L')

#    mask_filename = os.path.splitext(os.path.basename(args.e))[0]+'.jpeg'
    
    img.save('%s' % (args.ofile))


    '''print len(mask)

    mrc.write(data,'masked_8_proteasome.mrc')

    data[x_coords,y_coords] = 0.75

    mrc.append(data,'masked_8_proteasome.mrc')
        
    return '''


if __name__ == "__main__":
    main()

