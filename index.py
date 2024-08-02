from flask import Flask, send_file, request, render_template
import os
import tempfile
from trophy_generator import edit_blender_texts_and_export_scene
import subprocess

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/generate-trophy', methods=['GET'])
def generate_trophy():
    initials = request.args.get('initials', '')
    if not initials:
        return "No initials provided", 400
    if len(initials) > 3:
        return "Initials cannot be longer than 3 characters", 400

    blend_file = os.path.join(os.path.dirname(__file__), 'trophy-python.blend')
    text_object_name = "initials"
    output_path = os.path.join(tempfile.gettempdir(), 'trophy.stl')

    text_changes = {
        "initials": initials,
    }

    success, message = edit_blender_texts_and_export_scene(
        'blender',  # Blender executable path
        blend_file,
        text_changes,
        output_path
    )

    if success:
        return send_file(output_path, as_attachment=True, download_name=f"trophy_{initials}.stl")
    else:
        return message, 500
    
@app.route('/generate-trophy-double-sided', methods=['GET'])
def generate_trophy_ds():
    initials_1 = request.args.get('initials-1', '')
    initials_2 = request.args.get('initials-2', '')
    
    if not initials_1 or not initials_2:
        return "Both sets of initials are required", 400
    
    if len(initials_1) > 3 or len(initials_2) > 3:
        return "Initials cannot be longer than 3 characters", 400

    blend_file = os.path.join(os.path.dirname(__file__), 'trophy-twosided-python.blend')
    output_path = os.path.join(tempfile.gettempdir(), 'trophy.stl')

    text_changes = {
        "initials-1": initials_1,
        "initials-2": initials_2
    }

    success, message = edit_blender_texts_and_export_scene(
        'blender',  # Blender executable path
        blend_file,
        text_changes,
        output_path
    )

    if success:
        return send_file(output_path, as_attachment=True, download_name=f"trophy_{initials_1}_{initials_2}.stl")
    else:
        return message, 500

@app.route('/slice-stl', methods=['POST'])
def slice_stl():
    # Check if an STL file was uploaded
    if 'file' not in request.files:
        return "No file part", 400
    file = request.files['file']
    if file.filename == '':
        return "No selected file", 400
    if not file.filename.lower().endswith('.stl'):
        return "File must be an STL", 400

    # Create temporary files for input and output
    with tempfile.NamedTemporaryFile(suffix='.stl', delete=False) as temp_stl:
        file.save(temp_stl.name)
        temp_stl_path = temp_stl.name

    temp_gcode_path = tempfile.mktemp(suffix='.gcode')

    # Get the path to config.ini
    config_path = os.path.join(os.path.dirname(__file__), 'config.ini')

    try:
        # Run PrusaSlicer
        result = subprocess.run(
            ['prusa-slicer', '--export-gcode', '--load', config_path, '--output', temp_gcode_path, temp_stl_path],
            capture_output=True,
            text=True,
            check=True
        )

        # Check if the slicing was successful
        if os.path.exists(temp_gcode_path):
            return send_file(temp_gcode_path, as_attachment=True, download_name='sliced_model.gcode')
        else:
            return "Failed to generate G-code", 500

    except subprocess.CalledProcessError as e:
        return f"Error running PrusaSlicer: {e.stderr}", 500

    finally:
        # Clean up temporary files
        if os.path.exists(temp_stl_path):
            os.unlink(temp_stl_path)
        if os.path.exists(temp_gcode_path):
            os.unlink(temp_gcode_path)

if __name__ == '__main__':
    app.run(debug=True)