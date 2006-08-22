import math

def equallyAngled(min, max, start, step):
    if step == 0:
        raise ValueError('step size is zero')
    if min > max:
        min, max = max, min
    tilt = start
    tilts = []
    while tilt >= min and tilt <= max:
        tilts.append(tilt)
        tilt += step
    return tilts

def equallySloped(n):
    if n < 2:
        raise ValueError
    m = (2**n)/4
    angles = []
    angles += [math.atan2(-m, i) for i in range(0, m)]
    angles += [math.atan2(i, m) for i in range(-m, 0)]
    angles += [math.atan2(i, m) for i in range(0, m)]
    angles += [math.atan2(m, i) for i in range(m, 0, -1)]
    return angles

class Tilts(object):
    def __init__(self, **kwargs):
        self.update(**kwargs)

    def getTilts(self):
        return [list(tilts) for tilts in self.tilts]

    def update(self, **kwargs):
        attrs = ['min', 'max', 'start', 'step', 'n', 'equally_sloped']
        for attr in attrs:
            if attr not in kwargs:
                continue
            setattr(self, attr, kwargs[attr])

        for attr in attrs:
            if not hasattr(self, attr) or getattr(self, attr) is None:
                self.tilts = []
                return

        self.updateTilts()

    def updateTilts(self):
        self.tilts = []

        if self.equally_sloped:
            if self.start < self.min or self.start > self.max:
                raise ValueError('start angle out of range')
    
            tilts = equallySloped(self.n)
            tilts.sort()
    
            while tilts[0] < self.min:
                if not tilts:
                    raise ValueError('no angles from parameters specified')
                tilts.pop(0)
    
            while tilts[-1] > self.max:
                if not tilts:
                    raise ValueError('no angles from parameters specified')
                tilts.pop(-1)
    
            d = [abs(tilt - self.start) for tilt in tilts]
            index = d.index(min(d))
    
            tilt_half = tilts[index:]
            if len(tilt_half) > 1:
                self.tilts.append(tilt_half)

            if index < len(tilts) - 1:
                index += 1
            tilt_half = tilts[:index]
            tilt_half.reverse()
            if len(tilt_half) > 1:
                self.tilts.append(tilt_half)
        else:
            parameters = [
                (self.min, self.max, self.start, self.step),
                (self.min, self.max, self.start, -self.step),
            ]

            for args in parameters:
                tilts = equallyAngled(*args)
                if len(tilts) < 2:
                    continue
                self.tilts.append(tilts)

            if not self.tilts:
                raise ValueError('no angles from parameters specified')

if __name__ == '__main__':
    kwargs = {
        'equally_sloped': False,
        'min': math.radians(-60),
        'max': math.radians(60),
        'start': math.radians(0),
        'step': math.radians(1),
        'n': 8,
    }
    tilts = Tilts(**kwargs)
    print sum([len(t) for t in tilts.getTilts()])
    print tilts.getTilts()
    tilts.update(equally_sloped=True)
    print sum([len(t) for t in tilts.getTilts()])
    print tilts.getTilts()


