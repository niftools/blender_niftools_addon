"""Export and import bound boxes."""

import bpy
import nose.tools

import io_scene_nif.export_nif
from test import Test

class TestBoundImport(Test):

    def test_import(self):
        bpy.ops.import_scene.nif(
            filepath="test/import/bounding_box.nif",
            log_level='DEBUG',
            )
        
        b_bbox = bpy.data.objects.get("Bounding Box")
        
        # test stuff
        assert(b_bbox.draw_bounds_type == 'BOX')
        assert(b_bbox.draw_type == 'BOUNDS')
        
class TestBoundExport(Test):
    def setup(self):
        
        '''      
        # create a cube
        bpy.ops.mesh.primitive_cube_add()
        self.obj = bpy.data.objects["Cube"]
        self.obj.name = "Bounding Box"
        self.obj.draw_bounds_type = 'BOX'
        self.obj.draw_type = 'BOUNDS'
        self.mesh = self.obj.data
        
        bpy.ops.mesh.primitive_cube_add()
        self.obj = bpy.data.objects["Cube"]
        self.obj.name = "BBoxTest"
        '''
        
        bpy.ops.import_scene.nif(
            filepath="test/import/bounding_box.nif",
            log_level='INFO',
            )
        bpy.ops.object.select_name(name="Bounding Box")
        
    def test_export(self):
        # export   
        bpy.ops.export_scene.nif(
            filepath="test/export/bounding_box.nif",
            log_level='DEBUG',
            )
        
        '''
        self.obj = bpy.data.objects["Bounding Box"]
        self.mesh = self.obj.data
        
        # test stuff...
        bbox = nif_export.root_blocks[0].children[0]
        assert(bbox.has_bounding_box) 
        '''
    
        
class TestBSBoundImport(Test):
    def test_import(self):
        bpy.ops.import_scene.nif(
            filepath="test/import/bounding_box_bsbound.nif",
            log_level='DEBUG',
            )
