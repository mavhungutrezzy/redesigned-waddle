
(function () {
    // Click on zone -> open file picker
    document.querySelectorAll('.photo-upload-zone').forEach(zone => {
        const input = zone.querySelector('input[type="file"]');
        if (!input) return;

        // Click handler (avoid triggering when clicking remove button)
        zone.addEventListener('click', (e) => {
            if (e.target.closest('.photo-actions button')) return;
            input.click();
        });

        // When file selected
        input.addEventListener('change', () => {
            if (!input.files || !input.files[0]) return;
            showPreview(zone, input.files[0]);
            updateCounter();
        });

        // Drag & drop
        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });

        zone.addEventListener('dragleave', () => zone.classList.remove('dragover'));

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');

            const file = e.dataTransfer.files && e.dataTransfer.files[0];
            if (!file) return;
            if (!file.type || !file.type.startsWith('image/')) return;

            // Put file into the input (modern browsers)
            try {
                const dt = new DataTransfer();
                dt.items.add(file);
                input.files = dt.files;
            } catch (err) {
                // If DataTransfer isn't supported, user can still click-to-upload
            }

            showPreview(zone, file);
            updateCounter();
        });
    });

    // Preview renderer
    function showPreview(zone, file) {
        const reader = new FileReader();
        const placeholder = zone.querySelector('.upload-placeholder');
        const img = zone.querySelector('.image-preview');
        const actions =
            zone.querySelector('.photo-actions.d-none') ||
            zone.querySelector('.photo-actions');

        reader.onload = (ev) => {
            if (placeholder) placeholder.classList.add('d-none');
            if (img) {
                img.src = ev.target.result;
                img.classList.remove('d-none');
            }
            if (actions) actions.classList.remove('d-none');

            // If this form row had a DELETE checkbox (existing image), ensure it is unchecked when replacing
            const deleteCheckbox = zone.closest('.photo-card')?.querySelector('input[type="checkbox"][name$="-DELETE"]');
            if (deleteCheckbox) deleteCheckbox.checked = false;
        };
        reader.readAsDataURL(file);
    }

    // Delete button global function (matches your onclick="clearPhoto(n)")
    window.clearPhoto = function (counter) {
        const zone = document.getElementById('photoZone' + counter);
        if (!zone) return;

        const input = zone.querySelector('input[type="file"]');
        const placeholder = zone.querySelector('.upload-placeholder');
        const img = zone.querySelector('.image-preview');
        const actions = zone.querySelector('.photo-actions');

        // Clear preview UI
        if (img) {
            img.src = '';
            img.classList.add('d-none');
        }
        if (placeholder) placeholder.classList.remove('d-none');
        if (actions) actions.classList.add('d-none');

        // Clear input value (so user can re-upload same file)
        if (input) input.value = '';

        // If this is an existing image row, tick Django DELETE checkbox
        const deleteCheckbox = zone.closest('.photo-card')?.querySelector('input[type="checkbox"][name$="-DELETE"]');
        if (deleteCheckbox) deleteCheckbox.checked = true;

        updateCounter();
    };

    // Counter: counts how many are currently selected or already have an image
    function updateCounter() {
        let count = 0;

        document.querySelectorAll('.photo-upload-zone').forEach(zone => {
            const input = zone.querySelector('input[type="file"]');
            const img = zone.querySelector('.image-preview');
            const deleteCheckbox = zone.closest('.photo-card')?.querySelector('input[type="checkbox"][name$="-DELETE"]');

            // If marked delete -> don't count
            if (deleteCheckbox && deleteCheckbox.checked) return;

            // If a new file is selected -> count
            if (input && input.files && input.files.length > 0) {
                count++;
                return;
            }

            // If an existing image is shown (already has src and not hidden) -> count
            if (img && !img.classList.contains('d-none') && img.src) count++;
        });

        const badge = document.getElementById('photoCounter');
        if (badge) badge.textContent = `${count}/3 uploaded`;
    }

    // Run once on load to count existing images
    document.addEventListener('DOMContentLoaded', updateCounter);
    updateCounter();
})();