import bpy
from bpy.props import *
from ... matrix.c_utils import*
from . effector_utils import targetEffectorFunction
from .... base_types import AnimationNode, VectorizedSocket
from .... events import propertyChanged, executionCodeChanged
from .... algorithms.rotations import directionsToMatrices, eulersToDirections
from .... data_structures import Vector3DList, VirtualVector3DList, VirtualEulerList, Matrix4x4List, DoubleList

trackAxisItems = [(axis, axis, "") for axis in ("X", "Y", "Z", "-X", "-Y", "-Z")]
guideAxisItems  = [(axis, axis, "") for axis in ("X", "Y", "Z")]
directionAxisItems = [(axis, axis, "", "", i)
                      for i, axis in enumerate(("X", "Y", "Z", "-X", "-Y", "-Z"))]

class TargetEffectorNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_TargetEffector"
    bl_label = "Target Effector"
    bl_width_default = 150

    trackAxis: EnumProperty(items = trackAxisItems, update = propertyChanged, default = "Z")
    guideAxis: EnumProperty(items = guideAxisItems, update = propertyChanged, default = "X")
    directionAxis: EnumProperty(name = "Direction Axis", default = "Z",
        items = directionAxisItems, update = propertyChanged)

    useTargetList: VectorizedSocket.newProperty()

    def checkedPropertiesChanged(self, context):
        self.updateSocketVisibility()
        executionCodeChanged()

    useOffset: BoolProperty(update = checkedPropertiesChanged)
    useDirection: BoolProperty(update = checkedPropertiesChanged)
    useScale: BoolProperty(update = checkedPropertiesChanged)
    considerRotationsIn: BoolProperty(name = "Consider Incoming Rotations", default = False, update = propertyChanged)

    def create(self):
        self.newInput("Matrix List", "Matrices", "matrices")
        self.newInput(VectorizedSocket("Matrix", "useTargetList",
            ("Target", "target"), ("Targets", "targets")))
        self.newInput("Float", "Distance", "distanceIn")
        self.newInput("Float", "Width", "width", value = 3.0)
        self.newInput("Float", "Strength", "offsetStrength", value = 1.0)
        self.newInput("Vector", "Scale", "scaleIn")
        self.newInput("Vector", "Guide", "guideIn", value = (0,0,1), hide = True)
        self.newInput("Falloff", "Falloff", "falloff")
        self.newOutput("Matrix List", "Matrices", "matricesOut")
        self.newOutput("Float List", "Effector Strength", "effectorStrength", hide = True)
        self.newOutput("Float List", "Falloff Strength", "falloffStrength", hide = True)

        self.updateSocketVisibility()

    def draw(self, layout):
        col = layout.column(align = True)
        row = col.row(align = True)
        row.prop(self, "useDirection", text = "Direction", toggle = True, icon = "CON_TRACKTO")
        row = col.row(align = True)
        row.prop(self, "useOffset", text = "Offset", toggle = True, icon = "TRANSFORM_ORIGINS")
        row.prop(self, "useScale", text = "Scale", toggle = True, icon = "FULLSCREEN_ENTER")
        if self.useDirection:
            layout.prop(self, "trackAxis", expand = True)
            layout.prop(self, "guideAxis", expand = True)
            if self.trackAxis[-1:] == self.guideAxis[-1:]:
                layout.label(text = "Must be different", icon = "ERROR")

    def drawAdvanced(self, layout):
        layout.prop(self, "considerRotationsIn") 
        layout.prop(self, "directionAxis", expand = True)
            
    def updateSocketVisibility(self):
        condition = self.useOffset or self.useScale
        self.inputs[2].hide = not condition
        self.inputs[3].hide = not condition
        self.inputs[4].hide = not self.useOffset
        self.inputs[5].hide = not self.useScale

    def execute(self, matrices, targets, distanceIn, width, offsetStrength, scaleIn, guideIn, falloff):
        if not self.useTargetList: targets = Matrix4x4List.fromValues([targets])
        count = len(matrices)
        if len(targets) == 0 or len(matrices) == 0:
            return Matrix4x4List(), DoubleList(), DoubleList()
        else:
            if [self.useDirection, self.useOffset, self.useScale] == [0,0,0]:
                DefaultList = DoubleList(length = count)
                DefaultList.fill(0)
                return matrices, DefaultList, DefaultList
            else:
                vectors = extractMatrixTranslations(matrices)
                scales = extractMatrixScales(matrices)
                Directions = eulersToDirections(extractMatrixRotations(matrices), self.directionAxis)

                targetDirections = Vector3DList(length = len(vectors))
                targetDirections.fill(0)

                if self.considerRotationsIn:
                    targetDirections = Directions.copy()

                falloffEvaluator = self.getFalloffEvaluator(falloff)
                influences = DoubleList.fromValues(falloffEvaluator.evaluateList(vectors))

                v, d, s, eStrength = targetEffectorFunction(targets, vectors, targetDirections, scales, Directions, distanceIn, width, 
                            offsetStrength, scaleIn, influences, self.useOffset, self.useDirection, self.useScale)
                r = directionsToMatrices(d, guideIn, self.trackAxis, self.guideAxis).toEulers()

                _v = VirtualVector3DList.create(v, (0, 0, 0))    
                _r = VirtualEulerList.create(r, (0, 0, 0))
                _s = VirtualVector3DList.create(s, (1, 1, 1))
                return composeMatrices(count, _v, _r, _s), eStrength, influences

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")    
