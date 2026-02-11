bl_info = {
    "name": "Accessible Workspace & View Navigation",
    "author": "Ton Nom",
    "version": (1, 8, 0),
    "blender": (5, 0, 0),
    "category": "Accessibility",
    "description": "Workspace menu + keyboard view navigation (IJKL) and object selection (ALT + arrows)",
}

import bpy
from mathutils import Vector

# ==================================================
# WORKSPACE SWITCH
# ==================================================
class ACCESS_OT_switch_workspace(bpy.types.Operator):
    bl_idname = "access.switch_workspace"
    bl_label = "Switch Workspace"

    workspace_name: bpy.props.StringProperty()

    def execute(self, context):
        ws = bpy.data.workspaces.get(self.workspace_name)
        if ws:
            if self.workspace_name == "Sculpting":
                if context.object is None or context.object.type != 'MESH':
                    mesh = next((o for o in context.scene.objects if o.type == 'MESH'), None)
                    if mesh:
                        context.view_layer.objects.active = mesh
                        mesh.select_set(True)
            context.window.workspace = ws
            self.report({'INFO'}, f"Workspace: {ws.name}")
            return {'FINISHED'}
        return {'CANCELLED'}

class ACCESS_MT_workspace_menu(bpy.types.Menu):
    bl_idname = "ACCESS_MT_workspace_menu"
    bl_label = "Select Workspace"

    def draw(self, context):
        for ws in bpy.data.workspaces:
            op = self.layout.operator("access.switch_workspace", text=ws.name)
            op.workspace_name = ws.name

class ACCESS_OT_open_workspace_menu(bpy.types.Operator):
    bl_idname = "access.open_workspace_menu"
    bl_label = "Open Workspace Menu"

    def execute(self, context):
        bpy.ops.wm.call_menu(name="ACCESS_MT_workspace_menu")
        return {'FINISHED'}

# ==================================================
# VIEW NAVIGATION (IJKL)
# ==================================================
class ACCESS_OT_view_move(bpy.types.Operator):
    bl_idname = "access.view_move"
    bl_label = "Move 3D View"

    direction: bpy.props.StringProperty()  # "UP", "DOWN", "LEFT", "RIGHT"
    step: bpy.props.FloatProperty(default=1.0)

    def execute(self, context):
        area = next((a for a in context.screen.areas if a.type == 'VIEW_3D'), None)
        if not area:
            self.report({'WARNING'}, "No 3D View found")
            return {'CANCELLED'}

        rv3d = area.spaces.active.region_3d
        if not rv3d:
            self.report({'WARNING'}, "No 3D region found")
            return {'CANCELLED'}

        step = self.step

        # Pan en local par rapport à la vue
        view_right = rv3d.view_rotation @ Vector((1, 0, 0))
        view_up = rv3d.view_rotation @ Vector((0, 1, 0))

        if self.direction == 'UP':
            rv3d.view_location += view_up * step
        elif self.direction == 'DOWN':
            rv3d.view_location -= view_up * step
        elif self.direction == 'LEFT':
            rv3d.view_location -= view_right * step
        elif self.direction == 'RIGHT':
            rv3d.view_location += view_right * step

        return {'FINISHED'}

# ==================================================
# OBJECT SELECTION (ALT + flèches)
# ==================================================
class ACCESS_OT_object_cycle(bpy.types.Operator):
    bl_idname = "access.object_cycle"
    bl_label = "Cycle Objects"

    direction: bpy.props.EnumProperty(
        items=[('NEXT', 'Next', ''), ('PREV', 'Previous', '')]
    )

    def execute(self, context):
        objs = [o for o in context.view_layer.objects if o.visible_get()]
        if not objs:
            return {'CANCELLED'}

        active = context.view_layer.objects.active
        if active not in objs:
            target = objs[0]
        else:
            i = objs.index(active)
            target = objs[(i + 1) % len(objs)] if self.direction == 'NEXT' else objs[(i - 1) % len(objs)]

        for o in objs:
            o.select_set(False)

        target.select_set(True)
        context.view_layer.objects.active = target
        self.report({'INFO'}, f"Selected: {target.name}")
        return {'FINISHED'}

# ==================================================
# KEYMAPS
# ==================================================
addon_keymaps = []

def register_keymaps():
    kc = bpy.context.window_manager.keyconfigs.addon
    if not kc:
        return

    # --- SCREEN ---
    km = kc.keymaps.new(name="Screen", space_type='EMPTY')
    kmi = km.keymap_items.new(
        "access.open_workspace_menu", 'W', 'PRESS', ctrl=True
    )
    addon_keymaps.append((km, kmi))

    # --- 3D VIEW ---
    km = kc.keymaps.new(name="3D View", space_type='VIEW_3D')

    # Navigation IJKL
    mapping = {
        'I': 'UP',
        'K': 'DOWN',
        'J': 'LEFT',
        'L': 'RIGHT',
    }
    for key, direction in mapping.items():
        kmi = km.keymap_items.new("access.view_move", key, 'PRESS')
        kmi.properties.direction = direction
        kmi.properties.step = 1.0
        addon_keymaps.append((km, kmi))

    # Sélection objets ALT + flèches
    kmi = km.keymap_items.new("access.object_cycle", 'RIGHT_ARROW', 'PRESS', alt=True)
    kmi.properties.direction = 'NEXT'
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("access.object_cycle", 'LEFT_ARROW', 'PRESS', alt=True)
    kmi.properties.direction = 'PREV'
    addon_keymaps.append((km, kmi))

def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

# ==================================================
# REGISTER
# ==================================================
classes = (
    ACCESS_OT_switch_workspace,
    ACCESS_MT_workspace_menu,
    ACCESS_OT_open_workspace_menu,
    ACCESS_OT_view_move,
    ACCESS_OT_object_cycle,
)

def register():
    for c in classes:
        bpy.utils.register_class(c)
    register_keymaps()

def unregister():
    unregister_keymaps()
    for c in reversed(classes):
        bpy.utils.unregister_class(c)

if __name__ == "__main__":
    register()
