import os
import subprocess
import tempfile

def edit_blender_texts_and_export_scene(blender_path, blend_file, text_changes, output_path):
    # Create a temporary Blender Python script
    blender_script = f'''
import bpy
import os

def edit_texts_and_export_scene_stl(text_changes, output_path):
    success = True
    for obj_name, new_text in text_changes.items():
        text_obj = bpy.data.objects.get(obj_name)
        if text_obj is None or text_obj.type != 'FONT':
            print(f"Error: Text object '{{obj_name}}' not found or not a text object.")
            success = False
        else:
            text_obj.data.body = new_text
    
    if not success:
        return False
    
    # Deselect all objects
    bpy.ops.object.select_all(action='DESELECT')
    
    # Select all objects in the scene
    for obj in bpy.context.scene.objects:
        obj.select_set(True)
    
    # Export the entire scene as STL
    bpy.ops.export_mesh.stl(
        filepath=output_path,
        use_selection=True,
        global_scale=1.0,
        use_scene_unit=False,
        ascii=False,
        use_mesh_modifiers=True
    )
    
    print(f"Scene exported as STL to: {{output_path}}")
    return True

# Run the function with provided arguments
text_changes = {text_changes}
result = edit_texts_and_export_scene_stl(text_changes, r"{output_path}")
if result:
    print("SUCCESS")
else:
    print("FAILED")
'''

    # Create a temporary file to store the Blender script
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_script:
        temp_script.write(blender_script)
        temp_script_path = temp_script.name

    try:
        # Run Blender with the script
        result = subprocess.run(
            [blender_path, blend_file, '--background', '--python', temp_script_path],
            capture_output=True,
            text=True,
            check=True
        )

        # Check if the export was successful
        if "SUCCESS" in result.stdout:
            return True, "Scene exported successfully"
        else:
            print(result.stdout)
            return False, "Failed to export scene"

    except subprocess.CalledProcessError as e:
        return False, f"Error running Blender: {e.stderr}"

    finally:
        # Clean up the temporary script
        os.unlink(temp_script_path)

# Example usage
if __name__ == "__main__":
    blender_path = "blender"
    blend_file = "trophy-python.blend"
    text_changes = {
        "initials-1": "ABC",
        "initials-2": "XYZ"
    }
    output_path = "output.stl"

    success, message = edit_blender_texts_and_export_scene(
        blender_path, blend_file, text_changes, output_path
    )
    print(f"{'Success' if success else 'Failure'}: {message}")