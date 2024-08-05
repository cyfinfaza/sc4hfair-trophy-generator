import os
import subprocess
import tempfile

class PrusaSlicerError(Exception):
    """Custom exception for PrusaSlicer errors"""
    pass

def slice_stl(stl_path, config_path, output_path=None):
    """
    Slice an STL file using PrusaSlicer.

    :param stl_path: Path to the input STL file
    :param config_path: Path to the PrusaSlicer config file
    :param output_path: Path for the output G-code file. If None, a temporary file will be created.
    :return: Path to the generated G-code file
    :raises PrusaSlicerError: If slicing fails
    """
    if not os.path.exists(stl_path):
        raise FileNotFoundError(f"STL file not found: {stl_path}")
    
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found: {config_path}")

    if output_path is None:
        output_path = tempfile.mktemp(suffix='.gcode')

    try:
        result = subprocess.run(
            ['prusa-slicer', '--export-gcode', '--load', config_path, '--output', output_path, stl_path],
            capture_output=True,
            text=True,
            check=True
        )

        if not os.path.exists(output_path):
            raise PrusaSlicerError("Failed to generate G-code file")

        return output_path

    except subprocess.CalledProcessError as e:
        raise PrusaSlicerError(f"PrusaSlicer error: {e.stderr}")

def cleanup_file(file_path):
    """
    Safely delete a file.

    :param file_path: Path to the file to be deleted
    """
    if os.path.exists(file_path):
        os.unlink(file_path)

# Example usage
if __name__ == "__main__":
    try:
        stl_path = "path/to/your/model.stl"
        config_path = "path/to/your/config.ini"
        gcode_path = slice_stl(stl_path, config_path)
        print(f"G-code generated at: {gcode_path}")
    except (FileNotFoundError, PrusaSlicerError) as e:
        print(f"Error: {e}")
    finally:
        # Cleanup temporary files if needed
        # cleanup_file(gcode_path)
        pass