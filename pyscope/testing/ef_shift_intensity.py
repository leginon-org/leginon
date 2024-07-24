import sys, os, time
from pyami import mrc
from pyscope import feicam
c = feicam.Falcon4ECef()
#from pyscope import simccdcamera2
#c = simccdcamera2.SimCCDCamera()
slit_width = c.getEnergyFilterWidth()
print('current ef slit width', slit_width)
ef_offset = c.getEnergyFilterOffset()
print('current ef energy offset', ef_offset)
my_begin = int(ef_offset)
offset_begin, offset_end = c.getEnergyShiftRange()
print('energy offset range: %.1f -> %.1f' % (float(offset_begin), float(offset_end)))
sleep_time = int(input('wait time after offset in seconds: '))

if my_begin < offset_begin or my_begin > offset_end:
    print('Error: starting offset out of range')
    sys.exit()

answer=input('What is the slit width you want to use? (int) ')
try:
    my_width = int(answer)
    c.setEnergyFilterWidth(my_width)
except:
    print('Error: Bad width, width not set')
    p = input('return to quit.')
    sys.exit()

try:
    print('What is the energy offset you want to scan ? (int) (min:%d max:%d ev)' % (int(offset_begin),int(offset_end)))
    print('if your start value is higher than the end, the scan will be in negative direction.')
    answer=input('Start from in ev (int)')
    my_begin = int(answer)
    answer=input('End at in ev (int) ')
    my_end=int(answer)
except:
    print('Error: Bad input, range not set')
    p = input('return to quit.')
    sys.exit()

try:
    answer=input('What is the energy step you want to scan (int) ')
    my_step=int(answer)
    if not my_step:
        my_step=slit_width
    if my_begin > my_end:
        my_step=-1*abs(my_step)
    else:
        my_step=abs(my_step)
    answer=input('Exposure time in ms ')
    exposure_time = int(answer)
    c.setExposureTime(exposure_time)
    filedir=input('Directory to save the result txt file:')
    if not os.path.isdir(filedir):
        raise ValueError('Invalid directory: %s' % filedir)
except Excepttion as e:
    print('Error: %s' % (e))
    sys.exit()
# start collection
n = 1
while True:
    filename = 'width_%02d_step_%02d_position_%02d.txt' % (my_width,my_step,n)
    filepath = os.path.join(filedir, filename)
    print('---saving to %s' %filepath)
    print('---saving as offset\tmean\tstd')
    offset = my_begin
    f = open(filepath,'w')
    notes = input('short one line note= ')
    f.write(notes+'\n')
    m=1
    while offset_begin < offset < offset_end:
        array = c.getImage()
        line = '%.1f\t%.2f\t%.2f' % (offset,array.mean(),array.std())
        print(line)
        image_filepath='%s_%03d.mrc' % ('.'.join(filepath.split('.')[:-1]),m)
        mrc.write(array,image_filepath)
        f.write(line+'\n')
        c.setEnergyFilterOffset(offset)
        offset += my_step
        m += 1
        if my_step > 0:
            # positive step
            if offset > my_end:
                break
        else:
            # negative step
            if offset < my_end:
                break
        time.sleep(sleep_time)
    f.close()
    n += 1
    c.setEnergyFilterOffset(my_begin)
    time.sleep(sleep_time)
    answer=input('Enter "n" when ready for the next position.\n Anything else to exit.')
    if answer != 'n':
        break
print('setting slit width and offset back...')
c.setEnergyFilterWidth(slit_width)
c.setEnergyFilterOffset(ef_offset)
