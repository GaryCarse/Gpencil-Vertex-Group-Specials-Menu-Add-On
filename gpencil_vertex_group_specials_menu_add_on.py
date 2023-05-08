bl_info = {
    "name": "Gpencil Vertex Group Specials Menu",
    "author": "Gary Carse",
    "version": (1, 0),
    "blender": (3, 5, 0),
    "location": "Properties > Object Data Properties > Vertex Groups",
    "description": "Adds the Vertex Group Specials Menu to the Gpencil Vertex Groups panel",
}


import bpy
from bpy.types import Menu, Panel, UIList, Operator
from bpy.props import BoolProperty
from rna_prop_ui import PropertyPanel
from bl_ui.properties_data_gpencil import DATA_PT_gpencil_vertex_groups


class ObjectButtonsPanel:
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return ob and ob.type == 'GPENCIL'



class DATA_PT_gpencil_vertex_groups_extended(ObjectButtonsPanel, Panel):
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
        
        col.menu("GP_MT_vertex_group_context_menu", icon='DOWNARROW_HLT', text="")  #Custom menu
       
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
#This menu is copied from the object vertex group context menu with custom operators replacing some of the object ops that aren't compatible with Grease Pencil.
class GP_MT_vertex_group_context_menu(Menu):
    bl_label = "Vertex Group Specials"
    bl_idname = "GP_MT_vertex_group_context_menu"

    def draw(self, context):
        layout = self.layout

        layout.operator(
            "object.vertex_group_sort",
            icon='SORTALPHA',
            text="Sort by Name",
        ).sort_type = 'NAME'
        layout.operator(
            "object.vertex_group_sort",
            icon='BONE_DATA',
            text="Sort by Bone Hierarchy",
        ).sort_type = 'BONE_HIERARCHY'
        layout.separator()
        layout.operator("object.vertex_group_copy", icon='DUPLICATE')
        layout.operator("object.vertex_group_copy_to_selected")
        layout.separator()
        layout.operator("object.vertex_group_mirror", icon='ARROW_LEFTRIGHT').use_topology = False
        layout.operator("object.vertex_group_mirror", text="Mirror Vertex Group (Topology)").use_topology = True
        layout.separator()
        #Custom Ops START
        layout.operator("gpencil.vertex_group_remove_from_extended", icon='X', text="Remove from All Groups").use_all_groups = True
        layout.operator("gpencil.vertex_group_remove_from_extended", text="Clear Active Group").use_all_points = True
        #Custom Ops END
        layout.operator("object.vertex_group_remove", text="Delete All Unlocked Groups").all_unlocked = True
        layout.operator("object.vertex_group_remove", text="Delete All Groups").all = True
        layout.separator()
        props = layout.operator("object.vertex_group_lock", icon='LOCKED', text="Lock All")
        props.action, props.mask = 'LOCK', 'ALL'
        props = layout.operator("object.vertex_group_lock", icon='UNLOCKED', text="Unlock All")
        props.action, props.mask = 'UNLOCK', 'ALL'
        props = layout.operator("object.vertex_group_lock", text="Lock Invert All")
        props.action, props.mask = 'INVERT', 'ALL'

class GP_OP_vertex_group_remove_from_extended(Operator):
    #This appears in the tooltip of the operator and in the generated docs
    bl_idname = "gpencil.vertex_group_remove_from_extended"
    bl_label = "Remove from Vertex Group(s)"
    bl_description = "Remove the selected vertices from active or all vertex group(s)"
    #Should the operation be done on all groups, or just the active group?
    use_all_groups: BoolProperty(
        name="All Groups",
        description="Remove from all groups",
        default=False
    )
    #Should the operation be done on all points, or just the selected points?
    use_all_points: BoolProperty(
        name="All Points",
        description="Clear the active group",
        default=False
    )
    #Should the operation be done on all frames, or just the active frame? If true, it will only work with Multiframe editing enabled and will be run on all frames that are selected.
    #TODO Known issue: Multiframe editing doesn't work with all_points for some reason. So picking the "Clear Active Group" option will only work on the current frame. all_groups works though weirdly
    use_all_frames: BoolProperty(        #All uses of this op in the addon leave this at true. I just put this here to have the option in the future if it's needed.
        name="All Frames",
        description="Remove from all frames. Requires Multiframe editing enabled.",
        default=True
    )

    def execute(self, context):
        obj = bpy.context.view_layer.objects.active
        gp = obj.data
        mode = obj.mode             #Grab the current mode so we can switch back after
        bpy.ops.object.mode_set(mode='EDIT_GPENCIL', toggle=False)
        multiframe = self.use_all_frames and gp.use_multiedit
        frame_indices = set()
        points = []                 #The points to run the operation on
        selected_points = []        #The points that were selected, so we can keep the same points selected after the operation
        for layer in gp.layers:
            if not layer.lock:
                for frame in layer.frames if multiframe else [layer.active_frame]:
                    if not multiframe or frame.select:
                        frame_indices.add(frame.frame_number)
                        for stroke in frame.strokes:
                            for point in stroke.points:
                                if point.select:
                                    selected_points.append(point)
                                    points.append(point)
                                elif self.use_all_points:   #If the point wasn't selected but we're using all points, we need to select them to run the operation
                                    point.select = True;
                                    points.append(point)
        
        active_group = obj.vertex_groups.active             #The original active group so we can revert later
        current_frame = bpy.context.scene.frame_current     #The index of the current frame in blender. Not to be confused with a GP Frame object.
        
        for frame_index in frame_indices:
            bpy.context.scene.frame_set(frame_index)
            for group in obj.vertex_groups if self.use_all_groups else [obj.vertex_groups.active]:
                obj.vertex_groups.active = group
                bpy.ops.gpencil.vertex_group_remove_from()  #Runs on the active group
        #We're done, now change the status of everything back to the way it was before
        bpy.context.scene.frame_set(current_frame)
        obj.vertex_groups.active = active_group
        if self.use_all_points:     #If the operation was done on all points, revert all point selection status' back to their original status
            for point in points:
                point.select = point in selected_points
        
        bpy.ops.object.mode_set(mode=mode, toggle=False)
                
        return {'FINISHED'}

def register():
    try:
        bpy.utils.unregister_class(DATA_PT_gpencil_vertex_groups)
        bpy.utils.register_class(GP_MT_vertex_group_context_menu)
        bpy.utils.register_class(GP_OP_vertex_group_remove_from_extended)
        bpy.utils.register_class(DATA_PT_gpencil_vertex_groups_extended)
    except ValueError:
        pass

def unregister():
    try:
        bpy.utils.unregister_class(GP_MT_vertex_group_context_menu)
        bpy.utils.unregister_class(GP_OP_vertex_group_remove_from_extended)
        bpy.utils.unregister_class(DATA_PT_gpencil_vertex_groups_extended)
        bpy.utils.register_class(DATA_PT_gpencil_vertex_groups)
    except ValueError:
        pass

if __name__ == "__main__":
    register()
    
