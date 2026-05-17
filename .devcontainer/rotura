# Blender Python script to generate fatigue fracture animation
import bpy

# Clean scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

# Add cylinder (bar)
bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2, location=(0,0,0))
bar = bpy.context.object
bar.rotation_euler[1] = 1.57

# Material
mat = bpy.data.materials.new(name="Steel")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs[5].default_value = 1.0
bsdf.inputs[7].default_value = 0.3
bar.data.materials.append(mat)

# Crack sphere
bpy.ops.mesh.primitive_uv_sphere_add(radius=0.02, location=(0.7,0,0))
crack = bpy.context.object
crack.scale = (1,0.3,0.3)

# Boolean modifier
bool_mod = bar.modifiers.new(name="crack", type='BOOLEAN')
bool_mod.object = crack
bool_mod.operation = 'DIFFERENCE'

# Animate crack propagation
crack.keyframe_insert(data_path="scale", frame=1)
crack.scale = (1,3,3)
crack.keyframe_insert(data_path="scale", frame=100)

# Camera
bpy.ops.object.camera_add(location=(2,-2,1))
cam = bpy.context.object
cam.rotation_euler = (1.2,0,0.8)
bpy.context.scene.camera = cam

# Light
bpy.ops.object.light_add(type='AREA', location=(2,0,2))

# End setup
