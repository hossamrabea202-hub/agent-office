# From ChatGPT, passed on by the owner as advice. NOT run by anyone at the office.
# Sizes here are the 300 m targets. The owner wants size relative to our current tentacles: change them.
import bpy
import math
import os
import sys
from mathutils import Vector

# THE ABYSSAL DEVOURER
# Stage A — geometry blockout only
# Run Blender with --factory-startup to protect existing work.

OUT = (
    sys.argv[sys.argv.index("--") + 1]
    if "--" in sys.argv
    else os.path.abspath("Abyssal_Stage_A")
)
os.makedirs(OUT, exist_ok=True)

bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)

scene = bpy.context.scene
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1.0

geo = bpy.data.collections.new("A_BLOCKOUT_GEOMETRY")
setup = bpy.data.collections.new("REVIEW_CAMERAS_LIGHTS")
scene.collection.children.link(geo)
scene.collection.children.link(setup)

def put(obj, collection):
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collection.objects.link(obj)
    return obj

def material(name, color):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.use_nodes = True
    shader = m.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (*color, 1)
    shader.inputs["Roughness"].default_value = 0.85
    return m

body_mat = material("Clay_Body", (0.19, 0.20, 0.22))
arm_mat = material("Clay_Tentacles", (0.26, 0.27, 0.29))
lip_mat = material("Clay_Mouth_Rim", (0.34, 0.30, 0.31))
throat_mat = material("Clay_Throat", (0.045, 0.04, 0.05))
tooth_mat = material("Clay_Teeth_Proxy", (0.60, 0.57, 0.51))

# Central asymmetrical body
bpy.ops.mesh.primitive_uv_sphere_add(
    segments=64, ring_count=32, location=(0, 0, 48)
)
body = put(bpy.context.object, geo)
body.name = "BODY_Central_Mass"
body.data.materials.append(body_mat)

for v in body.data.vertices:
    x, y, z = v.co
    variation = (
        1
        + 0.055 * math.sin(4 * math.atan2(y, x) + 2 * z)
        + 0.035 * math.cos(7 * x + 3 * z)
    )
    v.co = (x * 37 * variation,
            y * 37 * variation,
            z * 44 * variation)

for p in body.data.polygons:
    p.use_smooth = True

# Mouth collar: faces forward along negative Y
mouth_z = 49.0
bpy.ops.mesh.primitive_torus_add(
    major_segments=64,
    minor_segments=16,
    location=(0, -47, mouth_z),
    rotation=(math.pi / 2, 0, 0),
    major_radius=16.5,
    minor_radius=3.3
)
rim = put(bpy.context.object, geo)
rim.name = "MOUTH_Outer_Collar"
rim.data.materials.append(lip_mat)

for p in rim.data.polygons:
    p.use_smooth = True

# Deep funnel-shaped mouth cavity
profiles = [
    (-51, 14.7),
    (-47, 13.8),
    (-42, 11.5),
    (-35, 8.0),
    (-27, 4.0),
    (-20, 0.4)
]

verts = []
faces = []
n = 64

for y, radius in profiles:
    for j in range(n):
        a = 2 * math.pi * j / n
        verts.append((
            radius * math.cos(a),
            y,
            mouth_z + radius * math.sin(a)
        ))

for k in range(len(profiles) - 1):
    for j in range(n):
        a = k * n + j
        b = k * n + (j + 1) % n
        faces.append((a, b, b + n, a + n))

mesh = bpy.data.meshes.new("Mouth_Cavity_Mesh")
mesh.from_pydata(verts, [], faces)
mesh.update()
throat = bpy.data.objects.new("MOUTH_Deep_Cavity", mesh)
geo.objects.link(throat)
throat.data.materials.append(throat_mat)

# Low-resolution placeholder teeth
for j in range(28):
    a = 2 * math.pi * j / 28
    r = 15.0
    base = Vector((
        r * math.cos(a),
        -52.0,
        mouth_z + r * math.sin(a)
    ))
    tip = Vector((
        9.0 * math.cos(a),
        -53.0,
        mouth_z + 9.0 * math.sin(a)
    ))
    direction = (tip - base).normalized()
    midpoint = (base + tip) * 0.5

    bpy.ops.mesh.primitive_cone_add(
        vertices=6,
        radius1=1.25,
        radius2=0.05,
        depth=(tip - base).length,
        location=midpoint
    )
    tooth = put(bpy.context.object, geo)
    tooth.name = f"MOUTH_ToothProxy_{j+1:02}"
    tooth.rotation_euler = direction.to_track_quat(
        "Z", "Y"
    ).to_euler()
    tooth.data.materials.append(tooth_mat)

# Twelve separate tapering tentacle meshes
def tentacle_path(index, t):
    angle = 2 * math.pi * index / 12
    angle -= math.pi / 2
    angle += (
        0.14 * math.sin(math.pi * t)
        * (1 if index % 2 == 0 else -1)
    )
    angle += 0.035 * math.sin(2 * math.pi * t + index)

    distance = 27 + 122 * t
    elevation = 74 + 16 * math.cos(index * 1.7)

    z = (
        32
        + elevation * math.sin(math.pi * t) ** 1.3
        - 19 * t
    )

    return Vector((
        distance * math.cos(angle),
        distance * math.sin(angle),
        z
    ))

def build_tentacle(index):
    rings = 41
    sides = 12
    vertices = []
    polygons = []

    for k in range(rings):
        t = k / (rings - 1)
        center = tentacle_path(index, t)

        t0 = max(0.0, t - 0.005)
        t1 = min(1.0, t + 0.005)
        tangent = (
            tentacle_path(index, t1)
            - tentacle_path(index, t0)
        ).normalized()

        sideways = tangent.cross(Vector((0, 0, 1)))
        sideways.normalize()
        vertical = tangent.cross(sideways).normalized()

        radius = 10.8 * (1 - t) ** 0.75 + 0.3

        for j in range(sides):
            a = 2 * math.pi * j / sides
            point = (
                center
                + radius * math.cos(a) * sideways
                + radius * 0.86 * math.sin(a) * vertical
            )
            vertices.append(tuple(point))

    for k in range(rings - 1):
        for j in range(sides):
            a = k * sides + j
            b = k * sides + (j + 1) % sides
            polygons.append((
                a, b, b + sides, a + sides
            ))

    polygons.append(tuple(reversed(range(sides))))
    last = (rings - 1) * sides
    polygons.append(tuple(last + j for j in range(sides)))

    mesh = bpy.data.meshes.new(
        f"Tentacle_{index+1:02}_Mesh"
    )
    mesh.from_pydata(vertices, [], polygons)
    mesh.update()

    obj = bpy.data.objects.new(
        f"TENTACLE_{index+1:02}", mesh
    )
    geo.objects.link(obj)
    obj.data.materials.append(arm_mat)
    obj["TentacleIndex"] = index + 1
    obj["ProductionStage"] = "A_BLOCKOUT"

    for p in mesh.polygons:
        p.use_smooth = True

    return obj

tentacles = [build_tentacle(i) for i in range(12)]
assert len(tentacles) == 12

# Lighting and orthographic review cameras
world = bpy.data.worlds.new("Preview_World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[
    "Color"
].default_value = (0.12, 0.13, 0.15, 1)

def add_light(name, pos, energy, size):
    data = bpy.data.lights.new(name, "AREA")
    data.energy = energy
    data.shape = "DISK"
    data.size = size
    obj = bpy.data.objects.new(name, data)
    setup.objects.link(obj)
    obj.location = pos
    target = Vector((0, 0, 40))
    obj.rotation_euler = (
        target - obj.location
    ).to_track_quat("-Z", "Y").to_euler()

add_light("Key_Light", (-120, -150, 240), 450000, 160)
add_light("Fill_Light", (130, 40, 160), 240000, 180)

def camera(name, location, target, scale=340):
    data = bpy.data.cameras.new(name)
    data.type = "ORTHO"
    data.ortho_scale = scale
    obj = bpy.data.objects.new(name, data)
    setup.objects.link(obj)
    obj.location = location
    obj.rotation_euler = (
        Vector(target) - obj.location
    ).to_track_quat("-Z", "Y").to_euler()
    return obj

views = {
    "Front": camera(
        "CAM_Front", (0, -430, 65), (0, 0, 52)
    ),
    "Side": camera(
        "CAM_Side", (430, 0, 65), (0, 0, 52)
    ),
    "Back": camera(
        "CAM_Back", (0, 430, 65), (0, 0, 52)
    ),
    "Top": camera(
        "CAM_Top", (0, 0, 450), (0, 0, 0)
    ),
    "ThreeQuarter": camera(
        "CAM_ThreeQuarter",
        (270, -330, 175),
        (0, 0, 47),
        360
    )
}

# Save review outputs
scene.render.resolution_x = 1400
scene.render.resolution_y = 900
scene.render.resolution_percentage = 100
scene.render.film_transparent = True
scene.render.image_settings.file_format = "PNG"

try:
    scene.render.engine = "BLENDER_EEVEE_NEXT"
except Exception:
    scene.render.engine = "BLENDER_EEVEE"

for name, cam in views.items():
    scene.camera = cam
    scene.render.filepath = os.path.join(
        OUT, f"StageA_{name}.png"
    )
    bpy.ops.render.render(write_still=True)

# Export geometry only, excluding preview setup
bpy.ops.object.select_all(action="DESELECT")
for obj in geo.objects:
    if obj.type == "MESH":
        obj.select_set(True)

bpy.ops.export_scene.gltf(
    filepath=os.path.join(
        OUT, "Abyssal_Devourer_Blockout.glb"
    ),
    export_format="GLB",
    use_selection=True,
    export_extras=True
)

scene.camera = views["ThreeQuarter"]
bpy.ops.wm.save_as_mainfile(
    filepath=os.path.join(
        OUT, "Abyssal_Devourer_StageA.blend"
    )
)

print("STAGE A BLOCKOUT GENERATED")
print("Exactly 12 tentacle objects")
print("Output:", OUT)
