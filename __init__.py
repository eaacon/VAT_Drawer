bl_info = {
    "name": "VFX Tools",
    "author": "eaacon",
    "version": (0, 0, 1),
    "blender": (4, 2, 0),
    "location": "3D Viewport > Sidebar > VFX Tools",
    "description": "Advanced Tools For Creating Real-Time VFX Meshes",
    "category": "Tool" }

if 'bpy' in locals():
    import importlib
    import sys
    importlib.reload(sys.modules[Copy_At_Frame])
    
import bpy
import math

from .Copy_At_Frame import Frame_Generator_Properties, MESH_OT_generate_frames
from .Draw_VAT import VAT_Draw_Properties, VAT_OT_draw
from .VAT_Collection_Setup import MESH_OT_setup_vat_collections

class VIEW3D_PT_Frame_Generator(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VFX Tools"
    bl_label = "Frame Generator"
    
    def draw(self, context): 
        fRangeRow = self.layout.row()
        fRangeRow.prop(context.scene, "frame_start")
        fRangeRow.prop(context.scene, "frame_end")
        
        self.layout.prop(context.scene.frame_gen, "fStep", slider = True)
        
        outputCount = self.layout.row()

        fCalc = (context.scene.frame_end - context.scene.frame_start) / context.scene.frame_gen.fStep
        fCalc = math.ceil(fCalc)

        outputCount.label(text = "Count: " + str(fCalc) + " frames")

        outputCount.prop(context.scene.frame_gen, "meshFrames", toggle = True, icon = "MESH_MONKEY", icon_only = True)

        if context.scene.frame_gen.meshFrames == False:
            return

        meshFramesBox = self.layout.box()

        setupRow = meshFramesBox.row()
        split = setupRow.split(factor = 0.8, align = True)
        split.prop(context.scene.frame_gen, "xOffset")
        split.prop(context.scene.frame_gen, "isSim", toggle = True)

        meshFramesBox.separator()

        meshFramesBox.prop(context.scene.frame_gen, "vTarget")
        meshFramesBox.prop(context.scene.frame_gen, "vIterations", slider = True)

        meshFramesBox.separator()

        meshFramesBox.operator("vfx.generate_frames", text = "Generate!")
        
        genTime = meshFramesBox.row()

        spd = round(context.scene.frame_gen.speed, 2)
        genTime.label(text = str(spd) + "s")
        genTime.operator("vfx.setup_collections", text = "Clear")

class VIEW3D_PT_VAT_Drawer(bpy.types.Panel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "VFX Tools"
    bl_label = "VAT Drawer"
    
    def draw(self, context): 
        if context.scene.frame_gen.meshFrames == True:
            row = self.layout.row()
            split = row.split(factor = 0.9, align = True)
            split.prop(context.scene.vat, "exportObj")
            split.prop(context.scene.vat, "deleteExportMesh", toggle = True, icon = "TRASH", icon_only = True)

            self.layout.row().separator()

        row = self.layout.row()
        row.prop(context.scene.vat, "texOnly", toggle = True, icon = "NODE_TEXTURE", icon_only = True)
        row.prop(context.scene.vat, "worldPos", toggle = True, icon = "WORLD", text = "World")
        row.prop(context.scene.vat, "genBaseUV", toggle = True, icon = "UV", text = "UV")
        row.prop(context.scene.vat, "ratio")

        box = self.layout.box()

        row = box.row()
        row.prop(context.scene.vat, "outputDir")
        row.prop(context.scene.vat, "isFolded", toggle = True, icon = "MOD_EDGESPLIT", icon_only = True)
        if context.scene.vat.texOnly == False:
            row.prop(context.scene.vat, "hasExtras", toggle = True, icon = "DECORATE_LINKED", icon_only = True)

        if context.scene.vat.hasExtras == True and context.scene.vat.texOnly == False:
            row = box.row()
            row.prop(context.scene.vat, "exportExtras", icon_only = True)
        
        if context.scene.vat.texOnly == False:
            row = box.row()
            row.scale_y = 1.5
            row.prop(context.scene.vat, "exportType", expand=True)

        draw = self.layout.row()
        draw.scale_y = 2
        draw.operator("vfx.draw_vat", text = "Draw!")

        create = self.layout.row()

        spd = round(context.scene.vat.speed, 2)
        #create.label(text = str(spd) + "s")
        
        create.progress(text = str(spd) + "s", factor = context.scene.vat.progress)

        create.prop(context.scene.vat, "popup", toggle = True, icon_only = True)
        if context.scene.frame_gen.meshFrames == False and context.scene.vat.texOnly == False:
            create.prop(context.scene.vat, "deleteExportMesh", toggle = True, icon = "TRASH", icon_only = True)
        
        pass

classes = (Frame_Generator_Properties,
    VAT_Draw_Properties,
    VIEW3D_PT_Frame_Generator,
    VIEW3D_PT_VAT_Drawer,
    MESH_OT_generate_frames,
    VAT_OT_draw,
    MESH_OT_setup_vat_collections)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    
    bpy.types.Scene.frame_gen = bpy.props.PointerProperty(type = Frame_Generator_Properties)
    bpy.types.Scene.vat = bpy.props.PointerProperty(type = VAT_Draw_Properties)

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    
    del bpy.types.Scene.frame_gen
    del bpy.types.Scene.vat

if __name__ == "__main__":
    register()