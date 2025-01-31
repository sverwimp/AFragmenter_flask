document.addEventListener('DOMContentLoaded', function() {
    const afdbRadio = document.getElementById('radio-afdb');
    const affilesRadio = document.getElementById('radio-affiles');
    const afdbDiv = document.querySelector('.div-afdb');
    const affilesDiv = document.querySelector('.div-affiles');

    afdbRadio.addEventListener('change', function() {
        if (afdbRadio.checked) {
            afdbDiv.style.display = 'block';
            affilesDiv.style.display = 'none';
        }
    });

    affilesRadio.addEventListener('change', function() {
        if (affilesRadio.checked) {
            afdbDiv.style.display = 'none';
            affilesDiv.style.display = 'block';
        }
    });

    // Initial state
    if (afdbRadio.checked) {
        afdbDiv.style.display = 'block';
        affilesDiv.style.display = 'none';
    } else if (affilesRadio.checked) {
        afdbDiv.style.display = 'none';
        affilesDiv.style.display = 'block';
    }
});