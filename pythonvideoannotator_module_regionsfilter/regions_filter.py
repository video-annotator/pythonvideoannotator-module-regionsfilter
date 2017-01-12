import sys, os, shutil, re, pyforms, numpy as np, cv2
from pysettings 		 import conf
from pyforms 			 import BaseWidget
from pyforms.Controls 	 import ControlFile
from pyforms.Controls 	 import ControlPlayer
from pyforms.Controls 	 import ControlButton
from pyforms.Controls 	 import ControlNumber
from pyforms.Controls 	 import ControlSlider
from pyforms.Controls 	 import ControlCheckBox
from pyforms.Controls 	 import ControlText
from pyforms.Controls 	 import ControlCheckBoxList
from pyforms.Controls 	 import ControlProgress
from pyforms.Controls 	 import ControlList
from pyforms.Controls 	 import ControlCombo
from pyforms.Controls 	 import ControlEmptyWidget
from PyQt4 import QtGui

from pythonvideoannotator.models.objects.object2d.datasets.path import Path
from geometry_designer.modules.geometry_manual_designer.GeometryManualDesigner import GeometryManualDesigner


class RegionsFilter(BaseWidget):

	def __init__(self, parent=None):
		BaseWidget.__init__(self, 'Regions filter', parent_win=parent)
		self.mainwindow = parent

		self.layout().setContentsMargins(10, 5, 10, 5)
		self.setMinimumHeight(300)
		self.setMinimumWidth(500)

		self._start 		= ControlNumber('Start on frame',0)
		self._end 			= ControlNumber('End on frame', 10)
		self._paths 		= ControlCheckBoxList('Objects')
		self._panel   		= ControlEmptyWidget('Geometry designer')
		self._tracks 		= ControlCombo('Track to save the events')
		self._reloadtracks  = ControlButton('Reload tracks')
		self._apply  		= ControlButton('Apply', checkable=True)
		self._progress  	= ControlProgress('Progress')

		
		self._formset = [
			('_paths',['_start','_end']), 
			'=',
			'_panel',
			('_tracks','_reloadtracks'),
			'_apply',
			'_progress'
		]

		self.load_order = ['_start', '_end', '_panel']

		self._panel.value = self._geodesigner_win = GeometryManualDesigner('Geometry designer', parent=self)
		self._reloadtracks.value = self.__reload_tracks_event

		self._apply.value = self.__apply_btn_event
		self._apply.icon  = conf.ANNOTATOR_ICON_REGIONS

		self._progress.hide()

	def __reload_tracks_event(self):
		self._tracks.clearItems()
		for track in self.mainwindow._time.tracks:
			self._tracks.addItem(str(track.title), track)
	
	def show(self):
		super(RegionsFilter, self).show()
		self.__reload_tracks_event()
	


	def __apply_btn_event(self):

		if self._apply.checked:
			self._start.enabled	= False
			self._end.enabled 	= False
			self._paths.enabled	= False
			self._panel.enabled	= False
			self._apply.label 	= 'Cancel'

			geometries = self._panel.value.geometries

			start = int(self._start.value)
			end   = int(self._end.value)
			self._progress.min = start
			self._progress.max = end * len(geometries) * len(self.paths)
			self._progress.show()

			track_index = self._tracks.value.track_index
			
			count = start
			for poly_name, poly in geometries:
				for path_dataset in self.paths:
					start_event = None
					end_event   = None
					for index in range(start, end+1):				
						pt = path_dataset.get_position(index)
						
						if cv2.pointPolygonTest(poly, pt, False)>=0:
							if start_event==None: start_event = index
							end_event = index
						elif start_event is not None:
							self.add_event_2_timeline(
								track_index, 
								"{1} entered on {0}".format(poly_name, str(path_dataset)), 
								start_event, end_event)
							start_event = None
							end_event   = None
					
						count += 1
						self._progress.value = count

			self._start.enabled	= True
			self._end.enabled 	= True
			self._paths.enabled	= True
			self._panel.enabled	= True
			self._apply.label 	= 'Apply'
			self._progress.hide()

	
	def add_event_2_timeline(self, track, evt_name, begin, end):
		self.mainwindow.add_event_2_timeline(track, evt_name, begin, end)
	

	def add_dataset_event(self, dataset):
		if isinstance(dataset, Path): self._paths += [dataset, True]

	def removed_dataset_event(self, dataset):
		if isinstance(dataset, Path): self._paths -= dataset

	def removed_object_event(self, obj):
		items2remove = []
		for i, (item, checked) in enumerate(self._paths.items):
			if item.object2d==obj: items2remove.append(i)
		for i in sorted(items2remove,reverse=True): self._paths -= i


	###########################################################################
	### PROPERTIES ############################################################
	###########################################################################

	@property
	def video_filename(self): return None
	@video_filename.setter
	def video_filename(self, value): 
		self._panel.value.video_filename = value
		self._start.max 	= self._panel.value.total_n_frames
		self._end.max 		= self._panel.value.total_n_frames
		

	@property
	def paths(self): return self._paths.value
	@paths.setter
	def paths(self, value):  self._paths.value = value




if __name__ == "__main__": pyforms.startApp(RegionsFilter)