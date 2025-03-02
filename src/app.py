from flask import Flask, render_template, request, jsonify
from flask_wtf.csrf import CSRFProtect
from afragmenter import AFragmenter, fetch_afdb_data
from afragmenter.structure_displacement import displace_structure
from afragmenter.sequence_reader import SequenceReader
import numpy as np

from .form import InputForm

from pprint import pprint as print
import json

app = Flask(__name__, instance_relative_config=True)
app.config.from_pyfile('config.py')
csrf = CSRFProtect(app=app)


@app.route("/")
def index():
    form = InputForm()
    return render_template("index.html", form=form)


def process_input():
    form = InputForm()

    print(f'alphafold_json: {form.alphafold_json}')
    print(f'alphafold_json data: {form.alphafold_json.data}')

    
    print("test")
    print(request.files)
    print(form.alphafold_json.data)
    print("end test")

    print('Before validation')
    if not (request.method == "POST" and form.validate_on_submit()):
        return jsonify({"error": "Form validation failed", "errors": form.errors}), 400
    print("After validation")
    
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


    print(data)
    
    
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
        a = a.cluster(resolution=resolution, objective_function=objective_function, n_iterations=n_iterations, min_size=min_size)
        return a.cluster_intervals
    except Exception as e:
        return {'error': str(e)}
    

def format_return_data(cluster_intervals, structure, structure_format):
    #structure_displaced = displace_structure(structure, cluster_intervals, structure_format)
    return {
        'success': True, 
        'data': {
            'cluster_intervals': cluster_intervals,
            'structure': structure,
            'structure_format': structure_format,
            #'structure_displaced': structure_displaced
        },
        
    }


def process_afdb_input(data: dict):
    pae, structure = fetch_afdb_data(data.get('uniprot_id'))
    if pae is None:
        return {'error': 'No PAE data found for the given UniProt ID.'}
    if structure is None:
        return {'error': 'No structure data found for the given UniProt ID.'}
    
    cluster_intervals = run_afragmenter(pae, 
                                        data.get('pae_threshold'), 
                                        data.get('resolution'), 
                                        data.get('objective_function'), 
                                        data.get('iterations'), 
                                        data.get('min_size'))
    
    if isinstance(cluster_intervals, dict) and 'error' in cluster_intervals:
        return cluster_intervals
    
    structure_format = SequenceReader.determine_file_format(structure)
    return format_return_data(cluster_intervals, structure, structure_format)


def process_file_upload(data: dict):
    pae_data = data.get('alphafold_json').read()
    cluster_intervals = run_afragmenter(pae_data, 
                                        data.get('pae_threshold'), 
                                        data.get('resolution'), 
                                        data.get('objective_function'), 
                                        data.get('iterations'), 
                                        data.get('min_size'))
    if isinstance(cluster_intervals, dict) and 'error' in cluster_intervals:
        return cluster_intervals
    
    # TODO: need to handle case where structure file is not provided
    
    structure_data = data.get('structure_file').read()
    structure_format = SequenceReader.determine_file_format(structure_data)
    return format_return_data(cluster_intervals, structure_data, structure_format)




@app.route("/process", methods=['GET', 'POST'])
def process():
    try:
        result = process_input()
        return result
    except Exception as e:
        app.logger.error(f"Error in processing route: {str(e)}")
        return jsonify({"error": str(e)}), 500



if __name__ == "__main__":
    app.run(debug=True)

    """
    TODO:
    - Check which radio button selected
    - Get data from AFDB in case 
    - Process data using AFragmenter
    - Make figure and return cluster_intervals result for processing using javascript

    json_file = None
    pae_threshold = None
    a = AFragmenter(pae_matrix=json_file, threshold=pae_threshold)

    resolution = None
    objective_function = None
    n_iterations = None
    min_size = None
    a = a.cluster(resolution=resolution, objective_function=objective_function, n_iterations=n_iterations, min_size=min_size)

    result = a.cluster_intervals
    image, ax = a.plot_pae()
    """