import bpy
from bpy.props import *
from ... utils.depsgraph import getEvaluatedID
from ... base_types import AnimationNode, VectorizedSocket
from ... data_structures import Vector3DList, BooleanList, DoubleList

collisionShapeItems = [
    ("BOX", "Box", "", "NONE", 0),
    ("SPHERE", "Sphere", "", "NONE", 1),
    ("CAPSULE", "Capsule", "", "NONE", 2),
    ("CYLINDER", "Cylinder", "", "NONE", 3),
    ("CONE", "Cone", "", "NONE", 4),
    ("CONVEX_HULL", "Convex Hull", "", "NONE", 5),
    ("MESH", "Mesh", "", "NONE", 6)    
]

class RigidBodyTrigger(bpy.types.Node, AnimationNode):
    bl_idname = "an_RigidBodyTrigger"
    bl_label = "Rigid Body Trigger"
    errorHandlingType = "EXCEPTION"

    collisionShape: EnumProperty(name = "Collision Shape", default = "CONVEX_HULL",
        items = collisionShapeItems, update = AnimationNode.refresh)

    useObjectList: VectorizedSocket.newProperty()
    useDynamicsList: VectorizedSocket.newProperty()
    useMassList: VectorizedSocket.newProperty()
    useFrictionList: VectorizedSocket.newProperty()
    useBouncinessList: VectorizedSocket.newProperty()

    linkObject: BoolProperty(name = "Link Object", description = "link objects to rigid body collection", default = True, update = AnimationNode.refresh)
    enableLink: BoolProperty(name = "Is Used", default = True, update = AnimationNode.refresh)
    enableShape: BoolProperty(name = "Is Used", default = True, update = AnimationNode.refresh)
    useMoreSettings: BoolProperty(name = "More Settings", default = False, update = AnimationNode.refresh)
    linkInvoked: BoolProperty(name = "More Settings2", default = False, update = AnimationNode.refresh)
    isLinked: BoolProperty(name = "More Settings", default = False, update = AnimationNode.refresh)

    def create(self):
        self.newInput("Scene", "Scene", "scene", hide = True)
        self.newInput(VectorizedSocket("Object", "useObjectList",
            ("Object", "object", dict(defaultDrawType = "PROPERTY_ONLY")),
            ("Objects", "objects")))   
        self.newInput("Falloff", "Falloff", "falloff")
        self.newInput("Float", "Threshold", "threshold", value = 0.5)
        if self.useMoreSettings:    
            self.newInput(VectorizedSocket("Boolean", "useDynamicsList",
                ("Dynamic", "dynamic"),("Dynamics", "dynamics")))
            self.newInput(VectorizedSocket("Float", "useMassList",
                ("Mass", "mass"),("Masses", "masses")))
            self.newInput(VectorizedSocket("Float", "useFrictionList",
                ("Friction", "friction"),("Frictions", "frictions")))
            self.newInput(VectorizedSocket("Float", "useBouncinessList",
                ("Bounciness", "bounciness"),("Bouncinesses", "bouncinesses")))           

        self.newOutput(VectorizedSocket("Object", "useObjectList",
            ("Object", "objectOut", dict(defaultDrawType = "PROPERTY_ONLY")),
            ("Objects", "objectsOut")))

        if self.useMoreSettings:
            for i in range(4,8):    
                self.inputs[i].useIsUsedProperty = True
                self.inputs[i].isUsed = False

    def edit(self):
        inputSocket = self.inputs[0]
        origin = inputSocket.dataOrigin
        if origin is None: return
        if origin.dataType != "Scene":
            inputSocket.removeLinks()
            inputSocket.hide = True

    def invokeLinkUnlink(self):
        # linkInvoked is set to 1 when button pressed
        self.linkInvoked = True
        # on every button press isLinked value is altered
        self.isLinked = not self.isLinked

    def draw(self, layout):
        row = layout.row(align = True)
        self.invokeFunction(row, "invokeLinkUnlink", text = "Link | Unlink")
        if self.useMoreSettings:
            row2 = layout.row(align = True)
            row2.prop(self, "collisionShape", text = "")
            row3 = row2.row(align = True)
            testIcon = "LAYER_USED"
            if self.enableShape:
                testIcon = "LAYER_ACTIVE"
            row3.prop(self, "enableShape", text = "", icon = testIcon)
            row2.active = self.enableShape

    def drawAdvanced(self, layout):
        layout.prop(self, "useMoreSettings")     

    def getExecutionFunctionName(self):
        if not self.useMoreSettings:
            return "execute_Simple"
        else:
            return "execute_MoreSettings"

    def execute_Simple(self, scene, objects, falloff, threshold):
        if objects is None:
            return
        if not self.useObjectList:
            objects = [objects]
        if not scene is None:
            rigidbody_world = scene.rigidbody_world
            if rigidbody_world is None:
                self.raiseErrorMessage("Rigid Body World not found")
            else:
                locations = Vector3DList.fromValues([getEvaluatedID(object).location for object in objects])
                falloffEvaluator = self.getFalloffEvaluator(falloff)
                influences = falloffEvaluator.evaluateList(locations)
                
                rb_collection = rigidbody_world.collection
                if rb_collection is None:
                    self.setErrorMessage("Rigid Body Collection not found")
                else:
                    if self.linkInvoked:
                        self.link_Objects(objects, rb_collection.objects)
                        self.linkInvoked = False # on every execution this boolean value set to false

                    for obj, influence in zip(objects, influences):
                        if obj.type != "MESH":
                            self.setErrorMessage("Object is not a mesh object")
                        else:
                            try:
                                obj.rigid_body.kinematic = True
                                if threshold <= influence:
                                    obj.rigid_body.kinematic = False
                            except:
                                self.setErrorMessage("Link objects to rigid body collection")
        return objects      

    def execute_MoreSettings(self, scene, objects, falloff, threshold, dynamics, masses, frictions, bouncinesses):
        if objects is None:
            return
        count = len(objects)
        if not self.useObjectList: objects = [objects]
        if not self.useDynamicsList: dynamics = self.fillList(dynamics, count, "boolean")
        if not self.useMassList: masses = self.fillList(masses, count, "float")
        if not self.useFrictionList: frictions = self.fillList(frictions, count, "float") 
        if not self.useBouncinessList: bouncinesses = self.fillList(bouncinesses, count, "float")        
    
        if not scene is None:
            rigidbody_world = scene.rigidbody_world
            if rigidbody_world is None:
                self.raiseErrorMessage("Rigid Body World not found")
            else:
                locations = Vector3DList.fromValues([getEvaluatedID(object).location for object in objects])
                falloffEvaluator = self.getFalloffEvaluator(falloff)
                influences = falloffEvaluator.evaluateList(locations)
                rb_collection = rigidbody_world.collection

                if rb_collection is None:
                    self.setErrorMessage("Rigid Body Collection not found")
                else:
                    if self.linkInvoked:
                        self.link_Objects(objects, rb_collection.objects)
                        self.linkInvoked = False # on every execution this boolean value set to false

                    totalCount = len(dynamics) + len(masses) + len(frictions) + len(bouncinesses)
                    if totalCount / 4 != count:
                        self.setErrorMessage("Boolean list length mismatch")
                    else:
                        for i in range(count):
                            if objects[i].type != "MESH":
                                self.setErrorMessage("Object is not a mesh object")
                            else:
                                try:
                                    if self.inputs[5].isUsed: objects[i].rigid_body.mass = masses[i]
                                    if self.inputs[4].isUsed: objects[i].rigid_body.enabled = dynamics[i]
                                    if self.inputs[6].isUsed: objects[i].rigid_body.friction = frictions[i]
                                    if self.inputs[7].isUsed: objects[i].rigid_body.restitution = bouncinesses[i]
                                    objects[i].rigid_body.kinematic = True
                                    if threshold <= influences[i]:
                                        objects[i].rigid_body.kinematic = False
                                    if self.enableShape: objects[i].rigid_body.collision_shape = self.collisionShape    
                                except:
                                    self.setErrorMessage("Link objects to rigid body collection")
        return objects

    def link_Objects(self, objects, rb_objects):
        for obj in objects:
            if self.isLinked:
                if obj.name not in rb_objects: rb_objects.link(obj)
            else:
                if obj.name in rb_objects: rb_objects.unlink(obj)

    def fillList(self, value, count, datatype):
        if datatype == "boolean":
            b = BooleanList(length = count)
        elif datatype == "float":
            b = DoubleList(length = count)
        b.fill(value)
        return b
       
    def getFalloffEvaluator(self, falloff):
        try: return falloff.getEvaluator("LOCATION")
        except: self.raiseErrorMessage("This falloff cannot be evaluated for vectors")
