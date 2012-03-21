# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****


###ADDON INFOS

bl_info = {
    "name": "BatchBake-dirtmap",
    "description": "script to bake AO-Dirtmap for a group of objects",
    "author": "Nicolò Zubbini",
    "version": (0,1),
    "blender": (2, 61,4),
    "location": "Properties > Render > BatchBake",
    "warning": "test-only, unstable, dangerous, use at your own risk !!", 
    "wiki_url": "http://wiki.blender.org/index.php/Extensions:2.5/Py/"
                "Scripts/My_Script",
    "tracker_url": "http://projects.blender.org/tracker/index.php?"
                   "func=detail&aid=<number>",
    "category": "Render"}



import bpy
import os
from bpy.props import *


######################################################
# PROPERTIES
## RENDERSCENE PROPERTIES

bpy.types.Scene.BBbakegroup = bpy.props.StringProperty( name="bake group",default='Group', description = " group containing objects to bake")  

bpy.types.Scene.BBuvmap = bpy.props.StringProperty( name="bake UVmap",default='dirtmap', description = "UVmap for bake")  

bpy.types.Scene.BBautouv = bpy.props.BoolProperty( name="Auto unwrap",default=True, description = "use auto lscm unwrap or set uvmap manually")  


bpy.types.Scene.BBAOdist = bpy.props.FloatProperty( name="AO R",default=1.5, description = "radius for concave/dark areas")  
bpy.types.Scene.BBAOInvdist = bpy.props.FloatProperty(name="Inv.AO R",default=0.1, description = "radius for edges/bright areas")  
bpy.types.Scene.BBCont = bpy.props.FloatProperty(name="AO contrast",default=1.25, description = "contrast for final dirtmap")  


class BBrendersize (bpy.types.PropertyGroup):
    res_x = bpy.props.IntProperty(name="res.x", default=512)
    res_y = bpy.props.IntProperty(name="res.y", default=512)

bpy.utils.register_class(BBrendersize)



bpy.types.Scene.BBres_x = bpy.props.IntProperty( name="X res.",default=1024, description = " X resolutioin for batch bake image")  
bpy.types.Scene.BBres_y = bpy.props.IntProperty( name="Y res.",default=1024, description = "Y resolutioin for batch bake image")  





######################################################
## OPERATORS

class BBtempjoin_go (bpy.types.Operator):

    bl_idname = "bpt.bb_tempjoin_go_op"
    bl_label = "temp join create obj"

    def execute(self,context):
        
        objlist= bpy.context.selected_objects
        
#        bpy.ops.object.select_pattern(extend=False, pattern='TJ_TempObject' , case_sensitive=True) 
#        bpy.ops.object.delete()
        
                        
        for obj in bpy.context.selected_objects:
         
            if ('TJ_'+obj.name) not in obj.vertex_groups.keys():
                vgroup=obj.vertex_groups.new(name=('TJ_'+obj.name))
       
            for vert in range(len(obj.data.vertices)):
                obj.vertex_groups[('TJ_'+obj.name)].add(index=[vert],weight=1,type='REPLACE') 

        bpy.ops.object.duplicate()
        
## clear rotations         
        
        bpy.ops.object.rotation_clear()
        bpy.ops.object.scale_clear()

        
        bpy.ops.object.join()
        bpy.context.selected_objects[0].name = 'TJ_TempObject'

###     
###          
                   
        return {'FINISHED'}

class BBtempjoin_apply (bpy.types.Operator):

    bl_idname = "bpt.bb_tempjoin_apply_op"
    bl_label = "temp join apply uvs"

    def execute(self,context):


### run in 3Dview area (?)

        original_type = bpy.context.area.type
        bpy.context.area.type = 'VIEW_3D'

        
        bpy.ops.object.select_all(action='DESELECT')
        bpy.ops.object.select_pattern(extend=False, pattern='TJ_TempObject' , case_sensitive=True)
        bpy.context.scene.objects.active = bpy.data.objects['TJ_TempObject'] 


## for vertexgroup
        vertgroups=[]
        for id in range(len(bpy.context.selected_objects[0].vertex_groups)):
            if bpy.context.selected_objects[0].vertex_groups[id].name.startswith('TJ'):
                vertgroups.append(bpy.context.selected_objects[0].vertex_groups[id])
            else:
                pass
        for vertgroup in vertgroups:
            
            bpy.ops.object.select_all(action='DESELECT')

            bpy.ops.object.select_pattern(extend=False, pattern='TJ_TempObject' , case_sensitive=True) 
            bpy.context.scene.objects.active = bpy.data.objects['TJ_TempObject']
         
        
#### select faces
            
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_all(action='DESELECT')


            bpy.ops.object.vertex_group_set_active(group=vertgroup.name)
            print(vertgroup)
            print(bpy.context.selected_objects[0].vertex_groups.active)

            bpy.ops.object.vertex_group_select()

#### detach 
            print(bpy.context.selected_objects[0])
            bpy.ops.mesh.separate(type='SELECTED')

            bpy.ops.object.mode_set(mode='OBJECT')


        for id in range(len(vertgroups)):
            
            origOB= (vertgroups[id].name)[3:]
            newOB=  'TJ_TempObject.'+str(id+1).zfill(3)
            print(origOB)
            print(newOB)

##### set detached origin as in original

            bpy.context.scene.objects.active = bpy.data.objects[origOB]
            bpy.ops.view3d.snap_cursor_to_active()

            bpy.ops.object.select_all(action='DESELECT')

            bpy.ops.object.select_pattern(extend=False, pattern= newOB, case_sensitive=True) 
            bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
#
#
##### apply new data to original object
#
            bpy.data.objects[origOB].data=bpy.data.objects[newOB].data

        bpy.context.area.type = original_type

### cleanup 
###  delete temp join detached part
###  delete temp join obj
        for object in bpy.data.objects:
            if object.name.startswith('TJ_TempObject'):
                print (object.name)
                bpy.ops.object.select_pattern(extend=False, pattern= object.name, case_sensitive=True)                
                bpy.ops.object.delete()
                
        return {'FINISHED'}




class BBmakecompmat (bpy.types.Operator):

    bl_idname = "bpt.bb_make_compmat_op"
    bl_label = "create compAO mat"

    def execute(self,context):
        
        bakegroup = bpy.context.scene.BBbakegroup
        img0name= str((bakegroup)+'_'+('AO2'))
        img1name= str((bakegroup)+'_'+('AO'))
        img2name= str((bakegroup)+'_'+('AOInv'))
        
        
        if (bakegroup+'_AOComp') in [bpy.data.materials.keys]:
            mat= bpy.data.materials[bakegroup+'_AOComp']
        else:
            mat = bpy.data.materials.new(bakegroup+'_AOComp')

        mat.use_shadeless = True
        mat.diffuse_color = (0.55,0.55,0.55)
        for slot in range(9):
            mat.texture_slots.clear(index=slot)

        for img in [img1name,img2name,img0name]:
            if img not in bpy.data.textures.keys():
                cTex = bpy.data.textures.new((img),type = 'IMAGE')
            mtex = mat.texture_slots.add()
            cTex = bpy.data.textures[img]
            cTex.image = bpy.data.images[img]
            mtex.texture = cTex
            mtex.texture_coords = 'UV'
            mtex.mapping = 'FLAT'
            mtex.use_map_color_diffuse = True  
                            
            if img.endswith('AO'):
                mtex.blend_type = 'MULTIPLY'
                mtex.diffuse_color_factor = bpy.context.scene.BBCont  
            
            if img.endswith('AOInv'):
                mtex.blend_type = 'ADD'
                mtex.invert = True
                mtex.diffuse_color_factor = (bpy.context.scene.BBCont)*1.35  
            if img.endswith('AO2'):
                mtex.blend_type = 'MULTIPLY'
                mtex.diffuse_color_factor = (bpy.context.scene.BBCont)*1.1  

                    
        return {'FINISHED'}



class BBflipoperator(bpy.types.Operator):
    
    bl_idname = "bpt.bb_flip_op"
    bl_label = "flip all normals"

    def execute(self,context):
        bakegroup = bpy.context.scene.BBbakegroup

        original_type = bpy.context.area.type
        bpy.context.area.type = "VIEW_3D"
        
        for bakeobj in bpy.data.groups[(bakegroup)].objects :       
            bpy.context.scene.objects.active = bakeobj
            bpy.ops.object.editmode_toggle()
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.flip_normals()
            bpy.ops.object.editmode_toggle()

        bpy.context.area.type = original_type

        return {'FINISHED'}



# MAIN render bake operator 

class BBmainoperator(bpy.types.Operator):

    bl_idname = "bpt.bb_op"
    bl_label = "Run Batch unwrap and bake"

    def execute(self,context):

        bakegroup = bpy.context.scene.BBbakegroup
        
        AOdist = bpy.context.scene.BBAOdist
        AOInvdist = bpy.context.scene.BBAOInvdist

        uvmap= bpy.context.scene.BBuvmap
        
        img0name= str((bakegroup)+'_'+('AO2'))
        img1name= str((bakegroup)+'_'+('AO'))
        img2name= str((bakegroup)+'_'+('AOInv'))
        img3name= str((bakegroup)+'_'+('DIRT'))


### run from 3d view 
        for area in bpy.context.window.screen.areas: 
            if area.type == 'VIEW_3D': 
                bpy.context.area.spaces.active = area.spaces[0]


### create image by groupname
        if (img1name) not in bpy.data.images :
            bpy.ops.image.new(name=img1name,width=bpy.context.scene.BBres_x,height=bpy.context.scene.BBres_y)

        if (img2name) not in bpy.data.images :
            bpy.ops.image.new(name=img2name,width=bpy.context.scene.BBres_x,height=bpy.context.scene.BBres_y)

        if (img0name) not in bpy.data.images :
            bpy.ops.image.new(name=img0name,width=bpy.context.scene.BBres_x,height=bpy.context.scene.BBres_y)



### create UV layers and assign image
        for bakeobj in bpy.data.groups[(bakegroup)].objects :
            if (uvmap) not in bakeobj.data.uv_textures :
                bakeobj.data.uv_textures.new(name=uvmap)
            bakeobj.data.uv_textures.active = bakeobj.data.uv_textures[uvmap]
            bakeobj.data.uv_textures.active.active_render = True
            for id in range(len(bakeobj.data.uv_textures[uvmap].data)):
                bakeobj.data.uv_textures[uvmap].data[id].image = bpy.data.images[img1name] 

### unwrap
        if bpy.context.scene.BBautouv == True:
                
            bpy.ops.object.select_all(action='DESELECT')
            for bakeobj in bpy.data.groups[(bakegroup)].objects :
                bpy.ops.object.select_pattern(extend=True, pattern=bakeobj.name , case_sensitive=True) 
    
            bpy.ops.uv.smart_project(island_margin=0.01, user_area_weight=0)
    
### bake ao 
##  prep bake settings
        bpy.context.scene.render.use_color_management = False
        bpy.context.scene.render.bake_type = 'AO'
        bpy.context.scene.render.use_bake_clear = False
        bpy.context.scene.render.use_bake_antialiasing = True
        bpy.context.scene.render.use_bake_normalize = True

##  batch bake each object 
        for bakeobj in bpy.data.groups[(bakegroup)].objects :
            bpy.ops.object.select_pattern(extend=False, pattern=bakeobj.name , case_sensitive=True)

##bake AO 1        
            bpy.context.scene.world.light_settings.distance = AOdist
            bpy.ops.object.bake_image()
##bake AO 0
            for id in range(len(bakeobj.data.uv_textures[uvmap].data)):
                bakeobj.data.uv_textures[uvmap].data[id].image = bpy.data.images[img0name] 

            bpy.context.scene.world.light_settings.distance = ((AOdist)*0.25)

            bpy.ops.object.bake_image()


## flip normals
            bpy.ops.bpt.bb_flip_op()
## assign AOInv image and bake 
          
            for id in range(len(bakeobj.data.uv_textures[uvmap].data)):
                bakeobj.data.uv_textures[uvmap].data[id].image = bpy.data.images[img2name] 
            
            bpy.context.scene.world.light_settings.distance = AOInvdist

            print ( 'baking AOInv for object: ' + bakeobj.name )
            bpy.ops.object.bake_image()

            
## flip normals
            bpy.ops.bpt.bb_flip_op()
            
                    
## bake AO and Inv AO together
### material creation        
        bpy.ops.bpt.bb_make_compmat_op()  

### duplicate for final bake        

        bpy.ops.object.select_all(action='DESELECT')
        for bakeobj in bpy.data.groups[(bakegroup)].objects :
            bpy.ops.object.select_pattern(extend=True, pattern=bakeobj.name , case_sensitive=True) 
        bpy.ops.object.duplicate()
        bpy.ops.object.join()

###  assign bake material
        
        ob=bpy.context.selected_objects[0]

        for slot in ob.material_slots:	
            slot.material = bpy.data.materials[(bakegroup+'_AOComp')]
        
###  create and assign new image
        if (img3name) not in bpy.data.images :
            bpy.ops.image.new(name=img3name,width=bpy.context.scene.BBres_x,height=bpy.context.scene.BBres_y)

        for id in range(len(ob.data.uv_textures[uvmap].data)):
           ob.data.uv_textures[uvmap].data[id].image = bpy.data.images[img3name] 

### settings and bake textures                    
        bpy.context.scene.render.bake_type = 'TEXTURE'
        bpy.context.scene.render.use_bake_clear = True
        bpy.ops.object.bake_image()
        bpy.ops.object.delete(use_global=False)
        
### assign final dirt map to group

        for ob in bpy.data.groups[(bakegroup)].objects :
            for id in range(len(ob.data.uv_textures[uvmap].data)):
               ob.data.uv_textures[uvmap].data[id].image = bpy.data.images[img3name] 

        
        print ( 'loop END' )            
        
        
        bpy.context.scene.render.use_color_management=True
        
### done
        return {'FINISHED'}

######################################################
## UI
class RENDER_PT_batchbake(bpy.types.Panel):
    bl_label = "Batch Bake"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "render"
    COMPAT_ENGINES = {'BLENDER_RENDER','CYCLES'}

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        col = row.column()
        split = layout.split()

        col.prop(bpy.context.scene,'BBbakegroup')
        
        sub = col.row(align=False)
        sub.prop(bpy.context.scene,'BBuvmap')
        sub.active = bpy.context.scene.BBautouv == False
        sub.prop(bpy.context.scene,'BBautouv')
        
        sub = col.row(align=True)
        sub.label(text='Resolution:')
        sub.prop(bpy.context.scene,'BBres_x')
        sub.prop(bpy.context.scene,'BBres_y')

        sub = col.row(align=True)
        sub.label(text='Radiuses:')
        sub.prop(bpy.context.scene,'BBAOdist',text='AO')
        sub.prop(bpy.context.scene,'BBAOInvdist',text='Inv.AO')
        sub = col.row(align=True)
        sub.label(text='Contrast:')
        sub.prop(bpy.context.scene,'BBCont',text='')

        
        col.operator("bpt.bb_op")
        layout.split()
        layout.separator()
        sub = col.row(align=True)
        sub.label(text='temp.join selected:')
        if 'TJ_TempObject' in [bpy.context.scene.objects]:
            sub.operator("bpt.bb_tempjoin_apply_op")
        else:
            sub.operator("bpt.bb_tempjoin_go_op",text='Create')
            sub.operator("bpt.bb_tempjoin_apply_op",text='Apply')
    

def register():
    bpy.utils.register_class(RENDER_PT_batchbake)
    bpy.utils.register_class(BBmainoperator)
    bpy.utils.register_class(BBflipoperator)
    bpy.utils.register_class(BBmakecompmat)
    bpy.utils.register_class(BBtempjoin_go)
    bpy.utils.register_class(BBtempjoin_apply)

def unregister():
    bpy.utils.unregister_class(RENDER_PT_batchbake)
    bpy.utils.unregister_class(BBmainoperator)
    bpy.utils.unregister_class(BBflipoperator)
    bpy.utils.unregister_class(BBmakecompmat)
    bpy.utils.unregister_class(BBtempjoin_go)
    bpy.utils.unregister_class(BBtempjoin_apply)
    	
if __name__ == "__main__":
    register()
