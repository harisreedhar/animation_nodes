import bpy
import random
from bpy.props import *
from ... base_types import AnimationNode, VectorizedSocket
from ... events import propertyChanged, executionCodeChanged
from ... data_structures import Vector3DList, PolySpline, BezierSpline

tracerPointTypeItems = [
    ("POLY", "Poly Spline", "Append point to poly spline", "NONE", 0),
    ("BEZIER_POINT", "Bezier Spline", "Append point to bezier spline", "NONE", 1)]

class StoreSpline(object):
    def __init__(self, spline):
        self.polyspline = PolySpline()
        self.bezierspline = BezierSpline()

p = {}

class SplineTracerNode(bpy.types.Node, AnimationNode):
    bl_idname = "an_splinetracer"
    bl_label = "Spline Tracer"
    bl_width_default = 150
    
    def checkedPropertiesChanged(self, context):
        self.updateSocketVisibility()
        executionCodeChanged()
    
    useRandomIdentifier: BoolProperty(update = checkedPropertiesChanged)
    
    tracerpointType: EnumProperty(name = "Spline Type", default = "POLY",
        items = tracerPointTypeItems, update = AnimationNode.refresh)

    usevectorlist: VectorizedSocket.newProperty()

    def create(self):
        self.newInput("Scene", "Scene", "scene", hide = True)
        self.newInput(VectorizedSocket("Vector", "usevectorlist",
            ("Point ", "point"), ("Points", "points")))   
        self.newInput("Integer", "Reset Frame", "resetframe", value = 1)
        self.newInput("Integer", "Start Frame", "start", value = 1)
        self.newInput("Integer", "End Frame", "end", value = 250)
        self.newInput("Float", "Radius", "radius", value = 0.1, minValue = 0)
        self.newInput("Float", "Tilt", "tilt")
        if self.tracerpointType == "BEZIER_POINT":
            self.newInput("Float", "Smoothness", "smoothness", value = 0.33)
        self.newInput("Float", "Min Distance", "minDistance", value = 0.01, minValue = 0)     
        self.newInput("Boolean", "Append Condition", "appendCondition", value = 1, hide = True)
        self.newInput("Integer", "Identifier Seed", "identifierSeed")

        self.newOutput(VectorizedSocket("Spline", "usevectorlist",
            ("Spline", "spline"), ("Splines", "splines")))

        self.updateSocketVisibility()

    def draw(self, layout):
        layout.prop(self, "tracerpointType", text = "")

    def drawAdvanced(self, layout):
        layout.label(text = "Experimental", icon = "ERROR")
        layout.label(text = "Use this option only when using inside loop")
        layout.prop(self, "useRandomIdentifier", text = "Use Random Identifier Seed")

    def updateSocketVisibility(self):
        if self.tracerpointType == "BEZIER_POINT":
            self.inputs[10].hide = not self.useRandomIdentifier
        else:
            self.inputs[9].hide = not self.useRandomIdentifier    
    
    def edit(self):
        inputSocket = self.inputs[0]
        origin = inputSocket.dataOrigin
        if origin is None: return
        if origin.dataType != "Scene":
            inputSocket.removeLinks()
            inputSocket.hide = True    

    def getExecutionFunctionName(self):
        if self.tracerpointType == "BEZIER_POINT":
            return "execute_beziersplines"
        elif self.tracerpointType == "POLY":
            return "execute_polysplines"          
      
    def execute_polysplines(self, scene, points, resetframe, start, end, radius, tilt, minDistance, appendCondition, identifierSeed):    
        if not self.usevectorlist:
            points = Vector3DList.fromValues([points])

        T = self.getTime(scene, resetframe)
        vecDistance = minDistance

        identifier = self.setIdentifier(identifierSeed)
         
        if T == resetframe:
            p[identifier] = []
        p_object = p.get(identifier, [])

        splinelist = []
        if T != resetframe and len(p_object) == 0:
            if not self.usevectorlist:
                return PolySpline()
            else:     
                return splinelist
           
        for i, point in enumerate(points):
            p_object.append(StoreSpline(i))
            if len(p_object[i].polyspline.points)!=0:
                vecDistance = (p_object[i].polyspline.points[-1] - point).length    
            if T >= start and T <= end and appendCondition and vecDistance >= minDistance :
                p_object[i].polyspline.appendPoint(point, radius, tilt)   
            splinelist.append(p_object[i].polyspline)
        p[identifier] = p_object

        if not self.usevectorlist:
            return splinelist[0]
        else:     
            return splinelist

    def execute_beziersplines(self, scene, points, resetframe, start, end, radius, tilt, smoothness, minDistance, appendCondition, identifierSeed):
        if not self.usevectorlist:
            points = Vector3DList.fromValues([points])

        T = self.getTime(scene, resetframe)
        vecDistance = minDistance

        identifier = self.setIdentifier(identifierSeed)
        
        if T == resetframe:
            p[identifier] = []
        p_object = p.get(identifier, [])

        splinelist = []
        if T != resetframe and len(p_object) == 0: 
            if not self.usevectorlist:
                return BezierSpline()
            else:     
                return splinelist

        for i, point in enumerate(points):
            p_object.append(StoreSpline(i))
            if len(p_object[i].bezierspline.points)!=0:
                vecDistance = (p_object[i].bezierspline.points[-1] - point).length
            if T >= start and T <= end and appendCondition and vecDistance >= minDistance :
                p_object[i].bezierspline.appendPoint(point, (0,0,0), (0,0,0), radius, tilt)
            splinelist.append(p_object[i].bezierspline)
            splinelist[i].smoothAllHandles(smoothness)
        p[identifier] = p_object

        if not self.usevectorlist:
            return splinelist[0]
        else:     
            return splinelist

    def getTime(self, scene, resetframe):
        if scene is not None:
            return scene.frame_current_final
        else:
            return resetframe 

    def setIdentifier(self, identifierSeed):
        identifier = self.identifier + "splineTracer"
        if self.useRandomIdentifier:
            identifier += self.randomText(identifierSeed)
        return identifier

    def randomText(self, seed):
        length = 6
        characters = "abcdefghijklmnopqrstuvwxyz"
        random.seed(seed + 12334)
        return ''.join(random.choice(characters) for _ in range(length))
         