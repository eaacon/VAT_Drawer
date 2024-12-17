#-------------------------------------------------------------------------------------------------------
# > Find/create collection for frame meshes.
# > Loop through frame range.
# > Duplicate geometry node simulation (curve object).
# > Convert to mesh.
# > Move to Collection.
# > Numbered rename.

import bpy
import time
import math

from .VAT_Collection_Setup import VFX_Collection_Utilities

class Frame_Generator_Properties(bpy.types.PropertyGroup):
    xOffset: bpy.props.FloatProperty(name = "Separation", default = 5, soft_min = 0, soft_max = 10)
    fStep: bpy.props.IntProperty(name = "Step", default = 1, min = 1, soft_max = 6)
    
    vTDesc = "Optimally, should be power of 2:\n\
256, \n\
512 \n\
1024 \n\
2048 \n\
4096 \n\
8192 \n\
etc"
    vTarget: bpy.props.IntProperty(name = "Vertex Target", description = vTDesc, default = 256, min = 4, soft_max = 16384, step = 4)
    vIterations: bpy.props.IntProperty(name = "Iterations",
        description = "Number of times the Even Remesh modifier will be adjusted to try and match the vertex target",
        default = 3, min = 1, soft_max = 5)

    frameCount: bpy.props.IntProperty(name = "Frame Count", description="(End frame - start frame) / step",
        default = 16)

    isSim: bpy.props.BoolProperty(name = "Sim?", default = True)

    meshFrames: bpy.props.BoolProperty(name = "Mesh Frames", default = False)
    speed: bpy.props.FloatProperty()
    
class MESH_OT_generate_frames(bpy.types.Operator):
    bl_idname = "vfx.generate_frames"
    bl_label = "Generates Frame Snapshots as Mershes in a Collection"
    bl_options = {'REGISTER', 'UNDO'}

    #Create/Set Collection for Mesh Frames and Copy for shading
    fCol = None
    sCol = None
    
    def execute(self, context):  
        
        if bpy.context.active_object.users_collection[0].name == "Frames"\
            or bpy.context.active_object.users_collection[0].name == "Shading":
            context.scene.frame_gen.speed = -1
            self.report({'ERROR_INVALID_INPUT'}, "Active object invalid, should not be in addon collection.")
            return{"CANCELLED"}

        #start time
        st = time.time()

        setup = VFX_Collection_Utilities()
        self.fCol = setup.clear_or_create("Frames")
        self.sCol = setup.clear_or_create("Shading")

        self.create_objects(bpy.context.active_object, bpy.data.scenes["Scene"].frame_start,\
            bpy.data.scenes["Scene"].frame_end,\
            context.scene.frame_gen.fStep)

        self.normalize_and_shade()

        #end time
        et = time.time()

        context.scene.frame_gen.speed = et - st

        return{"FINISHED"}

    def create_objects(self, obj, s, e, step):
        if self.fCol == None:
            print("fCol does not exist")
            return False
        
        fg = bpy.context.scene.frame_gen

        if fg.isSim:
            self.from_geonodes(obj, s, e, step, fg)
        else:
            self.from_animation(obj, s, e, step, fg)
        
    
    def from_geonodes(self, obj, s, e, step, fg):
        #Loop Through Each Frame Step
        for f in range(s, e + 1, step):
            bpy.data.scenes['Scene'].frame_set(f)

            objIndex = len(self.fCol.objects)

            #Duplicate Active Object
            dupe = obj.copy()
            dupe.data = obj.data.copy()
            dupe.name = obj.name + "_" + str(objIndex)
            self.fCol.objects.link(dupe)

            #Apply Transforms
            dupe.data.transform(dupe.matrix_basis)
            dupe.matrix_basis.identity()

            #Offset Location for Organization
            dupe.location[1] = (objIndex + 1) * fg.xOffset

            bpy.context.active_object.select_set(False)
            dupe.select_set(True)
            bpy.context.view_layer.objects.active = dupe

            #Convert To Mesh
            if dupe.type != 'MESH':
                bpy.ops.object.convert(target = 'MESH')

            bpy.context.active_object.select_set(False)
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj
    
    def from_animation(self, obj, s, e, step, fg):
        #Loop Through Each Frame Step
        for f in range(s, e + 1, step):

            objIndex = len(self.fCol.objects)

            dupe = self.snapshot_at_frame(obj, f)

            self.fCol.objects.link(dupe)

            #Offset Location for Organization
            dupe.location[1] = (objIndex + 1) * fg.xOffset

            bpy.context.active_object.select_set(False)
            obj.select_set(True)
            bpy.context.view_layer.objects.active = obj



    # > Duplicates objects in frames collection to the shading reference collection,
    # > Adds Geometry Node Tree to normalize each object's vert count across frames,
    # > Adds Data Transfer modifier linking the shading information.
    def normalize_and_shade(self):
        if self.sCol == None:
            print("fCol does not exist")
            return False

        fg = bpy.context.scene.frame_gen

        for obj in self.fCol.objects:
            #Duplicate object and add to shading collection
            dupe = obj.copy()
            dupe.data = obj.data.copy()
            dupe.name = obj.name.replace("VAT", "Shading")
            self.sCol.objects.link(dupe)

            #Add and setup remesh Geometry Node modifier.
            gn = obj.modifiers.new(name = "Normalize", type = "NODES")
            gn.node_group = bpy.data.node_groups['Even Remesh']
            gn["Socket_2"] = fg.vTarget

            #Add Data Transfer modifier and link to shading reference
            dt = obj.modifiers.new(name = "Copy_Shading", type = "DATA_TRANSFER")
            dt.object = dupe
            dt.use_loop_data = True
            dt.data_types_loops = {'CUSTOM_NORMAL'}
            dt.loop_mapping = 'POLYINTERP_NEAREST'

        for i in range(fg.vIterations):
            for obj in self.fCol.objects:
                gn = obj.modifiers["Normalize"]
                deps = bpy.context.evaluated_depsgraph_get()
                nv = len(obj.evaluated_get(deps).data.vertices)
                
                if nv == fg.vTarget:
                    continue

                if i == fg.vIterations - 1:
                    gn["Socket_7"] = .001
                    gn.node_group.interface_update(bpy.context)
                    continue
                elif i >= fg.vIterations:
                    break
                    
                gn["Socket_8"] += 1
                
                gn.node_group.interface_update(bpy.context)
    
    def snapshot_at_frame(self, obj, frame):

        bpy.data.scenes['Scene'].frame_set(f)

        dg = bpy.context.view_layer.depsgraph
        evalObj = obj.evaluated_get(dg)

        dupe = evalObj.copy()
        dupe.data = evalObj.data.copy()
        dupe.name = 'frame' + str(frame)

        #Apply Transforms
        dupe.data.transform(dupe.matrix_basis)
        dupe.matrix_basis.identity()

        dupe.animation_data_clear()
        return dupe


