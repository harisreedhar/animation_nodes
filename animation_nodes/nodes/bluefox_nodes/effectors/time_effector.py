import bpy
import numpy as np
from bpy.props import *
from . effector_utils import offsetMatrices
from .... base_types import AnimationNode, VectorizedSocket
from .... events import propertyChanged, executionCodeChanged
from .... nodes.number.c_utils import mapRange_DoubleList_Interpolated
from .... data_structures import VirtualVector3DList, VirtualEulerList, VirtualDoubleList
from .... data_structures import Matrix4x4List, DoubleList, Vector3DList, EulerList, FloatList

class TimeEffectorNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_TimeEffector"
    bl_label = "Time Effector"
    bl_width_default = 180
    errorHandlingType = "EXCEPTION"

    def checkedPropertiesChanged(self, context):
        self.updateSocketVisibility()
        executionCodeChanged()

    useLocationList: VectorizedSocket.newProperty()
    useRotationList: VectorizedSocket.newProperty()
    useScaleList: VectorizedSocket.newProperty()
    useDurationList: VectorizedSocket.newProperty()
    useSpeedList: VectorizedSocket.newProperty()   

    useLocation: BoolProperty(update = checkedPropertiesChanged)
    useRotation: BoolProperty(update = checkedPropertiesChanged)
    useScale: BoolProperty(update = checkedPropertiesChanged)
    useInfinite: BoolProperty(name = "Infinite", default = False, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Matrix List", "Matrices", "matrices")
        self.newInput(VectorizedSocket("Vector", "useLocationList",
            ("Location", "locations", dict(value = (0, 0, 0))),
            ("Locations", "locations")))
        self.newInput(VectorizedSocket("Euler", "useRotationList",
            ("Rotation", "rotations", dict(value = (0, 0, 0))),
            ("Rotations", "rotations")))
        self.newInput(VectorizedSocket("Vector", "useScaleList",
            ("Scale", "scales", dict(value = (0, 0, 0))),
            ("Scales", "scales")))
        self.newInput("Float", "Time", "time")
        self.newInput(VectorizedSocket("Float", "useDurationList",
            ("Duration", "durations", dict(value = 20)),
            ("Durations", "durations")))     
        self.newInput(VectorizedSocket("Float", "useSpeedList",
            ("Speed", "speeds", dict(value = 1)),
            ("Speeds", "speeds")))
        self.newInput("Falloff", "Falloff", "falloff")
        self.newInput("Float", "Min", "minValue", value = 0, hide = True)
        self.newInput("Float", "Max", "maxValue", value = 1, hide = True)
        self.newInput("Interpolation", "Interpolation", "interpolation", defaultDrawType = "PROPERTY_ONLY")
        self.newOutput("Matrix List", "Matrices", "matricesOut")
        self.newOutput("Float List", "Effector Strength", "effectorStrength", hide = True)
        self.newOutput("Float List", "Falloff Strength", "falloffStrength", hide = True)

        self.updateSocketVisibility()

    def draw(self, layout):
        row = layout.row(align = True)
        subrow = row.row(align = True)
        subrow.prop(self, "useLocation", index = 0, text = "Loc", toggle = True, icon = "EXPORT")
        subrow.prop(self, "useRotation", index = 1, text = "Rot", toggle = True, icon = "FILE_REFRESH") 
        subrow.prop(self, "useScale", index = 2, text = "Scale", toggle = True, icon = "FULLSCREEN_ENTER")
        layout.prop(self, "useInfinite") 

    def updateSocketVisibility(self):
        self.inputs[1].hide = not self.useLocation
        self.inputs[2].hide = not self.useRotation
        self.inputs[3].hide = not self.useScale
              
    def execute(self, matrices, locations, rotations, scales, time, durations, speeds, falloff, minValue, maxValue, interpolation):
        if not self.useLocationList: locations = Vector3DList.fromValue(locations)
        if not self.useRotationList: rotations = EulerList.fromValue(rotations)
        if not self.useScaleList: scales = Vector3DList.fromValue(scales)
        if not self.useDurationList: durations = DoubleList.fromValue(durations)
        if not self.useSpeedList: speeds = DoubleList.fromValue(speeds)
        if matrices is None:
            return Matrix4x4List(), DoubleList(), DoubleList()
        else:
            count = len(matrices)
            _durations = VirtualDoubleList.create(durations,0).materialize(count)
            _speeds = VirtualDoubleList.create(speeds,0).materialize(count)
            falloff_strengths, effector_strengths = self.calculateStrengths(falloff, matrices, time, _durations, _speeds, interpolation, minValue, maxValue)
            
            if not self.useLocation:
                locations = Vector3DList.fromValue([0,0,0])
            if not self.useRotation:
                rotations = EulerList.fromValue([0,0,0])
            if not self.useScale:
                scales = Vector3DList.fromValue([0,0,0])

            _locations = VirtualVector3DList.create(locations, (0, 0, 0))
            _rotations = VirtualEulerList.create(rotations, (0, 0, 0))
            _scales = VirtualVector3DList.create(scales, (0, 0, 0))
            newMatrices =  offsetMatrices(matrices, _locations, _rotations, _scales, effector_strengths)

            return newMatrices, effector_strengths, falloff_strengths

    def calculateStrengths(self, falloff, matrices, time, durations, speeds, interpolation, minValue, maxValue):
        if len(durations) != 0:
            timeOffset_array = time / durations.asNumpyArray() * speeds.asNumpyArray()
            if not self.useInfinite:
                timeOffset_array = np.clip(timeOffset_array,0,1)

            falloffEvaluator = self.getFalloffEvaluator(falloff)
            falloff_strengths = DoubleList.fromValues(falloffEvaluator.evaluateList(matrices))
            effector_strengths = mapRange_DoubleList_Interpolated(falloff_strengths, interpolation, 0, 1, minValue, maxValue)
            
            timeOffset_array *= effector_strengths.asNumpyArray()
            
            return falloff_strengths, DoubleList.fromNumpyArray(timeOffset_array.astype('double'))
        else:
            return DoubleList(), DoubleList()   

    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("TRANSFORMATION_MATRIX")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for matrices")          
    