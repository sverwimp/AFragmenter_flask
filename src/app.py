from flask import Flask, render_template, request, jsonify
from flask_wtf.csrf import CSRFProtect
from afragmenter import AFragmenter

from .form import InputForm

from pprint import pprint as print

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
    

def process_afdb_input(data: dict):
    print("Got to process_afdb_input")
    return {'error': 'NotImplementedError: process_afdb_input has not been implemented yet.'}


def process_file_upload(data: dict):
    try:

        json_file = data.get('alphafold_json')
        pae_threshold = data.get('pae_threshold')
        a = AFragmenter(pae_matrix=json_file, threshold=pae_threshold)

        resolution = data.get('resolution')
        objective_function = data.get('objective_function')
        n_iterations = data.get('iterations')
        min_size = data.get('min_size')
        a = a.cluster(resolution=resolution, objective_function=objective_function, n_iterations=n_iterations, min_size=min_size)

        result = a.cluster_intervals

        return result
    except Exception as e:
        print(f'Something went wrong: {str(e)}')
        return {'error': 'NotImplementedError: process_file_upload has not been implemented yet.'}



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