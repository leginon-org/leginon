def getTilts(min, max, start, step):
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

class Tilts(object):
    def __init__(self, min=None, max=None, start=None, step=None):
        if None in (min, max, start, step):
            self.tilts = []
            return
        self.min = min
        self.max = max
        self.start = start
        self.step = step
        self.updateTilts()

    def getTilts(self):
        return list(self.tilts)

    def update(self, **kwargs):
        attrs = [
            'min',
            'max',
            'start',
            'step',
        ]

        for attr in attrs:
            if attr not in kwargs:
                continue
            setattr(self, attr, kwargs[attr])

        self.updateTilts()

    def updateTilts(self):
        self.tilts = []

        parameters = [
            (self.min, self.max, self.start, self.step),
            (self.min, self.max, self.start, -self.step),
        ]

        for args in parameters:
            tilts = getTilts(*args)
            if len(tilts) < 2:
                continue
            self.tilts.append(tilts)

        if not self.tilts:
            raise ValueError('no angles from parameters specified')

if __name__ == '__main__':
    import math
    args = [math.radians(arg) for arg in (-60, 60, 0, 1)]
    tilts = Tilts(*args)
    print tilts.getTilts()

