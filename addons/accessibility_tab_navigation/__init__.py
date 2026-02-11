bl_info = {
    "name": "Workspace Navigation Menu",
    "author": "Ton Nom",
    "version": (1, 1, 0),
    "blender": (3, 0, 0),
    "category": "Accessibility",
    "description": "Open a menu to navigate between Blender workspaces/layouts, including Sculpting",
}

import bpy

# --------------------------------------------------
# Operator: switch to selected workspace
# --------------------------------------------------
class ACCESS_OT_switch_workspace(bpy.types.Operator):
    bl_idname = "access.switch_workspace"
    bl_label = "Switch Workspace"

    workspace_name: bpy.props.StringProperty()

    def execute(self, context):
        if self.workspace_name in bpy.data.workspaces:
            # 🔹 Spécial pour Sculpting : s'assurer qu'un objet MESH est actif
            if self.workspace_name == "Sculpting":
                if context.object is None or context.object.type != 'MESH':
                    mesh_obj = next((o for o in context.scene.objects if o.type == 'MESH'), None)
                    if mesh_obj:
                        context.view_layer.objects.active = mesh_obj
                        mesh_obj.select_set(True)

            # Changer de workspace
            context.window.workspace = bpy.data.workspaces[self.workspace_name]
            self.report({'INFO'}, f"Switched to {self.workspace_name}")
            return {'FINISHED'}
        else:
            self.report({'WARNING'}, f"Workspace {self.workspace_name} not found")
            return {'CANCELLED'}

# --------------------------------------------------
# Menu: list all workspaces
# --------------------------------------------------
class ACCESS_MT_workspace_menu(bpy.types.Menu):
    bl_label = "Select Workspace"
    bl_idname = "ACCESS_MT_workspace_menu"

    def draw(self, context):
        layout = self.layout
        for ws in bpy.data.workspaces:
            op = layout.operator(
                "access.switch_workspace",
                text=ws.name,
                icon='WINDOW'
            )
            op.workspace_name = ws.name

# --------------------------------------------------
# Operator: open workspace menu
# --------------------------------------------------
class ACCESS_OT_open_workspace_menu(bpy.types.Operator):
    bl_idname = "access.open_workspace_menu"
    bl_label = "Open Workspace Menu"

    def execute(self, context):
        bpy.ops.wm.call_menu(name="ACCESS_MT_workspace_menu")
        return {'FINISHED'}

# --------------------------------------------------
# Keymap
# --------------------------------------------------
addon_keymaps = []

def register_keymaps():
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if not kc:
        return

    km = kc.keymaps.new(name="Screen", space_type='EMPTY')

    # CTRL + W ouvre le menu des workspaces
    kmi = km.keymap_items.new(
        "access.open_workspace_menu",
        type='W',
        value='PRESS',
        ctrl=True
    )

    addon_keymaps.append((km, kmi))

def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

# --------------------------------------------------
# Register / Unregister
# --------------------------------------------------
classes = (
    ACCESS_OT_switch_workspace,
    ACCESS_MT_workspace_menu,
    ACCESS_OT_open_workspace_menu,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_keymaps()

def unregister():
    unregister_keymaps()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
