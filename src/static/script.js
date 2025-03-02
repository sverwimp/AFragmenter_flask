document.addEventListener('DOMContentLoaded', function() {
    const afdbRadio = document.querySelector('.radio-afdb');
    const affilesRadio = document.querySelector('.radio-affiles');
    const afdbDiv = document.getElementById('div-afdb');
    const affilesDiv = document.getElementById('div-affiles');
    
    const uniprotField = document.getElementById('afdb-input');
    const alphafoldJsonField = document.querySelector('.json-file-upload');

    // Function to set required states based on radio button state
    function setRequiredStates() {
        if (afdbRadio.checked) {
            afdbDiv.style.display = 'flex';
            affilesDiv.style.display = 'none';
            uniprotField.required = true;
            alphafoldJsonField.required = false;
        } else if (affilesRadio.checked) {
            afdbDiv.style.display = 'none';
            affilesDiv.style.display = 'flex';
            uniprotField.required = false;
            alphafoldJsonField.required = true;
        }
    }

    // Initialize required states
    setRequiredStates();
    afdbRadio.addEventListener('change', function() {
        setRequiredStates();
    });
    affilesRadio.addEventListener('change', function() {
        setRequiredStates();
    });

    // Form submission
    const form = document.querySelector('#main-form');
    form.addEventListener('submit', async (event) => {
        event.preventDefault(); // Prevent form submission

        if (!form.checkValidity()) {
            return; // stop execution if form is invalid
        }

        let formData = new FormData(form); // Extract form data

        try {
            let response = await fetch('/process', {
                method: 'POST',
                body: formData
            });

            let result = await response.json();

            /*
            result = {
                success: true,
                data: {
                    cluster_intervals: {
                        0: [(0, 10), (20, 30), (40, 50)],
                        1: [(11, 19), (31, 39)]],
                        ...
                    },
                    'structure': '# PDB file content',
                    'structure_format': 'pdb',
                },
                error: null
            }
            */


            if (result.success) {
                updateTable(result.data.cluster_intervals);

                /*
                TODO:
                - Display struture in 3D viewer
                - Display displaced structure in 3D viewer
                - Color residues in 3D viewer based on cluster_intervals
                - display PAE plot

                - Add download button (result, + something else? (like parameters used))
                */
        

                update3DViewer(result.data.structure, result.data.cluster_intervals, result.data.structure_format);


            } else {
                alert("Error: " + result.error);
            }
        } catch (error) {
            console.error("Error: " + error);
            alert("Error: " + error);
        }
    });


    // Function to update the 3D viewer
    function update3DViewer(structure, clusterIntervals, fileFormat) {
        let viewer3D = document.getElementById('viewer3Dmol');
        const viewer = $3Dmol.createViewer(viewer3D, {
            backgroundColor: 'white',
            defaultcolors: $3Dmol.rasmolElementColors,
            style: 'cartoon',
        });

        console.log('viewer: ', viewer);

        viewer.addModel(structure, fileFormat);
        viewer.setStyle({}, { cartoon: { color: 'grey' } });

        const colorRange = ['red', 'blue', 'green', 'yellow', 'orange', 'purple', 'cyan', 'magenta'];
        Object.entries(clusterIntervals).forEach(([cluster, intervals], index) => {
            const color = colorRange[index % colorRange.length];
            intervals.forEach(([start, end]) => {
                viewer.setStyle({ resi: `${start + 1}-${end + 1}` }, { cartoon: { color: color } });
            });
        });

        viewer.zoomTo();
        viewer.render();
    }


    // Function to update the result table after form submission
    function updateTable(data) {
        let tableBody = document.getElementById('result-table-body');
        tableBody.innerHTML = ''; // Clear table

        Object.entries(data).forEach(([key, intervals]) => {
            let keyNumber = parseInt(key) + 1; // Increment key by 1

            // Compute total size of all intervals
            let totalSize = intervals.reduce((sum, [start, end]) => sum + (end - start + 1), 0);

            // Format intervals as "start-end_start-end"
            let formattedIntervals = intervals.map(([start, end]) => `${start + 1}-${end + 1}`).join("_");

            // Create new table row
            let newRow = document.createElement("tr");
            newRow.innerHTML = `<td>${keyNumber}</td><td>${totalSize}</td><td>${formattedIntervals}</td>`;
            tableBody.appendChild(newRow);
        });

    }


    // Check if UniProt ID has an associated AlphaFold prediction
    const uniprotSearchButton = document.getElementById('uniprotSearch');
    uniprotSearchButton.addEventListener('click', async () => {
        let uniprotId = uniprotField.value;

        // do nothing if field is empty
        if (uniprotId === '') { return; }

        try {
            uniprotId = uniprotId.toUpperCase().trim();
            let afdb_url = `https://alphafold.ebi.ac.uk/api/prediction/${uniprotId}`;
            let response = await fetch(afdb_url);
            let uniprotFieldColor = response.ok ? '#C8E6C9' : '#E78587';
            uniprotField.style.backgroundColor = uniprotFieldColor
        } catch (error) {
            console.error("Error: " + error);
            alert("Error: " + error);
        }
    });
    
});

