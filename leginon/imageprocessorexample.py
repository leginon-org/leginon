import imageprocessor
import os

class FileNames(imageprocessor.ImageProcessor):

	def processImageList(self, imagelist):
		self.logger.info('printing filenames as an example')
		mrc_files = []
		imagepath = self.session['image path']
		for imagedata in imagelist:
			mrc_name = imagedata['filename'] + '.mrc'
			fullname = os.path.join(imagepath, mrc_name)
			mrc_files.append(fullname)

		for mrc_file in mrc_files:
			print mrc_file
