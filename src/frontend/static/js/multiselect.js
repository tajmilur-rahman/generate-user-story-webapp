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

// GitHub integration helpers
async function loadGitHubConfig() {
    try {
        const res = await fetch('/api/github-config');
        if (!res.ok) {
            return;
        }
        const data = await res.json();
        const statusEl = document.getElementById('githubStatus');
        const formEl = document.getElementById('githubConfigForm');
        const connectButtons = document.getElementById('githubConnectButtons');
        const manageButtons = document.getElementById('githubManageButtons');
        const ownerInput = document.getElementById('githubOwner');
        const repoInput = document.getElementById('githubRepo');

        if (!statusEl || !formEl || !connectButtons || !manageButtons) {
            return;
        }

        if (data.authenticated && data.github && data.github.username) {
            statusEl.textContent = `GitHub: Connected as ${data.github.username}`;
            connectButtons.style.display = 'none';
            manageButtons.style.display = 'flex';
            formEl.style.display = 'none'; // Start collapsed

            if (ownerInput) ownerInput.value = data.github.owner || data.github.username || '';
            if (repoInput) repoInput.value = data.github.repo || '';
        } else {
            statusEl.textContent = 'GitHub: Not connected';
            connectButtons.style.display = 'flex';
            manageButtons.style.display = 'none';
            formEl.style.display = 'none';
        }
    } catch (e) {
        console.error('Error loading GitHub config:', e);
    }
}

function toggleGitHubConfig() {
    const formEl = document.getElementById('githubConfigForm');
    if (formEl) {
        formEl.style.display = formEl.style.display === 'none' ? 'block' : 'none';
    }
}

function connectGitHub() {
    window.location.href = '/auth/github';
}

async function saveGitHubConfig() {
    const ownerInput = document.getElementById('githubOwner');
    const repoInput = document.getElementById('githubRepo');
    const formEl = document.getElementById('githubConfigForm');

    if (!ownerInput || !ownerInput.value.trim()) {
        alert('Please enter a GitHub owner/organization name.');
        return;
    }

    if (!repoInput || !repoInput.value.trim()) {
        alert('Please enter a GitHub repository name.');
        return;
    }

    try {
        const res = await fetch('/api/github-config', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                owner: ownerInput.value.trim(),
                repo: repoInput.value.trim(),
                branch: 'main',
                folder: null
            })
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error(data.error || 'Failed to save GitHub config');
        }

        alert('GitHub configuration saved successfully.');
        // Hide the form after successful save
        if (formEl) {
            formEl.style.display = 'none';
        }
    } catch (e) {
        console.error('Error saving GitHub config:', e);
        alert(`Error saving GitHub config: ${e.message}`);
    }
}

async function disconnectGitHub() {
    if (!confirm('Are you sure you want to disconnect GitHub? Your repository configuration will be removed.')) {
        return;
    }

    try {
        const res = await fetch('/api/github-disconnect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await res.json();
        if (!res.ok || !data.success) {
            throw new Error(data.error || 'Failed to disconnect GitHub');
        }

        alert('GitHub disconnected successfully.');
        // Reload the page to refresh the UI
        window.location.reload();
    } catch (e) {
        console.error('Error disconnecting GitHub:', e);
        alert(`Error disconnecting GitHub: ${e.message}`);
    }
}

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

    if (!confirm(`Are you sure you want to integrate ${selected.length} selected user stories to GitHub?`)) {
        return;
    }

    try {
        const response = await fetch('/api/integrate-selected-github', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
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
        let msg = `Created ${data.total_created} GitHub issue(s) successfully.`;
        if (data.total_failed > 0) {
            msg += ` (${data.total_failed} failed)`;
        }
        if (data.created_issues && data.created_issues.length > 0) {
            msg += `\n\nView issues:`;
            data.created_issues.forEach(issue => {
                msg += `\n• Issue #${issue.issue_number}: ${issue.issue_url}`;
            });
        }
        alert(msg);
        console.log('GitHub integration response:', data);
    } catch (error) {
        console.error('Error integrating selected stories to GitHub:', error);
        alert(`Error integrating stories to GitHub: ${error.message}`);
    }
}
