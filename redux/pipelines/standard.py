import redux.pipeline

from redux.pipes import Read, Power, Mask, Shape, Scale, Format, LPF, Sqrt

class StandardPipeline(redux.pipeline.Pipeline):
	pipeorder = [
		Read,
		Power,
		Mask,
		Shape,
		Sqrt,
		LPF,
		Scale,
		Format,
	]

