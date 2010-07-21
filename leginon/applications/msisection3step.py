import leginon.leginondata

def make_bindings_from_list(app, binding_list):
	binding_objects = []
	for event_class, from_node, to_node in binding_list:
		binding = leginon.leginondata.BindingSpecData()
		binding['application'] = app
		binding['event class string'] = event_class
		binding['from node alias'] = from_node
		binding['to node alias'] = to_node
		binding_objects.append(binding)
	return binding_objects

def make_nodes_from_list(app, node_list):
	node_objects = []
	for node_class, alias, launcher in node_list:
		nodespec = leginon.leginondata.NodeSpecData()
		nodespec['application'] = app
		nodespec['class string'] = node_class
		nodespec['alias'] = alias
		nodespec['launcher alias'] = launcher
		node_objects.append(nodespec)
	return node_objects

app = leginon.leginondata.ApplicationData()
app['name'] = "msisection3step"

bindings = (
	('ChangePresetEvent', 'Transformer', 'Presets Manager'),
	('TransformTargetDoneEvent', 'Transformer', 'Rough Tissue'),
	('TransformTargetDoneEvent', 'Transformer', 'Final Raster'),
	('ImageTargetListPublishEvent', 'Tilt Rotate', 'Rough Tissue'),
	('MoveToTargetEvent', 'Grid Focus', 'Navigation'),
	('ChangePresetEvent', 'Grid Focus', 'Presets Manager'),
	('TargetListDoneEvent', 'Grid Focus', 'Rough Tissue'),
	('ImageTargetListPublishEvent', 'Grid Targeting', 'Grid'),
	('PresetChangedEvent', 'Presets Manager', 'Transformer'),
	('PresetChangedEvent', 'Presets Manager', 'Grid Focus'),
	('MoveToTargetEvent', 'Presets Manager', 'Navigation'),
	('PresetChangedEvent', 'Presets Manager', 'Navigation'),
	('PresetChangedEvent', 'Presets Manager', 'Grid'),
	('PresetChangedEvent', 'Presets Manager', 'Rough Tissue'),
	('PresetChangedEvent', 'Presets Manager', 'Final Raster'),
	('PresetChangedEvent', 'Presets Manager', 'Section Focus'),
	('MoveToTargetDoneEvent', 'Navigation', 'Grid Focus'),
	('MoveToTargetDoneEvent', 'Navigation', 'Final Raster'),
	('MoveToTargetDoneEvent', 'Navigation', 'Section Focus'),
	('MoveToTargetDoneEvent', 'Navigation', 'Rough Tissue'),
	('MoveToTargetDoneEvent', 'Navigation', 'Grid'),
	('MoveToTargetDoneEvent', 'Navigation', 'Presets Manager'),
	('ChangePresetEvent', 'Navigation', 'Presets Manager'),
	('MoveToTargetEvent', 'Final Raster', 'Navigation'),
	('TargetListDoneEvent', 'Final Raster', 'Final Raster Targeting'),
	('ChangePresetEvent', 'Final Raster', 'Presets Manager'),
	('ImageTargetListPublishEvent', 'Final Raster', 'Section Focus'),
	('TargetListDoneEvent', 'Final Raster', 'Choose Grid'),
	('TransformTargetEvent', 'Final Raster', 'Transformer'),
	('MoveToTargetEvent', 'Section Focus', 'Navigation'),
	('TargetListDoneEvent', 'Section Focus', 'Final Raster'),
	('ChangePresetEvent', 'Section Focus', 'Presets Manager'),
	('QueuePublishEvent', 'Tissue Centering', 'Final Raster Targeting'),
	('ImageTargetListPublishEvent', 'Tissue Centering', 'Final Raster Targeting'),
	('ImageProcessDoneEvent', 'Tissue Centering', 'Rough Tissue'),
	('TargetListDoneEvent', 'Final Raster Targeting', 'Tissue Centering'),
	('ImageTargetListPublishEvent', 'Final Raster Targeting', 'Final Raster'),
	('QueuePublishEvent', 'Final Raster Targeting', 'Final Raster'),
	('TransformTargetEvent', 'Rough Tissue', 'Transformer'),
	('ImageTargetListPublishEvent', 'Rough Tissue', 'Grid Focus'),
	('MoveToTargetEvent', 'Rough Tissue', 'Navigation'),
	('AcquisitionImagePublishEvent', 'Rough Tissue', 'Tissue Centering'),
	('ChangePresetEvent', 'Rough Tissue', 'Presets Manager'),
	('TargetListDoneEvent', 'Rough Tissue', 'Tilt Rotate'),
	('MoveToTargetEvent', 'Grid', 'Navigation'),
	('ChangePresetEvent', 'Grid', 'Presets Manager'),
	('AcquisitionImagePublishEvent', 'Grid', 'Rough Tissue Targeting'),
	('TargetListDoneEvent', 'Grid', 'Rough Tissue Targeting'),
	('ImageTargetListPublishEvent', 'Rough Tissue Targeting', 'Tilt Rotate'),
	('MakeTargetListEvent', 'Choose Grid', 'Grid Targeting'),
)

nodes = (
	('TransformManager', 'Transformer', 'main'),
	('TiltRotateRepeater', 'Tilt Rotate', 'main'),
	('Focuser', 'Grid Focus', 'main'),
	('MosaicTargetMaker', 'Grid Targeting', 'main'),
	('PresetsManager', 'Presets Manager', 'main'),
	('Navigator', 'Navigation', 'main'),
	('Acquisition', 'Final Raster', 'main'),
	('Focuser', 'Section Focus', 'main'),
	('DTFinder', 'Tissue Centering', 'main'),
	('RasterTargetFilter', 'Final Raster Targeting', 'main'),
	('Acquisition', 'Rough Tissue', 'main'),
	('Corrector', 'Correction', 'main'),
	('Acquisition', 'Grid', 'main'),
	('MosaicClickTargetFinder', 'Rough Tissue Targeting', 'main'),
	('GridEntry', 'Choose Grid', 'main'),
	('EM', 'Instrument', 'scope'),
)

bindingspecs = make_bindings_from_list(app, bindings)
nodespecs = make_nodes_from_list(app, nodes)
