document.addEventListener('DOMContentLoaded', function() {
    const afdbRadio = document.querySelector('.radio-afdb');
    const affilesRadio = document.querySelector('.radio-affiles');
    const afdbDiv = document.querySelector('.div-afdb');
    const affilesDiv = document.querySelector('.div-affiles');
    
    const uniprotField = document.getElementById('afdb-input');
    const alphafoldJsonField = document.querySelector('.json-file-upload');

    /*
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
    */
    function setRequiredStates() {
        if (afdbRadio.checked) {
            afdbDiv.classList.add("input-visible");
            affilesDiv.classList.remove("input-visible");
            uniprotField.required = true;
            alphafoldJsonField.required = false;
        } else if (affilesRadio.checked) {
            affilesDiv.classList.add("input-visible");
            afdbDiv.classList.remove("input-visible");
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
        let userIterations = formData.get('iterations'); // Get user-specified iterations

        if (formData.get('input_type') === 'afdb') {
            // Check if UniProt ID has an associated AlphaFold prediction
            let hasEntry = await checkAlphaFoldDatabaseEntry(formData.get('uniprot_id'));
            if (hasEntry !== 0) {
                alert('UniProt ID doesn not an associated AlphaFold prediction.');
                return;
            }
        }

        async function submitForm(iterations) {
            formData.set('iterations', iterations);

            const controller = new AbortController();
            let timeoutId;

            if (iterations < 0) {
                timeoutId = setTimeout(() => controller.abort(), 30000); // 30 seconds
            }

            try {
                let response = await fetch('/process', {
                    method: 'POST',
                    body: formData,
                    signal: controller.signal
                });

                if (timeoutId) {
                    clearTimeout(timeoutId);
                }

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
                    updatePaePlot(result.data.pae_plot_path);
                    // If structure is available, update 3D viewer
                    if (result.data.structure && result.data.cluster_intervals) {
                        update3DViewer(result.data.structure, result.data.cluster_intervals, result.data.structure_format);
                    }


                    // TODO: display PAE plot and add Download button (result, fasta, parameters)
                } else {
                    alert("Error: " + result.error);
                }
            } catch (error) {
                if (error.name === 'AbortError' && iterations < 0) {
                    console.log('Request timed out. Retrying with limited iterations...');
                    submitForm(1000); // Retry with limited iterations
                    alert('Request timed out. Retrying with limited iterations...');
                } else {
                    console.error("Error: " + error);
                    alert("Error: " + error);
                }
            }
        }

        // Submit the form with the user-specified number of iterations
        submitForm(userIterations);
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

    function updatePaePlot(paePlotPath) {
        let paePlotImg = document.getElementById('pae-plot-img');
        // print the paePlotPath to the console
        // console.log('PAE Plot Path:', paePlotPath);
        paePlotImg.src = `${paePlotPath}?t=${new Date().getTime()}`;
    }

    /*https://codepen.io/ajlohman/pen/GRWYWw
    // Change table with something else?*/

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
            newRow.innerHTML = `<td class="partition-table">${keyNumber}</td><td class="nres-table">${totalSize}</td><td class="chopping-table">${formattedIntervals}</td>`;
            tableBody.appendChild(newRow);
        });
    }

    async function checkAlphaFoldDatabaseEntry(uniprotId) {
        // do nothing if field is empty

        if (!uniprotId) return 1;

        try {
            uniprotId = uniprotId.toUpperCase().trim();
            let afdb_url = `https://alphafold.ebi.ac.uk/api/prediction/${uniprotId}`;
            let response = await fetch(afdb_url);
    
            // Set background color based on response status
            if (typeof uniprotField !== "undefined" && !response.ok) {
                
                uniprotField.style.color = '#E78587';
            }
    
            return response.ok ? 0 : 1;
        } catch (error) {
            console.error("Error:", error);
            if (typeof uniprotField !== 'undefined') {
                uniprotField.style.backgroundColor = '#E78587';
            }
            return 1;
        }
    }

    /*
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
    */
    // Reset color of UniProt ID field when user starts typing
    uniprotField.addEventListener('input', () => {
        uniprotField.style.color = '#5c676b';
    });

    
});

