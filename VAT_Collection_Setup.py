import bpy

class MESH_OT_setup_vat_collections(bpy.types.Operator):
    bl_idname = "vfx.setup_collections"
    bl_label = "Creates or clears two collections for VAT frame meshes"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        vfxUtil = VFX_Collection_Utilities()
        vfxUtil.clear_or_create("Frames")
        vfxUtil.clear_or_create("Shading")
        return{"FINISHED"}

class VFX_Collection_Utilities():
    #Does collection of String name exist?
    def collection_exists(self, c):
        for col in bpy.data.collections:
            if col.name == c:
                return bpy.data.collections[c]
        return None

    #Clear collection if exists, otherwise make new.
    def clear_or_create(self, c):
        col = self.collection_exists(c)

        if col != None:
            
            bpy.ops.object.select_all(action = 'DESELECT')

            for ob in reversed(col.all_objects):
                ob.select_set(True)
                bpy.data.objects.remove(ob, do_unlink = True)
        else:

            col = bpy.data.collections.new(c)
            
            #Link Collection to Scene Collection
            bpy.context.scene.collection.children.link(col)

        
        return col