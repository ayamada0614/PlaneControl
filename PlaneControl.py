import os
import unittest
import os.path
import platform
from __main__ import vtk, qt, ctk, slicer

#
# PlaneControl
#
class PlaneControl:
  def __init__(self, parent):
    parent.title = "PlaneControl" # TODO make this more human readable by adding spaces
    parent.categories = ["IGT"]
    parent.dependencies = []
    parent.contributors = ["Atsushi Yamada (Shiga University of Medical Science)"]
    parent.helpText = """
    This module...The details are in <a href=http://www.slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/PlaneControl>the online documentation</a>.
    """
    parent.acknowledgementText = """
    This work was partially funded by Biomedical Innovation Center at Shiga University of Medical Science in Japan.
    """ 
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['PlaneControl'] = self.runTest

  def runTest(self):
    tester = PlaneControlTest()
    tester.runTest()

#
# qPlaneControlWidget
#
class ModuleListProperty:
  module = ''
  label = ''
  number = ''

class ModuleButtonProperty:
  module = ''
  label = ''
  handler = None
  button = None

class PlaneControlWidget:

  def __init__(self, parent = None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()

  def setup(self):
    # if this import is at top of the source, the loading could not work well.
    #import glob 
    # Instantiate and connect widgets ...

    #
    # Reload and Test area
    #
    reloadCollapsibleButton = ctk.ctkCollapsibleButton()
    reloadCollapsibleButton.text = "Reload && Test"
    reloadCollapsibleButton.collapsed = True
    #self.layout.addWidget(reloadCollapsibleButton)
    ##reloadFormLayout = qt.QFormLayout(reloadCollapsibleButton)

    # reload button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadButton = qt.QPushButton("Reload")
    self.reloadButton.toolTip = "Reload this module."
    self.reloadButton.name = "PlaneControl Reload"
    #reloadFormLayout.addWidget(self.reloadButton)
    ##self.reloadButton.connect('clicked()', self.onReload)

    # reload and test button
    # (use this during development, but remove it when delivering
    #  your module to users)
    self.reloadAndTestButton = qt.QPushButton("Reload and Test")
    self.reloadAndTestButton.toolTip = "Reload this module and then run the self tests."
    #reloadFormLayout.addWidget(self.reloadAndTestButton)
    ##self.reloadAndTestButton.connect('clicked()', self.onReloadAndTest)

    #
    # Parameters Area
    #
    self.configurationCollapsibleButton = ctk.ctkCollapsibleButton()
    self.configurationCollapsibleButton.text = "Setup"
    self.configurationCollapsibleButton.collapsed = False
    self.configurationList = self.configurationCollapsibleButton
    self.layout.addWidget(self.configurationCollapsibleButton)
    # Layout within the collapsible button
    self.configurationFormLayout = qt.QFormLayout(self.configurationCollapsibleButton)

    #
    # Sensor Transform (vtkMRMLLinearTransformNode)
    #
    self.sensorTransformSelector = slicer.qMRMLNodeComboBox()
    self.sensorTransformSelector.nodeTypes = ( ("vtkMRMLLinearTransformNode"), "" )
    self.sensorTransformSelector.noneEnabled = True
    self.sensorTransformSelector.setMRMLScene( slicer.mrmlScene )
    self.configurationFormLayout.addRow("Sensor Matrix: ", self.sensorTransformSelector)

    #
    # PLANE_0 Transform (vtkMRMLLinearTransformNode)
    #
    self.plane_0TransformSelector = slicer.qMRMLNodeComboBox()
    self.plane_0TransformSelector.nodeTypes = ( ("vtkMRMLLinearTransformNode"), "" )
    self.plane_0TransformSelector.noneEnabled = True
    self.plane_0TransformSelector.setMRMLScene( slicer.mrmlScene )
    self.configurationFormLayout.addRow("PLANE_0 Matrix: ", self.plane_0TransformSelector)

    #
    # PLANE_1 Transform (vtkMRMLLinearTransformNode)
    #
    self.plane_1TransformSelector = slicer.qMRMLNodeComboBox()
    self.plane_1TransformSelector.nodeTypes = ( ("vtkMRMLLinearTransformNode"), "" )
    self.plane_1TransformSelector.noneEnabled = True
    self.plane_1TransformSelector.setMRMLScene( slicer.mrmlScene )
    self.configurationFormLayout.addRow("PLANE_1 Matrix: ", self.plane_1TransformSelector)

    #
    # PLANE_2 Transform (vtkMRMLLinearTransformNode)
    #
    self.plane_2TransformSelector = slicer.qMRMLNodeComboBox()
    self.plane_2TransformSelector.nodeTypes = ( ("vtkMRMLLinearTransformNode"), "" )
    self.plane_2TransformSelector.noneEnabled = True
    self.plane_2TransformSelector.setMRMLScene( slicer.mrmlScene )
    self.configurationFormLayout.addRow("PLANE_2 Matrix: ", self.plane_2TransformSelector)

    # Apply button
    self.applyMatrixButton = qt.QPushButton("ON")
    self.configurationFormLayout.addRow("Matrix Connection: ", self.applyMatrixButton)
    self.applyMatrixButton.connect('clicked()', self.onApplyMatrixConnectionButton)

    # Stop button
    self.removeMatrixButton = qt.QPushButton("OFF")
    self.configurationFormLayout.addRow("Matrix Connection: ", self.removeMatrixButton)
    self.removeMatrixButton.connect('clicked()', self.onStopMatrixConnectionButton)

    # QTimer
    self.t = qt.QTimer();
    self.t.connect('timeout()',self.tCount)    
    self.freq = 30 #50

    #
    # Dock Panel
    #
    self.createDockPanel()

    # Add vertical spacer
    self.layout.addStretch(1)

    self.extensionSelector = {}
    self.installedExtensionName = {}
    self.selectedItem = {}

    self.currentModuleId = 0
    self.numberOfModule = 0
    self.numberOfExtention = 0
    self.numberOfExtentionList = 0
    self.loadFileFlag = 0
    self.numberOfLabelText = 15
    self.itemsOnOneLine = 3

    #Matrix
    self.timerStopFlag = 0
    self.sensorMatrix = vtk.vtkMatrix4x4()
    self.plane_0Matrix = vtk.vtkMatrix4x4()
    self.plane_1Matrix = vtk.vtkMatrix4x4()
    self.plane_2Matrix = vtk.vtkMatrix4x4()

  def createDockPanel(self):
    self.modules = []

    self.dockPanel = qt.QDockWidget('Plane Control')
    self.dockPanel.windowTitle = "Plane Control"
    self.dockPanel.setAllowedAreas(qt.Qt.LeftDockWidgetArea | qt.Qt.RightDockWidgetArea);

    self.dockFrame = qt.QFrame(self.dockPanel)
    self.dockFrame.setFrameStyle(qt.QFrame.NoFrame)
    self.dockLayout = qt.QVBoxLayout()

    ## Button Frame
    self.dockButtonFrame = qt.QFrame(self.dockFrame)
    self.dockButtonFrame.setFrameStyle(qt.QFrame.NoFrame)
    self.dockButtonLayout = qt.QHBoxLayout()
      
    self.dockButtonFrame.setLayout(self.dockButtonLayout)

    ## Wizard Frame
    self.dockWizardFrame = qt.QFrame(self.dockFrame)
    self.dockWizardFrame.setFrameStyle(qt.QFrame.NoFrame)
    self.dockWizardLayout = qt.QHBoxLayout()

    self.transversalCheckBox = ctk.ctkCheckBox()
    self.transversalCheckBox.text = "Transversal"
    self.transversalCheckBox.enabled = True
    self.transversalCheckBox.checked = False

    self.inplane0CheckBox = ctk.ctkCheckBox()
    self.inplane0CheckBox.text = "Inplane0"
    self.inplane0CheckBox.enabled = True
    self.inplane0CheckBox.checked = False

    self.inplane90CheckBox = ctk.ctkCheckBox()
    self.inplane90CheckBox.text = "Inplane90"
    self.inplane90CheckBox.enabled = True
    self.inplane90CheckBox.checked = False

    self.dockWizardLayout.addWidget(self.transversalCheckBox)
    self.dockWizardLayout.addWidget(self.inplane0CheckBox)
    self.dockWizardLayout.addWidget(self.inplane90CheckBox)

    self.dockWizardFrame.setLayout(self.dockWizardLayout)
    self.dockLayout.addWidget(self.dockWizardFrame)

    self.dockFrame.setLayout(self.dockLayout)
    self.dockPanel.setWidget(self.dockFrame)

    self.dockButtonFrame.show()
    self.dockWizardFrame.show()
    mw = slicer.util.mainWindow()
    mw.addDockWidget(qt.Qt.LeftDockWidgetArea, self.dockPanel)
    self.dockFrame.show()    

  def cleanup(self):
    pass

  def enter(self):
    pass
    
  def onApplyMatrixConnectionButton(self):
    if self.timerStopFlag == 0:
      print("timer was started!")
      self.timerStopFlag = 1
      self.t.start(self.freq)

  def onStopMatrixConnectionButton(self):
    self.timerStopFlag = 0

  def tCount(self):
    if self.sensorTransformSelector.currentNode() != None and self.plane_0TransformSelector.currentNode() != None:
      self.sensorTransform = self.sensorTransformSelector.currentNode()
      self.plane_0Transform = self.plane_0TransformSelector.currentNode()
      
      self.sensorTransform.GetMatrixTransformToParent(self.sensorMatrix)
      self.plane_0Transform.GetMatrixTransformToParent(self.plane_0Matrix)

      for i in xrange(0,4):
        for j in xrange(0,4):
          self.plane_0Matrix.SetElement(i,j,self.sensorMatrix.GetElement(i,j))
      self.plane_0Transform.SetMatrixTransformToParent(self.plane_0Matrix)

    if self.plane_0TransformSelector.currentNode() != None and self.plane_1TransformSelector.currentNode() != None:
      self.plane_0Transform = self.plane_0TransformSelector.currentNode()
      self.plane_1Transform = self.plane_1TransformSelector.currentNode()
      
      self.plane_0Transform.GetMatrixTransformToParent(self.plane_0Matrix)
      self.plane_1Transform.GetMatrixTransformToParent(self.plane_1Matrix)

      for i in xrange(0,4):
        for j in xrange(0,4):
          self.plane_1Matrix.SetElement(i,j,self.plane_0Matrix.GetElement(i,j))
      self.plane_1Transform.SetMatrixTransformToParent(self.plane_1Matrix)

    if self.plane_0TransformSelector.currentNode() != None and self.plane_2TransformSelector.currentNode() != None:
      self.plane_0Transform = self.plane_0TransformSelector.currentNode()
      self.plane_2Transform = self.plane_2TransformSelector.currentNode()
      
      self.plane_0Transform.GetMatrixTransformToParent(self.plane_0Matrix)
      self.plane_2Transform.GetMatrixTransformToParent(self.plane_2Matrix)

      for i in xrange(0,4):
        for j in xrange(0,4):
          self.plane_2Matrix.SetElement(i,j,self.plane_0Matrix.GetElement(i,j))
      self.plane_2Transform.SetMatrixTransformToParent(self.plane_2Matrix)

    if self.timerStopFlag == 0:
      print("timer was stopped!")
      self.t.stop()   

  def onPlaneControl(self):
    slicer.util.selectModule("PlaneControl")
    self.modules[self.currentModuleId].button.setChecked(False)
    self.PlaneControlButton.enabled = False

  def onReload(self,moduleName="PlaneControl"):
    """Generic reload method for any scripted module.
    ModuleWizard will subsitute correct default moduleName.
    """
    import imp, sys, os, slicer

    #Delete IGT Wizard Pane
    self.dockPanel.close()

    widgetName = moduleName + "Widget"
    # reload the source code
    # - set source file path
    # - load the module to the global space
    filePath = eval('slicer.modules.%s.path' % moduleName.lower())
    p = os.path.dirname(filePath)
    if not sys.path.__contains__(p):
      sys.path.insert(0,p)
    fp = open(filePath, "r")
    globals()[moduleName] = imp.load_module(
        moduleName, fp, filePath, ('.py', 'r', imp.PY_SOURCE))
    fp.close()

    # rebuild the widget
    # - find and hide the existing widget
    # - create a new widget in the existing parent
    parent = slicer.util.findChildren(name='%s Reload' % moduleName)[0].parent()
    for child in parent.children():
      try:
        child.hide()
      except AttributeError:
        pass
    # Remove spacer items
    item = parent.layout().itemAt(0)
    while item:
      parent.layout().removeItem(item)
      item = parent.layout().itemAt(0)

    # delete the old widget instance
    if hasattr(globals()['slicer'].modules, widgetName):
      getattr(globals()['slicer'].modules, widgetName).cleanup()

    # create new widget inside existing parent
    globals()[widgetName.lower()] = eval(
        'globals()["%s"].%s(parent)' % (moduleName, widgetName))
    globals()[widgetName.lower()].setup()
    setattr(globals()['slicer'].modules, widgetName, globals()[widgetName.lower()])

  def onReloadAndTest(self,moduleName="PlaneControl"):
    try:
      self.onReload()
      evalString = 'globals()["%s"].%sTest()' % (moduleName, moduleName)
      tester = eval(evalString)
      tester.runTest()
    except Exception, e:
      import traceback
      traceback.print_exc()
      qt.QMessageBox.warning(slicer.util.mainWindow(), 
          "Reload and Test", 'Exception!\n\n' + str(e) + "\n\nSee Python Console for Stack Trace")

#
# PlaneControlLogic
#
class PlaneControlLogic:
  def __init__(self):
    pass

class PlaneControlTest(unittest.TestCase):
  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_PlaneControl1()

  def test_PlaneControl1(self):
    self.delayDisplay('Test passed!')
