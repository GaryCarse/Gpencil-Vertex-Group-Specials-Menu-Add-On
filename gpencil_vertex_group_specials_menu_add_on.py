bl_info = {
    "name": "Gpencil Vertex Group Specials Menu",
    "author": "Gary Carse",
    "version": (1, 0),
    "blender": (3, 5, 0),
    "location": "Properties > Object Data Properties > Vertex Groups",
    "description": "Adds the Vertex Group Specials Menu to the Gpencil Vertex Groups panel",
}


import bpy
from bpy.types import Menu, Panel, UIList
from rna_prop_ui import PropertyPanel

from bl_ui.properties_grease_pencil_common import (
    GreasePencilLayerMasksPanel,
    GreasePencilLayerTransformPanel,
    GreasePencilLayerAdjustmentsPanel,
    GreasePencilLayerRelationsPanel,
    GreasePencilLayerDisplayPanel,
)

class ObjectButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == 'GPENCIL'



class DATA_PT_gpencil_vertex_groups(ObjectButtonsPanel, Panel):
    bl_label = "Vertex Groups"
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        ob = context.object
        group = ob.vertex_groups.active

        rows = 2
        if group:
            rows = 4

        row = layout.row()
        row.template_list("GPENCIL_UL_vgroups", "", ob, "vertex_groups", ob.vertex_groups, "active_index", rows=rows)

        col = row.column(align=True)
        col.operator("object.vertex_group_add", icon='ADD', text="")
        col.operator("object.vertex_group_remove", icon='REMOVE', text="").all = False

        col.separator()
        
        col.menu("MESH_MT_vertex_group_context_menu", icon='DOWNARROW_HLT', text="")
       
        if group:
            col.separator()
            col.operator("object.vertex_group_move", icon='TRIA_UP', text="").direction = 'UP'
            col.operator("object.vertex_group_move", icon='TRIA_DOWN', text="").direction = 'DOWN'

        if ob.vertex_groups:
            row = layout.row()

            sub = row.row(align=True)
            sub.operator("gpencil.vertex_group_assign", text="Assign")
            sub.operator("gpencil.vertex_group_remove_from", text="Remove")

            sub = row.row(align=True)
            sub.operator("gpencil.vertex_group_select", text="Select")
            sub.operator("gpencil.vertex_group_deselect", text="Deselect")

            layout.prop(context.tool_settings, "vertex_group_weight", text="Weight")

def register():
    try:
        bpy.utils.register_class(DATA_PT_gpencil_vertex_groups)
    except ValueError:
        pass

def unregister():
    try:
        bpy.utils.unregister_class(DATA_PT_gpencil_vertex_groups)
    except ValueError:
        pass

if __name__ == "__main__":
    register()
    