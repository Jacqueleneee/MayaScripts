from maya import cmds
import pprint
import controllerLibrary
reload(controllerLibrary)
from Qt import QtWidgets, QtCore, QtGui

# LIBRARY UI CLASS
class ControllerLibraryUI (QtWidgets.QDialog):
	"""
	The ControllerLibraryUI is a dialog that lets us save and import controllers

	"""



	def __init__(self):
		# Arg1 - Find super clas of ControllerLibraryUI (QtWidgets.QDialog)
		# Arg2 - How to reference
		# Then call QDialog's 'init' method
		super(ControllerLibraryUI, self).__init__()

		self.setWindowTitle('Controller Library UI ')
		
		# Create instance of our controller library in out UI
		self.library = controllerLibrary.ControllerLibrary()
		
		# Everytime new instance is created, automatically build UI and populate it
		self.buildUI()
		self.populate()



	def buildUI(self):
		"""
		Build out the UI
		
		Args:
			self (obj): reference itself

		"""
		# MASTER LAYOUT is vertical and apply it to 'self'
		layout = QtWidgets.QVBoxLayout(self)


		# *** SAVE WIDGET  ***
		# Create the sub horizontal layout
		saveWidget = QtWidgets.QWidget()
		saveLayout = QtWidgets.QHBoxLayout(saveWidget)
		layout.addWidget(saveWidget)
		# Name Text Field
		self.saveNameField = QtWidgets.QLineEdit()
		saveLayout.addWidget(self.saveNameField)
		# Save Button
		saveBtn = QtWidgets.QPushButton('Save')
		saveBtn.clicked.connect(self.save)
		saveLayout.addWidget(saveBtn)


		# *** THUMBNAIL LIST WIDGET  ***
		# Make Icons larger & set buffer
		size = 64
		buffer = 12
		# Displays an area where controllers can be displayed
		self.listWidget = QtWidgets.QListWidget()
		# List Widget should display items in icon mode instead
		self.listWidget.setViewMode(QtWidgets.QListWidget.IconMode)
		self.listWidget.setIconSize(QtCore.QSize(size, size))
		# List Widget shoudl readjust content based on window size
		self.listWidget.setResizeMode(QtWidgets.QListWidget.Adjust)
		self.listWidget.setGridSize(QtCore.QSize(size+buffer, size+buffer))
		layout.addWidget(self.listWidget)

		# *** BUTTONS  ***
		# Create sub-horizontal layout for buttons
		btnWidget = QtWidgets.QWidget()
		btnLayout = QtWidgets.QHBoxLayout(btnWidget)
		layout.addWidget(btnWidget)
		# ------- Import Btn
		importBtn = QtWidgets.QPushButton('Import!')
		importBtn.clicked.connect(self.load)
		btnLayout.addWidget(importBtn)
		# -------Refresh Btn
		refreshBtn = QtWidgets.QPushButton('Refresh')
		refreshBtn.clicked.connect(self.populate)
		btnLayout.addWidget(refreshBtn)
		# -------Close Btn
		closeBtn = QtWidgets.QPushButton('Close')
		# close() defined from QDialog
		closeBtn.clicked.connect(self.close)
		btnLayout.addWidget(closeBtn)




	def populate(self):
		"""
		Clears list widget and populates it with controllers
		
		Args:
			self (obj): reference itself

		"""
		self.listWidget.clear()
		self.library.find()


		for name, info in sorted(self.library.items()):
			# Create item text for our list widget 
			item = QtWidgets.QListWidgetItem(name)
			self.listWidget.addItem(item)
			# Attach screenshot to each
			screenshot = info.get('screenshot')
			if screenshot:
				icon = QtGui.QIcon(screenshot)
				item.setIcon(icon)

			item.setToolTip(pprint.pformat(info))


	def load(self):
		"""
		Load all controller that we have selected
		
		Args:
			self (obj): reference itself

		"""
		# Gives us current selected intem in out listWidget
		currentItem = self.listWidget.currentItem()

		if not currentItem:
			return

		name = currentItem.text()
		self.library.load(name)


	def save(self):
		"""
		Save the controller in our scene with given name
		
		Args:
			self (obj): reference itself

		"""
		# Get name to save from text field
		name = self.saveNameField.text()
		# Ensure user enters text before saving
		if not name.strip():
			cmds.warning("You must give a name!")
			return

		# Save the model with its name
		self.library.save(name)
		# Refresh list view
		self.populate()
		# Reset text field
		self.saveNameField.setText('')




def showUI():
	"""
	Displays our UI Window and returns handle to UI
	Returns:
		QDialog

	"""
	ui = ControllerLibraryUI()
	# Display UI
	ui.show()
	return ui