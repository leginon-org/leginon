import redux.pipeline

from redux.pipes import Read, Power, Mask, Shape, Scale, Format

class StandardPipeline(redux.pipeline.Pipeline):
	pipeorder = [
		Read,
		Power,
		Mask,
		Shape,
		Scale,
		Format,
	]

