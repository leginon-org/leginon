import node
import event

False=0
True=1

class CalibrationTest(node.Node):
	def __init__(self, id, nodelocations):
		node.Node.__init__(self, id, nodelocations)
		self.start()

	def main(self):
		pass

	def defineUserInterface(self):
		nodespec = node.Node.defineUserInterface(self)
		tspec = self.registerUIMethod(self.uiTest, 'Test', ())

		self.registerUISpec('Test', (nodespec, tspec))

	def uiTest(self):
		e = event.ImageShiftPixelShiftEvent(self.ID(), {'row': 1, 'column': 3})
		print "outputting event...",
		self.outputEvent(e)
		print "done"
		return ''
