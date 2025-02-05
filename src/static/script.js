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


    function setupSliderControlEvents(slider, valueElement) {
        // Put slider value in number input
        slider.addEventListener("input", (event) => {
            valueElement.value = event.target.value;
        });
    
        // Put number input value in slider, with range check
        valueElement.addEventListener("input", () => {
            const max = parseFloat(valueElement.max);
            const min = parseFloat(valueElement.min);
            let passedValue = parseFloat(valueElement.value);
    
            // Clamp value to min/max
            if (passedValue > max) {
                valueElement.value = max;
                slider.value = max;
            } else if (passedValue < min) {
                valueElement.value = min;
                slider.value = min;
            } else {
                slider.value = passedValue;
            }
        });
    
        slider.addEventListener("wheel", (event) => {
            event.preventDefault(); // Prevent page scroll
    
            const step = parseFloat(valueElement.step) || 1;
            let newSliderValue = Number(slider.value);
    
            // Adjust value based on wheel scroll direction
            if (event.deltaY < 0) {
                newSliderValue += step;
            } else {
                newSliderValue -= step;
            }
    
            // Clamp slider value to min/max
            const max = parseFloat(slider.max);
            const min = parseFloat(slider.min);
    
            if (newSliderValue > max) {
                newSliderValue = max;
            } else if (newSliderValue < min) {
                newSliderValue = min;
            }
    
            // Update slider and value element
            slider.value = newSliderValue.toFixed(10); // Round to avoid floating point issues
            valueElement.valueAsNumber = parseFloat(slider.value);
        });
    }


    const paeThresholdSliderValue = document.querySelector('.pae-threshold-value');
    const paeThresholdSlider = document.querySelector('.pae-threshold-range');
    const resolutionSliderValue = document.querySelector('.resolution-value')
    const resolutionSlider = document.querySelector('.resolution-range')

    setupSliderControlEvents(paeThresholdSlider, paeThresholdSliderValue);
    setupSliderControlEvents(resolutionSlider, resolutionSliderValue);


   // Handle form submission
   const form = document.querySelector('#main-form');
   form.addEventListener('submit', (event) => {
        if (!form.checkValidity()) {
            e.preventDefault();
        } else {
            form.submit();
        }
   });

    
});

