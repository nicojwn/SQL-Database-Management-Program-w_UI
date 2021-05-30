# gui imports
from PyQt5 import QtWidgets, uic, QtCore
from PyQt5.uic import loadUi
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys

import sip

import os

# Database imports
import sqlite3 as lite
from matplotlib import pyplot

class Main(QMainWindow):
	def __init__(self, stack, windowStack):
		super(Main, self).__init__()
		loadUi("Home.ui", self)
		
		self.stack = stack
		self.windowStack = windowStack

		self.connection = None
		self.cursor = None

		self.databaseOpen = False
		self.openDatabase = ""

		self.LocalUiSetup()

	def GetCursor(self):
		return self.cursor
	def GetConnection(self):
		return self.connection

	def LocalUiSetup(self):
		self.ButtonConnect()
		self.ActionConnect()

	"""CONNECT METHODS"""
	def ButtonConnect(self):
		pass
	def ActionConnect(self):
		self.actionOpen_Database.triggered.connect(self.OpenDatabase)
		self.actionCreate_Database.triggered.connect(self.CreateNewDatabase)
		self.actionEdit_Database.triggered.connect(self.LoadEditScreen)
		self.actionView_Open_Database.triggered.connect(self.LoadViewScreen)
		self.actionCommit.triggered.connect(self.Commit)
		self.actionClose.triggered.connect(self.Close)
		self.actionCurrent_Open.triggered.connect(lambda : self.DisplayMessageBox("{} is currently open.".format(self.CurrentlyOpen()), "Info", QMessageBox.Information, QMessageBox.Close))

	def CreateNewDatabase(self):

		fileFilter = "Data File (*.db)"
		response = QFileDialog.getSaveFileName(

			parent = self,
			caption = "Select Data File",
			directory = "newDatabase.db",
			filter = fileFilter,
			initialFilter = "Data File (*.db)"

		)

		if response[0] == "":
			self.DisplayMessageBox("No database has been created.", "Warning", QMessageBox.Warning)
			return
		with open(response[0], "w") as w:
			pass

	def OpenDatabase(self):

		fileFilter = "Data File (*.db)"
		response = QFileDialog.getOpenFileName(

			parent = self,
			caption = "Select Data File",
			directory = os.getcwd(),
			filter = fileFilter,
			initialFilter = "Data File (*.db)"

		)

		if response[0] == "":
			self.DisplayMessageBox("No database selected.", "Warning", QMessageBox.Warning)
			return

		try:
			self.connection = lite.connect(response[0])
			self.cursor = self.connection.cursor()
		except Exception:
			self.DisplayMessageBox("Something went wrong while opening the database.", "Error", QMessageBox.Critical, QMessageBox.Close)
			return
		self.openDatabase = response[0].split("/")[-1]
		self.databaseOpen = True

	"""LOAD OTHER SCREENS"""
	def LoadEditScreen(self):
		if not self.databaseOpen:
			self.DisplayMessageBox("No database has been opened. Open a database to edit it.", "Error", QMessageBox.Critical)
			return
		self.stack.setCurrentIndex(self.windowStack.index("edit"))
	def LoadViewScreen(self):
		if not self.databaseOpen:
			self.DisplayMessageBox("No database has been opened. Open a database to view it.", "Error", QMessageBox.Critical)
			return
		self.stack.setCurrentIndex(self.windowStack.index("view"))

	def Commit(self):

		if not self.databaseOpen:
			self.DisplayMessageBox("No open database to commit to. Open a database first.", "Error", QMessageBox.Critical)
			return

		try:
			self.connection.commit()
		except:
			self.DisplayMessageBox("Something went wrong while commiting to the database.", "Error", QMessageBox.Critical, QMessageBox.Close)
			return -1

		self.DisplayMessageBox("Successfully commited to the database.", "Yay!", QMessageBox.Information, QMessageBox.Close)
	def Close(self):

		if not self.databaseOpen:
			self.DisplayMessageBox("No open database to close. Open a database first.", "Error", QMessageBox.Critical)
			return

		try:
			self.connection.close()
		except Exception:
			self.DisplayMessageBox("Something went wrong while closing the database.", "Error", QMessageBox.Critical, QMessageBox.Close)
			return
		
		self.DisplayMessageBox("Connection successfully closed.", "Info", QMessageBox.Information)

		self.databaseOpen = False
		self.openDatabase = ""

	def CurrentlyOpen(self):
		if self.databaseOpen:
			return self.openDatabase.split(".")[0]
		else:
			return "No database"

	def GetCursor(self):
		return self.connection.cursor()

	def DisplayMessageBox(self, message, title, icon=QMessageBox.NoIcon, button=QMessageBox.Ok):
		msg = QMessageBox()
		msg.setText(message)
		msg.setWindowTitle(title)
		msg.setIcon(icon)
		msg.setDefaultButton(button)
		msg.exec_()

class Edit(QMainWindow):
	def __init__(self, stack, windowStack, main):

		super(Edit, self).__init__()
		loadUi("Edit.ui", self)

		self.main=main

		self.stack = stack
		self.windowStack = windowStack

		self.toExecute = []

		self.localToSQL = {}

		self.font = QFont("Arial", 20)

		self.commited = False

		self.addTableUI = []
		self.addEntityUI = []
		self.addAttributeUI = []
		self.removeTableUI = []
		self.removeEntityUI = []
		self.removeAttributeUI = []

		self.dataTypes = ["CHAR", "VARCHAR", "TEXT", "TINYTEXT", "INT"]
		self.inputs = [QLineEdit, QLineEdit, QLineEdit, QLineEdit, QSpinBox]
		self.dataTypesQ = {"CHAR":(1,255), "VARCHAR":(1,65535), "TEXT":(1,65535), "INT":(1,2147483647)} # Requiring Quantity
		self.constraints = ["", "NOT NULL", "UNIQUE", "PRIMARY KEY"]

		self.LocalUiSetup()

	def LocalUiSetup(self):
		self.ButtonConnect()
		self.ActionConnection()
		# self.GenerateUIPresets()

	"""CONNECT METHODS"""
	def ButtonConnect(self):
		self.executeButton.clicked.connect(self.Execute)
	def ActionConnection(self):
		# File
		self.actionHome.triggered.connect(self.Home)
		self.actionCommit.triggered.connect(self.Commit)

		# Actions
		self.actionCreate_Table.triggered.connect(self.AddTableUI)
		self.actionAdd_Entity.triggered.connect(self.AddEntityUI)
		self.actionAdd_Attribute.triggered.connect(self.AddAttributeUI)
		self.actionRemove_Table.triggered.connect(self.RemoveTableUI)
		self.actionRemove_Entity.triggered.connect(self.RemoveEntityUI)
		self.actionRemove_Attribute.triggered.connect(self.RemoveAttributeUI)
	def Home(self):
		self.stack.setCurrentIndex(self.windowStack.index("home"))
	def Commit(self):

		commit = QMessageBox.warning(self, "Warning", "Once you commit any not yet executed commands will be lost.", QMessageBox.Ok|QMessageBox.Abort)
		if commit == QMessageBox.Abort:
			return

		x = self.main.Commit()
		if x == -1:
			self.commited = False
			return
		self.commited = True
		self.toExecute = []

	"""EDIT UI METHODS"""
	def GenerateAddTableUI(self):

		attrs = []

		dataTypes = self.dataTypes
		dataTypesQ = self.dataTypesQ
		constraints = self.constraints

		tableNameLineEdit = self.LineEdit("Table Name", self.font)
		attrNameLineEdit = self.LineEdit("Attribute Name", self.font)

		dataTypeComboBox = self.ComboBox(dataTypes, self.font)
		constraintComboBox = self.ComboBox(
					constraints, 
					self.font
					)
		
		quantitySpinBox = self.SpinBox(self.font, minimum = self.dataTypesQ[dataTypeComboBox.currentText()][0], maximum = self.dataTypesQ[dataTypeComboBox.currentText()][1])

		dataTypeComboBox.currentTextChanged.connect(
						lambda: 
							(
								hbox_2.removeWidget(quantitySpinBox), 
								quantitySpinBox.setParent(None)
							) 
							if self.UpdateOnSpinBoxChange(hbox_2, quantitySpinBox, dataTypeComboBox.currentText() in dataTypesQ.keys()) 
							else 
							(
								hbox_2.addWidget(quantitySpinBox),
								quantitySpinBox.setMaximum(dataTypesQ[dataTypeComboBox.currentText()][1]),
								quantitySpinBox.setMinimum(dataTypesQ[dataTypeComboBox.currentText()][0])
							)
						)

		addAttrPushButton = self.PushButton(
						lambda: 
							attrs.append(
								(
									attrNameLineEdit.text(), 
									dataTypeComboBox.currentText() 
									if not dataTypeComboBox.currentText() in dataTypesQ.keys() 
									else 
									"{0}({1})".format(dataTypeComboBox.currentText(), quantitySpinBox.value()), 
									constraintComboBox.currentText()
								)
							)
							if not attrNameLineEdit.text() == "" and not attrNameLineEdit.text() in [i[0] for i in attrs]
							else self.DisplayMessageBox("Please give the attribute a unique name", "Error", QMessageBox.Critical),
						"Add Attribute",
						self.font
						)
		createTablePushButton = self.PushButton(
							lambda: 
								(
									self.AddTableCMD(tableNameLineEdit.text(), attrs),
									attrs.clear()
								)
								if self.CheckName(tableNameLineEdit.text())
								else self.DisplayMessageBox("Please give the table a unique name", "Error", QMessageBox.Critical), 
							"Create Table", 
							self.font
						)
		showUsedNamesPushButton = self.PushButton(lambda : self.ShowTableNames(), "Used Table Names", self.font)

		vbox_1 = self.Layout(QVBoxLayout(), [tableNameLineEdit, createTablePushButton, showUsedNamesPushButton, "s"])
		hbox_2 = self.Layout(QHBoxLayout(), [dataTypeComboBox, quantitySpinBox])
		vbox_2 = self.Layout(QVBoxLayout(), [attrNameLineEdit, hbox_2, constraintComboBox, addAttrPushButton, "s"])

		self.addTableUI = [
							hbox_2, 
							vbox_1, 
							vbox_2, 
							tableNameLineEdit, 
							attrNameLineEdit, 
							quantitySpinBox, 
							dataTypeComboBox, 
							constraintComboBox, 
							addAttrPushButton, 
							createTablePushButton
						  ]
	def GenerateAddEntityUI(self):
		
		tables = self.GetTableNames().split(", ")

		typeToInput = {i:j for i,j in zip(self.dataTypes, self.inputs)}

		chooseAttrsComboBox = self.ComboBox(self.GetAttributes(tables[0]), self.font)
		chooseTableComboBox = self.ComboBox(tables, self.font)

		attrTypeLabel = self.Label(self.GetAttributes(chooseTableComboBox.currentText())[chooseAttrsComboBox.currentText()], self.font)

		chooseTableComboBox.currentTextChanged.connect(lambda : self.UpdateAttrAndLabel(chooseAttrsComboBox, attrTypeLabel, chooseTableComboBox))
		chooseAttrsComboBox.currentIndexChanged.connect(lambda : self.UpdateAttrTypeLabel(attrTypeLabel, chooseTableComboBox, chooseAttrsComboBox))

		hbox_1 = self.Layout(QHBoxLayout(), [attrTypeLabel, chooseAttrsComboBox])
		vbox_1 = self.Layout(QVBoxLayout(), [hbox_1, chooseTableComboBox])

		chooseAttrsComboBox.currentIndexChanged.connect(lambda : self.UpdateAttrInput(chooseAttrsComboBox, hbox_1, typeToInput))

		# Store each value in a dictionary with the key being the attribute name

		self.addEntityUI = [vbox_1, chooseAttrsComboBox, chooseTableComboBox]
	def GenerateAddAttributeUI(self):
		pass
	def GenerateRemoveTableUI(self):
		pass
	def GenerateRemoveEntityUI(self):
		pass
	def GenerateRemoveAttributeUI(self):
		pass

	def AddTableUI(self):
		self.ClearLayout(self.horizontalLayout_2)
		self.GenerateAddTableUI()
		self.horizontalLayout_2 = self.Layout(self.horizontalLayout_2, ["s", self.addTableUI[1], self.addTableUI[2], "s"])
	def AddEntityUI(self):
		self.ClearLayout(self.horizontalLayout_2)
		self.GenerateAddEntityUI()
		self.horizontalLayout_2 = self.Layout(self.horizontalLayout_2, ["s", self.addEntityUI[0],"s"])
	def AddAttributeUI(self):
		hbox_1 = self.horizontalLayout_2
		self.ClearLayout(hbox_1)
		self.GenerateAddAttributeUI()
	def RemoveTableUI(self):
		hbox_1 = self.horizontalLayout_2
		self.ClearLayout(hbox_1)
		self.GenerateRemoveTableUI()
	def RemoveEntityUI(self):
		hbox_1 = self.horizontalLayout_2
		self.ClearLayout(hbox_1)
		self.GenerateRemoveTableUI()
	def RemoveAttributeUI(self):
		hbox_1 = self.horizontalLayout_2
		self.ClearLayout(hbox_1)
		self.GenerateRemoveTableUI()

	"""Add Table Functions"""
	def IterateThroughLayout(self, layout):
		children = []
		for i in range(layout.count()):
			children.append(layout.itemAt(i).widget())
		return children
	def UpdateOnSpinBoxChange(self, layout, widget, condition):
		if not condition and widget in self.IterateThroughLayout(layout):
			return True
		elif condition and not widget in self.IterateThroughLayout(layout):
			return False
	def CheckName(self, name):
		if name == "" or self.CheckTableExist(name) == False:
			return False
		return True
	def CheckTableExist(self, name):
		self.main.cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table';")
		names = [i[0].lower() for i in self.main.cursor.fetchall()]
		if name.lower() in names:
			return False
		return True
	def ShowTableNames(self):
		self.DisplayMessageBox(lambda : self.GetTableNames(), "Used Table Names", QMessageBox.Information)

	"""Add Attribute Functions"""
	def GetAttributes(self, table):
		command = "PRAGMA TABLE_INFO({});".format(table)
		self.main.cursor.execute(command)
		print(self.main.cursor.fetchall())
		attributes = {i[1] : i[2] for i in self.main.cursor.fetchall()}
		return attributes
	def ReplaceComboBox(self, comboBox, newContents):
		prevCount = comboBox.count()
		comboBox.addItems(newContents)
		for i in range(prevCount):
			comboBox.removeItem(0)
	def UpdateAttrAndLabel(self, attrComboBox, attrTypeLabel, tableComboBox):
		self.ReplaceComboBox(attrComboBox, self.GetAttributes(tableComboBox.currentText()))
		attrTypeLabel.setText(self.GetAttributes(tableComboBox.currentText())[attrComboBox.currentText()])
	def UpdateAttrTypeLabel(self, attrTypeLabel, tableComboBox, attrComboBox):
		try:
			attrTypeLabel.setText(self.GetAttributes(tableComboBox.currentText())[attrComboBox.currentText()])
		except Exception:
			pass
	def UpdateAttrInput(self, attrsComboBox, hbox_1, typeToInput):
		newInput = typeToInput[attrsComboBox.currentText()]()
		if type(newInput) == QLineEdit:
			newInput.setMaxLength()
		elif type(newInput) == QSpinBox:
			newInput.setMaximum()
			newInput.setMinimum()
		hbox_1.replaceWidget(hbox_1.itemAt(-1), newInput)

	def GetTableNames(self):
		tableNames = ""
		self.main.cursor.execute("SELECT name FROM sqlite_master WHERE type = 'table';")
		names = [i[0] for i in self.main.cursor.fetchall()]
		for i in names:
			tableNames += str(i) + ", "
		tableNames = tableNames[:-2]
		return tableNames


	def ClearLayout(self, currentLayout):
		if currentLayout is not None:
			while currentLayout.count():
				item = currentLayout.takeAt(0)
				widget = item.widget()
				if widget is not None:
					widget.deleteLater()
				else:
					self.ClearLayout(item.layout())
	def ComboBox(self, items=None, font=None, connection=None):
		comboBox = QComboBox()
		if not font == None:
			comboBox.setFont(font)
		if not items == None:
			comboBox.addItems(items)
		if not connection == None:
			comboBox.currentIndexChanged.connect(connection)
		return comboBox
	def SpinBox(self, font=None, minimum=None, maximum=None):
		spinBox = QSpinBox()
		if not font == None:
			spinBox.setFont(font)
		if not minimum == None:
			spinBox.setMinimum(minimum)
		if not maximum == None:
			spinBox.setMaximum(maximum)
		return spinBox
	def LineEdit(self, placeHolderText=None, font=None):
		lineEdit = QLineEdit()
		if not placeHolderText == None:
			lineEdit.setPlaceholderText(placeHolderText)
		if not font == None:
			lineEdit.setFont(font)
		return lineEdit
	def PushButton(self, connection=None, text=None, font=None):
		pushButton = QPushButton()
		if not connection == None:
			pushButton.clicked.connect(connection)
		if not text == None:
			pushButton.setText(text)
		if not font == None:
			pushButton.setFont(font)
		return pushButton
	def Label(self, text, font=None):
		label = QLabel()
		label.setText(text)
		if not font == None:
			label.setFont(font)
		return label
	def Layout(self, lType, widgets):
		layoutTypes = [QHBoxLayout, QVBoxLayout, QGridLayout]
		layout = lType
		for i in widgets:
			if type(i) is tuple:
				if i[0] == "s":
					layout.addStretch(i[1])
			elif i == "s":
				layout.addStretch()
			elif i.isWidgetType():
				layout.addWidget(i)
			elif type(i) in layoutTypes:
				layout.addLayout(i)
		return layout
	"""EDIT CMD METHODS"""
	def AddTableCMD(self, tableName, attrs=[]):
		# CREATE TABLE table_name
		command = "CREATE TABLE {} ".format(tableName)
		if attrs == []:
			# CREATE TABLE table_name (id INT PRIMARY KEY);
			command += "(id INT PRIMARY KEY);"
		else:
			# CREATE TABLE table_name (
			command += "("
			# CREATE TABLE table_name (attribute_name data_type constraint,attribute_name data_type constraint,...,
			for i in attrs:
				command += "{0} {1} {2},".format(i[0],i[1],i[2])
			# CREATE TABLE table_name (attribute_name data_type constraint,attribute_name data_type constraint,...
			command = command[:-1]
			# CREATE TABLE table_name (attribute_name data_type constraint,attribute_name data_type constraint,...);
			command += ");"
		self.toExecute.append(command)
		print(self.toExecute)
	def AddEntityCMD(self, table, attrs):
		# INSERT INTO table_name
		command = "INSERT INTO {}".format(table)
		# INSERT INTO table_name(
		tempCommand = "("
		# INSERT INTO table_name(attribute1, attribute2,...,
		for i in list(attrs.keys()):
			tempCommand += "{},".format(i)
		# INSERT INTO table_name(attribute1, attribute2,...
		tempCommand = tempCommand[:-1]
		# INSERT INTO table_name(attribute1, attribute2,...) VALUES
		tempCommand += ") VALUES"
		# INSERT INTO table_name(attribute1, attribute2,...) VALUES(
		tempCommand = "("
		# INSERT INTO table_name(attribute1, attribute2,...) VALUES(value1,value2,...,
		for i in list(attrs.values()):
			tempCommand += "{},".format(i)
		# INSERT INTO table_name(attribute1, attribute2,...) VALUES(value1,value2,...
		tempCommand = tempCommand[:-1]
		# INSERT INTO table_name(attribute1, attribute2,...) VALUES(value1,value2,...);
		tempCommand += ");"

		command += tempCommand
		self.toExecute.append(command)
	def AddAttributeCMD(self, table, attributeName):
		command = "ALTER TABLE {0} ADD {1};".format(table, attributeName)
		self.toExecute.append(command)
	def RemoveTableCMD(self, tableName):
		command = "DROP TABLE {};".format(tableName)
		self.toExecute.append(command)
	def RemoveEntityCMD(self, table, conditions):
		# DELETE FROM table_name 
		command = "DELETE FROM {} ".format(table)
		# DELETE FROM table_name WHERE condition1 AND condition2 AND ... AND 
		for i in conditions:
			command += "WHERE {0}={1} AND ".format(i[0],i[1])
		# DELETE FROM table_name WHERE condition1 AND condition2 AND ...
		command = command[:-5]
		# DELETE FROM table_name WHERE condition1 AND condition2 AND ...;
		command += ";"
		self.toExecute.append(command)
	def RemoveAttributeCMD(self, table, attributeName):
		command = "ALTER TABLE {0} DROP COLUMN {1}".format(table, attributeName)
		self.toExecute.append(command)

	def Execute(self):
		nOS = 0 # Number of Successfully executed commands
		for i in self.toExecute:
			try:
				if type(i) is tuple:
					self.main.cursor.execute(i[0],i[1])
				else:
					self.main.cursor.execute(i)
				nOS += 1
			except Exception as e:
				print(e)

		if len(self.toExecute) == 0:
			self.DisplayMessageBox("There were no commands to execute.", "??", QMessageBox.Information)
		elif nOS == len(self.toExecute):
			self.DisplayMessageBox("All of the {} commands were successfully executed.".format(len(self.toExecute)), "Yay!", QMessageBox.Information)
		elif nOS == 0:
			self.DisplayMessageBox("None of the {} commands were successfully executed.".format(len(self.toExecute)), "Warning", QMessageBox.Warning)
		else:
			self.DisplayMessageBox("{0} of the {1} commands were successfully executed.".format(nOS, len(self.toExecute)), "Partial Yay", QMessageBox.Information)

		self.toExecute = []
		self.commited = False

	def DisplayMessageBox(self, message, title, icon=QMessageBox.NoIcon, button=QMessageBox.Ok):
		msg = QMessageBox()
		msg.setText(message)
		msg.setWindowTitle(title)
		msg.setIcon(icon)
		msg.setDefaultButton(button)
		msg.exec_()

class View(QMainWindow):
	def __init__(self, stack, windowStack, main):
		super(View, self).__init__()
		loadUi("View.ui", self)

		self.stack = stack
		self.windowStack = windowStack

		self.main=main

		self.LocalUiSetup()

	def LocalUiSetup(self):
		self.ActionConnect()

	"""CONNECT METHODS"""
	def ActionConnect(self):
		self.actionHome.triggered.connect(self.Home)

	def Home(self):
		self.stack.setCurrentIndex(self.windowStack.index("home"))

	def DisplayMessageBox(self, message, title, icon=QMessageBox.NoIcon, button=QMessageBox.Ok):
		msg = QMessageBox()
		msg.setText(message)
		msg.setWindowTitle(title)
		msg.setIcon(icon)
		msg.setDefaultButton(button)
		msg.exec_()


def window():

	windowStack = ("home","edit","view")

	app = QApplication(sys.argv)
	stack = QtWidgets.QStackedWidget()

	main = Main(stack, windowStack)
	edit = Edit(stack, windowStack, main)
	view = View(stack, windowStack, main)

	stack.addWidget(main)
	stack.addWidget(edit)
	stack.addWidget(view)
	stack.show()

	sys.exit(app.exec_())

if __name__ == "__main__":
	window()





class Template(QMainWindow):
	def __init__(self, stack, windowStack, main):
		super(Template, self).__init__()
		loadUi("*****.ui", self)

		self.stack = stack
		self.windowStack = windowStack

		self.main = main

		self.font = QFont()

		self.LocalUiSetup()

	def LocalUiSetup(self):
		pass

	def Home(self):
		self.stack.setCurrentIndex(self.windowStack.index("Home"))

	def DisplayMessageBox(self, message, title, icon=QMessageBox.NoIcon, button=QMessageBox.Ok):
		msg = QMessageBox()
		msg.setText(message)
		msg.setWindowTitle(title)
		msg.setIcon(icon)
		msg.setDefaultButton(button)
		msg.exec_()
	def ClearLayout(self, currentLayout):
		if currentLayout is not None:
			while currentLayout.count():
				item = currentLayout.takeAt(0)
				widget = item.widget()
				if widget is not None:
					widget.deleteLater()
				else:
					self.ClearLayout(item.layout())
	def ComboBox(self, items=None, font=None, connection=None):
		comboBox = QComboBox()
		if not font == None:
			comboBox.setFont(font)
		if not items == None:
			comboBox.addItems(items)
		if not connection == None:
			comboBox.currentIndexChanged.connect(connection)
		return comboBox
	def SpinBox(self, font=None, minimum=None, maximum=None):
		spinBox = QSpinBox()
		if not font == None:
			spinBox.setFont(font)
		if not minimum == None:
			spinBox.setMinimum(minimum)
		if not maximum == None:
			spinBox.setMaximum(maximum)
		return spinBox
	def LineEdit(self, placeHolderText=None, font=None):
		lineEdit = QLineEdit()
		if not placeHolderText == None:
			lineEdit.setPlaceholderText(placeHolderText)
		if not font == None:
			lineEdit.setFont(font)
		return lineEdit
	def PushButton(self, connection=None, text=None, font=None):
		pushButton = QPushButton()
		if not connection == None:
			pushButton.clicked.connect(connection)
		if not text == None:
			pushButton.setText(text)
		if not font == None:
			pushButton.setFont(font)
		return pushButton
	def Layout(self, lType, widgets):
		layoutTypes = [QHBoxLayout, QVBoxLayout, QGridLayout]
		layout = lType
		for i in widgets:
			if type(i) is tuple:
				if i[0] == "s":
					layout.addStretch(i[1])
			elif i == "s":
				layout.addStretch()
			elif i.isWidgetType():
				layout.addWidget(i)
			elif type(i) in layoutTypes:
				layout.addLayout(i)
		return layout

