from flask import Flask, send_file, request, render_template
import os
import tempfile
from trophy_generator import edit_blender_texts_and_export_scene

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route('/generate-trophy', methods=['GET'])
def generate_trophy():
    initials = request.args.get('initials', '')
    if not initials:
        return "No initials provided", 400

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
    

if __name__ == '__main__':
    app.run(debug=True)