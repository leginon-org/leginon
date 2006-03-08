import math

class Exposure:
    def __init__(self, exposure, cosine_exposure, high_tension, thickness,
                    start_tilt):
        self.exposure = exposure
        self.cosine_exposure = cosine_exposure
        self.high_tension = high_tension
        self.thickness = thickness
        self.start_tilt = start_tilt

    def calculate(self, tilt):
        if self.cosine_exposure:
            return self.calculateCosExposure(tilt)
        else:
            return self.calculateSaxtonExposure(tilt)

    def calculateInitialDose(self, total_dose, tilts):
        if not self.cosine_exposure:
            raise RuntimeError
        initial_dose = total_dose/sum([1.0/math.cos(tilt) for tilt in tilts])
        return initial_dose/math.cos(self.start_tilt)

    def calculateSaxtonExposure(self, tilt):
        cos_alpha = math.cos(tilt)
        mean_path = self.calculateMeanPath()
        thickness = self.thickness/mean_path
        factor = math.exp(thickness*(1.0/cos_alpha - 1))
        exposure = factor*self.exposure
        return fExposure

    def calculateCosExposure(self, tilt):
        cos_alpha = math.cos(tilt)
        cos_start = math.cos(self.start_tilt)
        return self.exposure*cos_start/cos_alpha

    def calculateMeanPath(self):
        kv = self.high_tension/1000.0
        return (350 - 200) / (300.0 - 120.0) * (kv - 120) + 200

if __name__ == '__main__':
    exposure = Exposure(None, True, None, None, None)
    print exposure.calculateInitialDose(200.0, math.pi/90, [math.radians(i) for i in range(-60, 60) + [0]])

