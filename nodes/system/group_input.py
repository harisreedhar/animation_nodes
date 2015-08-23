import bpy
from bpy.props import *
from . utils import updateCallerNodes
from ... sockets.info import toIdName
from ... events import networkChanged
from ... base_types.node import AnimationNode
from . subprogram_sockets import SubprogramData

class GroupInput(bpy.types.Node, AnimationNode):
    bl_idname = "an_GroupInput"
    bl_label = "Group Input"

    subprogramName = StringProperty(name = "Subprogram Name", default = "Group",
        description = "Subprogram name to identify this group elsewhere",
        update = networkChanged)

    subprogramDescription = StringProperty(name = "Description", default = "",
        description = "Short description about what this group does",
        update = networkChanged)

    def create(self):
        socket = self.outputs.new("an_NodeControlSocket", "New Parameter")
        socket.drawCallback = "drawNewParameterSocket"
        self.width = 180

    def draw(self, layout):
        layout.separator()
        layout.prop(self, "subprogramName", text = "", icon = "GROUP_VERTEX")
        if self.outputNode is None:
            self.functionOperator(layout, "createGroupOutputNode", text = "Output Node", icon = "PLUS")

    def drawAdvanced(self, layout):
        col = layout.column()
        col.label("Description:")
        col.prop(self, "subprogramDescription", text = "")

        col = layout.column()
        col.label("Parameter Defaults:")
        box = col.box()
        for socket in list(self.outputs)[:-1]:
            socket.drawInput(box, self, socket.getDisplayedName())

    def drawNewParameterSocket(self, layout):
        self.functionOperator(layout, "chooseNewParameterType", text = "New Parameter", emboss = False)

    def chooseNewParameterType(self):
        self.chooseSocketDataType("newParameter")

    def edit(self):
        for target in self.newParameterSocket.dataTargetSockets:
            if target.dataType == "Node Control": continue
            socket = self.newParameter(target.dataType, target.getDisplayedName(), target.getStoreableValue())
            socket.linkWith(target)
        self.newParameterSocket.removeConnectedLinks()

    def newParameter(self, dataType, name = "Socket", defaultValue = None):
        socket = self.outputs.new(toIdName(dataType), name, "parameter")
        if defaultValue is not None: socket.setStoreableValue(defaultValue)
        socket.customName = name
        socket.moveable = True
        socket.removeable = True
        socket.displayCustomName = True
        socket.nameSettings.editable = True
        socket.display.customNameInput = True
        socket.display.removeOperator = True
        socket.moveUp()
        return socket

    def socketChanged(self):
        self.updateCallerNodes()

    def delete(self):
        self.outputs.clear()
        self.updateCallerNodes()

    def updateCallerNodes(self):
        updateCallerNodes(self.identifier)

    def getSocketData(self):
        data = SubprogramData()
        for socket in self.outputs[:-1]:
            data.newInputFromSocket(socket)
        if self.outputNode is not None:
            for socket in self.outputNode.inputs[:-1]:
                data.newOutputFromSocket(socket)
        return data

    @property
    def newParameterSocket(self):
        return self.outputs[-1]

    @property
    def outputNode(self):
        return self.network.groupOutputNode

    def createGroupOutputNode(self):
        settings = [{"name" : "groupInputIdentifier", "value" : repr(self.identifier)}]
        bpy.ops.node.add_and_link_node("INVOKE_DEFAULT", use_transform = True, settings = settings, type = "an_GroupOutput")
