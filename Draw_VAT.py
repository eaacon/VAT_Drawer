import bpy
import bmesh
import math
import mathutils
import time

class VAT_Draw_Properties(bpy.types.PropertyGroup):
    exportObj: bpy.props.PointerProperty(type = bpy.types.Object, name = "")

    hasExtras: bpy.props.BoolProperty(name = "Include Extras?", default = False, 
    description = "Would you like to include extra objects in export?")
    exportExtras: bpy.props.PointerProperty(type = bpy.types.Collection, name = "Extra Meshes", 
    description="Include collection meshes in exported file as non-VAT objects.")

    genBaseUV: bpy.props.BoolProperty(name = "Generate UV Map",
    default = False,
    description="Cube project default UVs")

    worldPos: bpy.props.BoolProperty(name = "World Space", default = False, 
    description = "Should VAT be drawn based on world space position/normal?")

    isFolded: bpy.props.BoolProperty(name = "Make Square",
    default = True,
    description="Attempts to cut in half and stack the output image to become as square as possible")

    popup: bpy.props.BoolProperty(name = "Popup?", default = True)

    outputDir: bpy.props.StringProperty(
        name="",
        description="Location to save VAT textures",
        default="",
        subtype='FILE_PATH'
    )

    deleteExportMesh: bpy.props.BoolProperty(name = "Delete Temp Export Mesh",
    default = True,
    description="Removes temporary mesh used for export")

    exportType: bpy.props.EnumProperty(
        name = "Export Format",
        items = [('fbx', "FBX", ""),('gltf', "GLTF", "")]
    )

    ratio: bpy.props.IntProperty(default = 0, description= "If != 0, then overrides automatic ratio setting")
    speed: bpy.props.FloatProperty(default= 0)
    progress: bpy.props.FloatProperty(default= 0)

class VAT_OT_draw(bpy.types.Operator):
    bl_idname = "vfx.draw_vat"
    bl_label = "Draws two textures: One for vertex positions, and one for normals/rotation "
    bl_options = {'REGISTER', 'UNDO'}

    vPos = list()
    vNorm = list()

    cuts = 1
    vertices = 0
    frameCount = 0
    uvProgress = 0

    def execute(self, context):
        #start time
        st = time.time()

        if context.scene.frame_gen.meshFrames == True:
            self.execute_meshFrames(context)
        else:
            self.execute_normal(context)
        
        et = time.time()
        context.scene.vat.speed = et - st

        return{"FINISHED"} 
    
    def execute_normal(self, context):
        context.scene.vat.progress = 0
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP')
        #get objects for VAT
        vatObjs = context.selected_objects

        if len(vatObjs) == 0:
            print("no objects selected")
            context.scene.vat.speed = 0
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP')
            return

        for o in vatObjs:
            self.vertices += len(o.data.vertices)

        #find total frames of VAT
        fCalc = (context.scene.frame_end - context.scene.frame_start) / context.scene.frame_gen.fStep
        fCalc = math.ceil(fCalc)
        self.frameCount = fCalc

        #figure out scale ratio
        if bpy.context.scene.vat.ratio != 0:
            scale = bpy.context.scene.vat.ratio
        else:
            deps = bpy.context.evaluated_depsgraph_get()
            obj = bpy.context.active_object.evaluated_get(deps)
            scale = self.calc_ratio([obj])

        context.scene.vat.progress = .15

        #image to show after operation (position VAT usually)
        pImg = None
        #metadata
        meta = str(self.frameCount) + "_" + str(scale) + "_" + str(bpy.context.scene.render.fps/bpy.context.scene.frame_gen.fStep)

        #get vertex data and draw vat
        if context.scene.vat.isFolded:
            #aspectRatio = math.floor(math.log2(math.sqrt(self.vertices/self.frameCount)))
            #self.cuts = pow(2,aspectRatio)
            tempCuts = int(math.sqrt(self.vertices/self.frameCount))
            cutCheck = self.vertices/tempCuts
            while cutCheck % 1 != 0:
                tempCuts -= 1
                cutCheck = self.vertices/tempCuts

            self.cuts = tempCuts

            meta += "_" + str(self.cuts)
            print(self.cuts)
            vData = self.get_anim_vertex_data(self.cuts, vatObjs, scale)

            self.draw_vat_image(vData[0], "_position" + meta, [int(self.vertices / self.cuts), int(self.frameCount * self.cuts)])
            pImg = self.draw_vat_image(vData[1], "_normals"+ meta, [int(self.vertices / self.cuts), int(self.frameCount * self.cuts)])
        else:
            vData = self.get_anim_vertex_data(1, vatObjs, scale)

            pImg = self.draw_vat_image(vData[0], "_position"+ meta, [self.vertices, self.frameCount])
            context.scene.vat.progress = .7
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP')
            self.draw_vat_image(vData[1], "_normals"+ meta, [self.vertices, self.frameCount])
            context.scene.vat.progress = .85
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP')
        
        if pImg != None:
            self.show_image(pImg)
        
        #export VAT mesh
        self.uvProgress = 0
        self.export_mesh(vatObjs)
        context.scene.vat.progress = 1
        bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP')
        
    
    def execute_meshFrames(self, context):
        #for meshobjects
        fObjs = bpy.data.collections["Frames"].objects
        self.frameCount = len(fObjs)
        fObjs = self.get_applied_frame_objects(fObjs)
        
        scale = self.calc_ratio(fObjs)

        pImg = None

        if context.scene.vat.isFolded:
            l = len(fObjs[-1].data.vertices)
            w = len(fObjs)
            aspectRatio = math.floor(math.log2(math.sqrt(l/w)))
            self.cuts = pow(2,aspectRatio)
            vData = self.get_obj_vertex_data(self.cuts, fObjs, scale)

            pImg = self.draw_vat_image(vData[0], "_position", [int(l / self.cuts), int(w * self.cuts)])
            self.draw_vat_image(vData[1], "_normals", [int(l / self.cuts), int(w * self.cuts)])
        else:
            self.cuts = 1
            vData = self.get_obj_vertex_data(1, fObjs, scale)

            pImg = self.draw_vat_image(vData[0], "_position", [len(fObjs[-1].data.vertices), len(fObjs)])
            self.draw_vat_image(vData[1], "_normals", [len(fObjs[-1].data.vertices), len(fObjs)])

        if pImg != None:
            self.show_image(pImg)
        
        self.export_mesh(context.scene.vat.exportObj)

    def draw_vat_image(self, pixels, name, size):
        #Set filepath
        if bpy.context.scene.vat.outputDir != "":
            fPath = bpy.path.abspath(bpy.context.scene.vat.outputDir)
            fPath += name + ".png"
        else: 
            
            fPath = bpy.app.tempdir + "temp.png"

        #create new image
        image = bpy.data.images.new(bpy.path.basename(fPath), width = size[0], height = size[1], float_buffer=True, is_data=True)
        image.colorspace_settings
        print(len(image.pixels))
        print(len(pixels))
        image.pixels = pixels

        #print(pixels)
        #save to disc if not temp
        if fPath != bpy.app.tempdir + "temp.png":
            image.save_render(fPath, scene=bpy.context.scene, quality=100)

        print(fPath + " | " + str(size[0]) + ", " + str(size[1]))
        image.update()
        return image
    
    def export_mesh(self, objs, f = 0):
        bpy.context.scene.frame_set(f)

        active = bpy.context.active_object
        bpy.ops.object.select_all(action = 'DESELECT')

        if bpy.context.scene.vat.exportExtras != None:
            for co in bpy.context.scene.vat.exportExtras.objects:
                if co != active:
                    co.select_set(True)

        exportObjs = list()

        for obj in objs:
            dupe = obj.copy()   
            dupe.data = obj.data.copy()
            dupe.animation_data_clear()

            bpy.context.collection.objects.link(dupe)
            dupe.select_set(True)
            exportObjs.append(dupe)
            #for m in (dupe.modifiers):
            #    bpy.ops.object.modifier_apply(modifier = m.name)
            
            self.generate_vat_uv(dupe, self.cuts, self.frameCount)
        
        bpy.context.view_layer.objects.active = exportObjs[0]
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        bpy.ops.object.join()

        fPath = bpy.path.abspath(bpy.context.scene.vat.outputDir)

        if bpy.context.scene.vat.exportType == "fbx":
            fPath = fPath + ".fbx"
            bpy.ops.export_scene.fbx(use_selection = True, filepath = fPath, use_mesh_modifiers = True)
        elif bpy.context.scene.vat.exportType == "gltf":
            fPath += ".gltf"
            bpy.ops.export_scene.gltf(use_selection = True, filepath = fPath, export_apply = True)
        
        if bpy.context.scene.vat.deleteExportMesh:
                bpy.data.objects.remove(bpy.context.active_object, do_unlink = True)

    def generate_vat_uv(self, obj, splits, height):
        if self.cuts == None or self.frameCount == 0:
            print("error, no frame count or cut count")
            return
        
        if bpy.context.scene.vat.genBaseUV:
            bpy.context.view_layer.objects.active = obj
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.uv.cube_project()
            bpy.ops.object.mode_set(mode='OBJECT')
        
        #VAT UV
        bm = bmesh.new()
        bm.from_mesh(obj.data)

        bm.loops.layers.uv  
        uv_layer = bm.loops.layers.uv.new("UVMap2")

        pixel_size = 1.0 / self.vertices * splits

        if splits == 1: 
            section = self.vertices
        else:
            section = self.vertices#round(len(bm.verts)/splits)
        
        x = self.uvProgress
        for v in bm.verts:
            for l in v.link_loops:
                uv_data = l[uv_layer]
                uv_data.uv = mathutils.Vector((x * pixel_size + (pixel_size * .5), 0.0))
            x += 1

        self.uvProgress = x

        bm.to_mesh(obj.data)
        bm.free()
    
    def split_uv(self):
        for f in range(splits):
                s = f * section
                e = f * section + section
                for v in bm.verts[s:e]:
                    for l in v.link_loops:
                        uv_data = l[uv_layer]
                        uv_data.uv = mathutils.Vector((x * pixel_size + (pixel_size * .5), y * pixel_size))
                    x += 1
                x = 0
                y = (f + 1) * height

    def get_anim_vertex_data(self, splits, objs, ratio):
        posData = list()
        normData = list()

        sLength = self.vertices/splits

        #get obj vertex info
        objInfo = []
        for i, obj in enumerate(objs):
            dg = bpy.context.view_layer.depsgraph
            evalObj = obj.evaluated_get(dg)
            objInfo.append([i,len(evalObj.data.vertices)])

        print(objInfo)
        for f in range(splits):
            for frame in range(self.frameCount):
                bpy.data.scenes['Scene'].frame_set(frame + bpy.context.scene.frame_start)

                lengthTracker = sLength
                
                for o, oInfo in enumerate(objInfo):
                    #get eval obj
                    dg = bpy.context.view_layer.depsgraph
                    evalObj = objs[oInfo[0]].evaluated_get(dg)

                    mb = evalObj.matrix_world
                    ob = evalObj.rotation_euler.to_matrix()
                    
                    v = evalObj.data.vertices
                    vLen = len(v)

                    if objInfo[o][1] < vLen:
                        v = v[int(vLen-objInfo[o][1]):]

                    if objInfo[o][1] > lengthTracker:
                        v = v[:int(lengthTracker)]
                        lengthTracker = 0
                    else:
                        lengthTracker -= objInfo[o][1]

                    for vert in v:
                        index = vert.index
                        if bpy.context.scene.vat.worldPos == True:
                            pos = self.unsign_vector((mb @ evalObj.data.vertices[index].co.copy())/ratio)
                        else:
                            pos = self.unsign_vector(evalObj.data.vertices[index].co.copy()/ratio)
                        pos.append(1.0)
                        posData += pos
                        
                        if bpy.context.scene.vat.worldPos == True:
                            #norm = self.unsign_vector(ob @ vert.normal.copy())
                            #norm = self.unsign_vector(evalObj.matrix_world @ vert.normal.copy())
                            norm = self.unsign_vector(evalObj.matrix_world.inverted_safe().transposed().to_3x3() @ vert.normal.copy())
                        else:
                            norm = self.unsign_vector(vert.normal.copy())
                        norm.append(1.0)
                        normData += norm
                    
                    if lengthTracker <= 0: break

            finVerts = sLength
            while finVerts != 0:
                finVerts = objInfo[0][1] - finVerts
                if finVerts > 0:
                    objInfo[0][1] = finVerts
                    finVerts = 0
                elif finVerts < 0:
                    finVerts = abs(finVerts)
                    objInfo.pop(0)
                elif finVerts == 0:
                    objInfo.pop(0)
            print(objInfo)

            bpy.context.scene.vat.progress += .4/splits
            bpy.ops.wm.redraw_timer(type='DRAW_WIN_SWAP')

        return [posData, normData]

    def get_obj_vertex_data(self, splits, fObjs, ratio):

        posData = list()
        normData = list()

        for f in range(splits):
            for obj in fObjs:
                v = obj.data.vertices
                section = len(v)/splits

                s = round(section * f)
                e = round(section * f + section)

                for vert in v[s:e]:
                    pos = self.unsign_vector(vert.co.copy()/ratio)
                    pos.append(1.0)
                    posData += pos

                    norm = self.unsign_vector(vert.normal.copy())
                    norm.append(1.0)
                    normData += norm
    
        return [posData, normData]

    def get_applied_frame_objects(self, fObjs):
        objs = []
        deps = bpy.context.evaluated_depsgraph_get()
        for obj in fObjs:
            objs.append(obj.evaluated_get(deps))
        
        return objs

    def calc_ratio(self, objs = None):
        #to be implemented: provide temporary rectangle for ratio calculation
        largest = 1.0

        for o in objs:
            for d in o.dimensions:
                if d > largest:
                    largest = d
        
        largest = math.ceil(largest)
        print(largest)
        return largest
    
    def unsign_vector(self, vec, as_list = True):
        #Convert (-1,1) to (0,1)
        vec += mathutils.Vector((1., 1., 1.))
        vec /= 2.

        if as_list:
            return list(vec.to_tuple())
        else:
            return vec

    def show_image(self, image):
        if bpy.context.scene.vat.popup:
            bpy.ops.render.view_show("INVOKE_DEFAULT")

        for area in bpy.context.screen.areas:
            if area.type == 'IMAGE_EDITOR':
                area.spaces.active.image = image

                
    
