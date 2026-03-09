// Multi-select functionality for user stories

// Track selected stories
let selectedStories = new Set();

// Update selected count display
function updateSelectedCount() {
    const countElement = document.getElementById('selectedCount');
    if (countElement) {
        countElement.textContent = selectedStories.size;
    }
}

// Select all stories
function selectAllStories() {
    const storyItems = document.querySelectorAll('.story-item');
    storyItems.forEach((item, index) => {
        selectedStories.add(index);
    });
    applySelectionClasses();
    updateSelectedCount();
}

// Deselect all stories
function deselectAllStories() {
    selectedStories.clear();
    applySelectionClasses();
    updateSelectedCount();
}

// Toggle story selection (without checkbox)
function toggleStorySelection(index) {
    if (selectedStories.has(index)) {
        selectedStories.delete(index);
    } else {
        selectedStories.add(index);
    }
    applySelectionClasses();
    updateSelectedCount();
}

// Apply visual selection classes to story items
function applySelectionClasses() {
    const storyItems = document.querySelectorAll('.story-item');
    storyItems.forEach((item) => {
        const index = parseInt(item.getAttribute('data-story-index'));
        if (selectedStories.has(index)) {
            item.classList.add('selected');
        } else {
            item.classList.remove('selected');
        }
    });
}

// Toggle export dropdown menu
function toggleExportDropdown() {
    const menu = document.getElementById('exportMenu');
    if (menu) {
        menu.style.display = menu.style.display === 'none' ? 'block' : 'none';
    }
}

// Close dropdown when clicking outside
document.addEventListener('click', function(event) {
    const dropdown = document.querySelector('.export-dropdown');
    const menu = document.getElementById('exportMenu');
    if (dropdown && menu && !dropdown.contains(event.target)) {
        menu.style.display = 'none';
    }
});

// Get selected stories
function getSelectedStories() {
    if (selectedStories.size === 0) {
        return [];
    }
    return Array.from(selectedStories).map(index => userStories[index]);
}

// Export selected stories to JSON
async function exportSelectedToJSON() {
    const selected = getSelectedStories();

    if (selected.length === 0) {
        alert('Please select at least one user story to export.');
        return;
    }

    try {
        const response = await fetch('/api/export-json', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stories: selected })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Export failed');
        }

        // Download the file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `selected_stories_${new Date().toISOString().slice(0, 10)}.json`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        console.log(`✅ Exported ${selected.length} stories to JSON successfully`);
    } catch (error) {
        console.error('Error exporting to JSON:', error);
        alert(`Error exporting to JSON: ${error.message}`);
    }
}

// Export selected stories to Word
async function exportSelectedToWord() {
    const selected = getSelectedStories();

    if (selected.length === 0) {
        alert('Please select at least one user story to export.');
        return;
    }

    try {
        const response = await fetch('/api/export-docx', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ stories: selected })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Export failed');
        }

        // Download the file
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `selected_stories_${new Date().toISOString().slice(0, 10)}.docx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        console.log(`✅ Exported ${selected.length} stories to Word successfully`);
    } catch (error) {
        console.error('Error exporting to Word:', error);
        alert(`Error exporting to Word: ${error.message}`);
    }
}

// Integrate selected stories
async function integrateSelected() {
    const selected = getSelectedStories();

    if (selected.length === 0) {
        alert('Please select at least one user story to integrate.');
        return;
    }

    if (!confirm(`Are you sure you want to integrate ${selected.length} selected user stories?`)) {
        return;
    }

    try {
        const response = await fetch('/api/integrate-all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                storyIds: selected.map((s, idx) => s.id || idx + 1),
                stories: selected
            })
        });

        const responseText = await response.text();

        if (!response.ok) {
            let errorMessage = `Server error: ${response.status}`;
            try {
                const errorData = JSON.parse(responseText);
                errorMessage = errorData.error || errorData.message || errorMessage;
            } catch (e) {
                console.error('Server returned non-JSON error:', responseText.substring(0, 200));
            }
            throw new Error(errorMessage);
        }

        const data = JSON.parse(responseText);
        alert(`${selected.length} selected stories integrated successfully!`);
        console.log('Integration response:', data);
    } catch (error) {
        console.error('Error integrating selected stories:', error);
        alert(`Error integrating stories: ${error.message}`);
    }
}
