import flask_wtf
import wtforms
import wtforms.validators as val

from flask_wtf.file import FileField, FileAllowed

class InputForm(flask_wtf.FlaskForm):


    input_type = wtforms.RadioField("Input type", 
                                    choices=[
                                        ('afdb', 'AFDB'), 
                                        ('affiles', 'File upload')
                                    ], 
                                    validators=[val.InputRequired()])

    # Text input for UniProt ID (only when AFDB is selected)
    uniprot_id = wtforms.StringField(
        "Uniprot ID",
        validators=[
            val.Optional(),
            val.Length(min=1, max=20),
            val.Regexp('^[a-zA-Z0-9]+$', message="Only letters and numbers are allowed")
        ]
    )

    alphafold_json = FileField(
        "AlphaFold json",
        validators=[
            FileAllowed(['json'], "Expected a json file!"),
            val.Optional()
        ]
    )

    structure_file = FileField(
        "Structure file (PDB or cif) [optional]",
        validators=[
            FileAllowed(["cif", "pdb"], "Expected a cif of PDB file"),
        ]
    )

    """
    # Add custom validation for required fields based on input_type
    class ValidateInput(val.StopValidation):
        def __init__(self, message=None):
            super().__init__(message)

        def validate(self, form, field):
            if form.input_type.data == 'afdb':
                if not form.uniprot_id.data:
                    raise self.ValidateError("Please enter a UniProt ID")
            elif form.input_type.data == 'affiles':
                if not form.alphafold_json.data.filename:
                    raise self.ValidateError("Please upload the AlphaFold JSON file")
    
    # Add the custom validator to the form
    validators = [ValidateInput()]
    """

    # Custom validation method inside the form class
    def validate(self, extra_validators=None):
        # Run default validators first
        rv = super().validate(extra_validators=extra_validators)
        if not rv:
            return False

        # Apply custom validation logic based on input_type
        if self.input_type.data == "afdb":
            if not self.uniprot_id.data:
                self.uniprot_id.errors.append("Please enter a UniProt ID")
                return False
        elif self.input_type.data == "affiles":
            if not self.alphafold_json.data:
                self.alphafold_json.errors.append("Please upload the AlphaFold JSON file")
                return False

        return True



    pae_threshold = wtforms.IntegerField(
        "PAE contrast threshold",
        validators=[
            val.NumberRange(min=0, max=32),
            val.InputRequired()
        ],
        default=2
    )

    resolution = wtforms.DecimalField(
        "Clustering resolution",
        places=1,
        validators=[
            val.NumberRange(min=0, max=1.5),
            val.InputRequired()
        ],
        default=0.7
    )

    min_size = wtforms.IntegerField(
        "Minimum size parition",
        validators=[val.Optional()],
        default=10
    )

    merge = wtforms.BooleanField(
        "Merge small partitions",
        default=True
    )

    objective_function = wtforms.SelectField(
        'Objective function',
        choices=[
            ('modularity', 'Modularity'),
            ('cpm', 'Constant Potts Model')
        ],
        validators=[val.Optional()],
        default="modularity"
    )

    iterations = wtforms.IntegerField(
        "Iterations for the Leiden clustering algorithm",
        validators=[
            val.NumberRange(min=-1_000_000, max=1_000_000),
            val.Optional()
        ],
        default=-1
    )

    submit = wtforms.SubmitField("Submit")