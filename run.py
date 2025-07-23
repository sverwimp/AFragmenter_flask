from flask import Flask, render_template, request, jsonify
from flask_wtf.csrf import CSRFProtect
from afragmenter import AFragmenter, fetch_afdb_data
from afragmenter.structure_displacement import displace_structure
from afragmenter.sequence_reader import _determine_file_format
import numpy as np
import os
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import hashlib

import time
import re

from app import app

from app.form import InputForm

from pprint import pprint as print
import json


def cleanup_generated_files():
    image_dir = os.path.join(app.static_folder, 'images/temp_pae_images')
    twenty_four_hours_ago = time.time() - (24 * 60 * 60)
    hex_pattern = re.compile(r"^[0-9a-f]{40}\.png$")

    for filename in os.listdir(image_dir):
        if hex_pattern.match(filename):
            file_path = os.path.join(image_dir, filename)
            try:
                if os.path.getmtime(file_path) < twenty_four_hours_ago:
                    os.remove(file_path)
                    app.logger.info(f"Removed old generated file: {filename}")
            except Exception as e:
                app.logger.error(f"Error removing file {filename}: {e}")


@app.route("/")
@app.route("/index")
def index():
    form = InputForm()
    return render_template("index.html", form=form)


def process_input():
    form = InputForm()

    if not (request.method == "POST" and form.validate_on_submit()):
        return jsonify({"error": "Form validation failed", "errors": form.errors}), 400
    
    data = {
        'input_type': form.input_type.data,
        'uniprot_id': form.uniprot_id.data,
        'alphafold_json': form.alphafold_json.data,
        'structure_file': form.structure_file.data,
        'pae_threshold': form.pae_threshold.data,
        'resolution': float(form.resolution.data),
        'min_size': form.min_size.data,
        'merge': form.merge.data,
        'objective_function': form.objective_function.data,
        'iterations': form.iterations.data
    }

    try:
        processing_functions = {
            'afdb': process_afdb_input,
            'affiles': process_file_upload
        }

        processing_function = processing_functions.get(data.get('input_type'), None)
        if not processing_function:
            return jsonify({"error": "Invalid input type"}), 400
    
        result = processing_function(data)
        return jsonify(result), 200

    except Exception as e:
        app.logger.error(f"Error processing input: {str(e)}")
        return jsonify({'error': str(e)}), 500


def run_afragmenter(pae_data, pae_threshold, resolution, objective_function, n_iterations, min_size):
    try:
        a = AFragmenter(pae_matrix=pae_data, threshold=pae_threshold)
        afragmenter_result = a.cluster(resolution=resolution, objective_function=objective_function, n_iterations=n_iterations, min_size=min_size)
        return afragmenter_result
    except Exception as e:
        return {'error': str(e)}
    

def format_return_data(cluster_intervals, structure, structure_format, pae_plot_path):
    #structure_displaced = displace_structure(structure, cluster_intervals, structure_format)
    return {
        'success': True, 
        'data': {
            'cluster_intervals': cluster_intervals,
            'structure': structure,
            'structure_format': structure_format,
            'pae_plot_path': pae_plot_path
            #'structure_displaced': structure_displaced
        },
        
    }


def process_afdb_input(data: dict):
    uniprot_id = data.get('uniprot_id')
    pae, structure = fetch_afdb_data(uniprot_id)
    if pae is None:
        return {'error': 'No PAE data found for the given UniProt ID.'}
    if structure is None:
        return {'error': 'No structure data found for the given UniProt ID.'}
    
    afragmenter_result = run_afragmenter(pae, 
                                        data.get('pae_threshold'), 
                                        data.get('resolution'), 
                                        data.get('objective_function'), 
                                        data.get('iterations'), 
                                        data.get('min_size'))
    
    if isinstance(afragmenter_result, dict) and 'error' in afragmenter_result:
        return afragmenter_result
    
    plot_hash = hashlib.sha1(uniprot_id.encode()).hexdigest()
    #pae_plot_path = f"images/{plot_hash}.png"
    
    #fig, ax = afragmenter_result.plot_pae()
    #fig = ax.get_figure()
    #ax.figure.savefig(os.path.join(app.static_folder, pae_plot_path))
    pae_plot_path = plot_pae_figure(plot_hash, afragmenter_result)

    structure_format = _determine_file_format(structure)
    return format_return_data(afragmenter_result.cluster_intervals, structure, structure_format, pae_plot_path)


def process_file_upload(data: dict):
    pae_data_bytes = data.get('alphafold_json').read()
    pae_data = json.loads(pae_data_bytes)
    
    afragmenter_result = run_afragmenter(pae_data, 
                                        data.get('pae_threshold'), 
                                        data.get('resolution'), 
                                        data.get('objective_function'), 
                                        data.get('iterations'), 
                                        data.get('min_size'))
    if isinstance(afragmenter_result, dict) and 'error' in afragmenter_result:
        return afragmenter_result

    plot_hash = hashlib.sha1(pae_data_bytes).hexdigest()
    #pae_plot_path = f"images/{plot_hash}.png"
    #fig, ax = afragmenter_result.plot_pae()
    #fig = ax.get_figure()
    #ax.figure.savefig(os.path.join(app.static_folder, pae_plot_path))
    pae_plot_path = plot_pae_figure(plot_hash, afragmenter_result)
    
    if not data.get('structure_file'):
        structure_data = ""
        return format_return_data(afragmenter_result.cluster_intervals, structure_data, None, pae_plot_path)
        
    structure_data = data.get('structure_file').read()
    structure_data = structure_data.decode('utf-8')
    structure_format = _determine_file_format(structure_data)
    return format_return_data(afragmenter_result.cluster_intervals, structure_data, structure_format, pae_plot_path)


def plot_pae_figure(plot_hash: str, afragmenter_result):
    cleanup_generated_files() # Clean up old files before generating new ones

    relative_url_path = f"images/temp_pae_images/{plot_hash}.png"
    full_save_path = os.path.join(app.static_folder, relative_url_path)

    # Check if the plot already exists in the static folder
    if os.path.exists(full_save_path):
        return f"/static/{relative_url_path}"
    
    plt.rc('font', size=14)
    fig, ax = afragmenter_result.plot_pae()
    ax.figure.savefig(
        full_save_path,
        transparent=True,
        bbox_inches='tight',
        pad_inches=0.05
    )
    return f"/static/{relative_url_path}"




@app.route("/process", methods=['GET', 'POST'])
def process():
    try:
        result = process_input()
        return result
    except Exception as e:
        app.logger.error(f"Error in processing route: {str(e)}")
        return jsonify({"error": str(e)}), 500



@app.route("/documentation")
def documentation():
    return render_template("documentation.html")



if __name__ == "__main__":
    app.run(debug=True)
    