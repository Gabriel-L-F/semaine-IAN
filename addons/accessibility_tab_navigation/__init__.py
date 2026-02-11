bl_info = {
    "name": "Ultimate Accessible Workspace & Navigation",
    "author": "Adapté par Gemini",
    "version": (2, 0, 0),
    "blender": (5, 0, 0),
    "category": "Accessibility",
    "description": "Navigation IJKL, TTS pour Workspaces, Cycle d'objets et déplacement précis.",
}

import bpy
import platform
import subprocess
import threading
from mathutils import Vector

# ==================================================
# MOTEUR TTS ET TRADUCTION
# ==================================================
WS_TRANSLATION = {
    "Layout": "Mise en page",
    "Modeling": "Modélisation",
    "Sculpting": "Sculpture",
    "UV Editing": "Édition UV",
    "Texture Paint": "Peinture de texture",
    "Shading": "Ombrage",
    "Animation": "Animation",
    "Rendering": "Rendu",
    "Compositing": "Composition",
    "Geometry Nodes": "Noeuds de géométrie",
    "Scripting": "Script"
}

def translate_ws(name):
    return WS_TRANSLATION.get(name, name)

def speak_worker(text):
    system_name = platform.system()
    try:
        if system_name == "Darwin":
            subprocess.run(["say", text])
        elif system_name == "Windows":
            cmd = f'$OutputEncoding = [System.Text.Encoding]::UTF8; Add-Type –AssemblyName System.Speech; (New-Object System.Speech.Synthesis.SpeechSynthesizer).Speak("{text}");'
            subprocess.run(["powershell", "-command", cmd], shell=True)
    except: 
        pass

def speak(text):
    thread = threading.Thread(target=speak_worker, args=(text,))
    thread.start()

# ==================================================
# GESTION DES WORKSPACES (VOCALISÉ)
# ==================================================
class ACCESS_OT_workspace_selector(bpy.types.Operator):
    """Sélecteur accessible : Flèches pour écouter, Entrée pour valider"""
    bl_idname = "access.workspace_selector"
    bl_label = "Choisir l'espace de travail"
    bl_property = "my_search"

    def get_ws_items(self, context):
        return [(ws.name, translate_ws(ws.name), "") for ws in bpy.data.workspaces]

    my_search: bpy.props.EnumProperty(items=get_ws_items)

    def check(self, context):
        speak(translate_ws(self.my_search))
        return True

    def execute(self, context):
        ws_name = self.my_search
        ws = bpy.data.workspaces.get(ws_name)
        if ws:
            # Logique spécifique au Sculpting du premier code
            if ws_name == "Sculpting":
                if context.object is None or context.object.type != 'MESH':
                    mesh = next((o for o in context.scene.objects if o.type == 'MESH'), None)
                    if mesh:
                        context.view_layer.objects.active = mesh
                        mesh.select_set(True)
            
            context.window.workspace = ws
            speak(f"Espace {translate_ws(ws_name)} activé")
            return {'FINISHED'}
        return {'CANCELLED'}

    def invoke(self, context, event):
        speak("Liste des espaces. Utilisez les flèches.")
        context.window_manager.invoke_search_popup(self)
        return {'RUNNING_MODAL'}

last_ws = ""
def check_workspace_change(scene):
    global last_ws
    if not bpy.context.window: return
    curr_ws = bpy.context.window.workspace.name
    if curr_ws != last_ws:
        if last_ws != "": # Évite de parler au tout premier chargement si souhaité
            speak(f"Espace {translate_ws(curr_ws)}")
        last_ws = curr_ws

# ==================================================
# NAVIGATION ET SELECTION (IJKL / ALT+Flèches)
# ==================================================
class ACCESS_OT_view_move(bpy.types.Operator):
    bl_idname = "access.view_move"
    bl_label = "Déplacer la vue"
    direction: bpy.props.StringProperty() 
    step: bpy.props.FloatProperty(default=1.0)

    def execute(self, context):
        area = next((a for a in context.screen.areas if a.type == 'VIEW_3D'), None)
        if not area: return {'CANCELLED'}
        rv3d = area.spaces.active.region_3d
        
        view_right = rv3d.view_rotation @ Vector((1, 0, 0))
        view_up = rv3d.view_rotation @ Vector((0, 1, 0))

        if self.direction == 'UP': rv3d.view_location += view_up * self.step
        elif self.direction == 'DOWN': rv3d.view_location -= view_up * self.step
        elif self.direction == 'LEFT': rv3d.view_location -= view_right * self.step
        elif self.direction == 'RIGHT': rv3d.view_location += view_right * self.step
        
        return {'FINISHED'}

class ACCESS_OT_object_cycle(bpy.types.Operator):
    bl_idname = "access.object_cycle"
    bl_label = "Cycle Objets"
    direction: bpy.props.EnumProperty(items=[('NEXT', 'Suivant', ''), ('PREV', 'Précédent', '')])

    def execute(self, context):
        objs = [o for o in context.view_layer.objects if o.visible_get()]
        if not objs: return {'CANCELLED'}

        active = context.view_layer.objects.active
        if active not in objs:
            target = objs[0]
        else:
            i = objs.index(active)
            target = objs[(i + 1) % len(objs)] if self.direction == 'NEXT' else objs[(i - 1) % len(objs)]

        for o in objs: o.select_set(False)
        target.select_set(True)
        context.view_layer.objects.active = target
        speak(f"Cible : {target.name}")
        return {'FINISHED'}

# ==================================================
# TRANSFORMATIONS ET STATUS
# ==================================================
class ACCESS_OT_move_object(bpy.types.Operator):
    bl_idname = "access.move_object"
    bl_label = "Déplacer Objet"
    axis: bpy.props.StringProperty()
    amount: bpy.props.FloatProperty()

    def execute(self, context):
        obj = context.active_object
        if obj:
            if self.axis == 'X': obj.location.x += self.amount
            elif self.axis == 'Y': obj.location.y += self.amount
            context.view_layer.update() 
            new_val = getattr(obj.location, self.axis.lower())
            speak(f"{self.axis} {round(new_val, 1)}")
        else:
            speak("Aucun objet sélectionné")
        return {'FINISHED'}

class ACCESS_OT_announce_status(bpy.types.Operator):
    bl_idname = "access.announce_status"
    bl_label = "Annoncer Status"
    def execute(self, context):
        obj = context.active_object
        if obj:
            speak(f"Objet {obj.name}. X {round(obj.location.x,1)}, Y {round(obj.location.y,1)}")
        else:
            speak("Rien n'est sélectionné")
        return {'FINISHED'}

# ==================================================
# ENREGISTREMENT ET RACCOURCIS
# ==================================================
classes = (
    ACCESS_OT_workspace_selector,
    ACCESS_OT_view_move,
    ACCESS_OT_object_cycle,
    ACCESS_OT_move_object,
    ACCESS_OT_announce_status,
)

addon_keymaps = []

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    
    # Handler pour surveiller les changements de workspace
    if check_workspace_change not in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.append(check_workspace_change)

    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        # --- KEYMAP GLOBALE (SCREEN/WINDOW) ---
        km_screen = kc.keymaps.new(name="Screen", space_type='EMPTY')
        
        # CTRL + W : Sélecteur vocal
        kmi = km_screen.keymap_items.new("access.workspace_selector", 'W', 'PRESS', ctrl=True)
        addon_keymaps.append((km_screen, kmi))
        
        # F5 : Annonce Status
        kmi = km_screen.keymap_items.new("access.announce_status", 'F5', 'PRESS')
        addon_keymaps.append((km_screen, kmi))

        # --- KEYMAP 3D VIEW ---
        km_3d = kc.keymaps.new(name="3D View", space_type='VIEW_3D')

        # IJKL Navigation
        nav_map = {'I': 'UP', 'K': 'DOWN', 'J': 'LEFT', 'L': 'RIGHT'}
        for key, direct in nav_map.items():
            kmi = km_3d.keymap_items.new("access.view_move", key, 'PRESS')
            kmi.properties.direction = direct
            addon_keymaps.append((km_3d, kmi))

        # ALT + Flèches : Cycle Objets
        kmi = km_3d.keymap_items.new("access.object_cycle", 'RIGHT_ARROW', 'PRESS', alt=True)
        kmi.properties.direction = 'NEXT'
        addon_keymaps.append((km_3d, kmi))
        kmi = km_3d.keymap_items.new("access.object_cycle", 'LEFT_ARROW', 'PRESS', alt=True)
        kmi.properties.direction = 'PREV'
        addon_keymaps.append((km_3d, kmi))

        # CTRL + Flèches : Déplacement objet précis
        mvs = [('RIGHT_ARROW','X',1.0), ('LEFT_ARROW','X',-1.0), ('UP_ARROW','Y',1.0), ('DOWN_ARROW','Y',-1.0)]
        for k, a, v in mvs:
            kmi = km_3d.keymap_items.new("access.move_object", k, 'PRESS', ctrl=True, head=True)
            kmi.properties.axis = a
            kmi.properties.amount = v
            addon_keymaps.append((km_3d, kmi))

    speak("Système d'accessibilité prêt.")

def unregister():
    if check_workspace_change in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(check_workspace_change)
    
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()

    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()