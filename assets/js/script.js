// Store selected file globally
let selectedFile = null;
let currentUser = null;

// Check authentication status
async function checkAuth() {
    try {
        const response = await fetch('/auth/status');
        const data = await response.json();
        
        if (!data.authenticated) {
            // Redirect to login if not authenticated
            if (!window.location.pathname.includes('login.html')) {
                window.location.href = '/auth/login';
            }
            return false;
        }
        
        currentUser = data.user;
        displayUserProfile();
        return true;
    } catch (error) {
        console.error('Error checking authentication:', error);
        return false;
    }
}

// Display user profile in navbar
function displayUserProfile() {
    if (!currentUser) return;
    
    const navbar = document.querySelector('.title-bar');
    if (!navbar) return;
    
    // Check if user profile already exists
    if (document.getElementById('userProfile')) return;
    
    // Create user profile element
    const userProfile = document.createElement('div');
    userProfile.id = 'userProfile';
    userProfile.style.cssText = 'display: flex; align-items: center; gap: 12px; margin-left: auto; margin-right: 12px;';
    
    // User avatar and name
    const userInfo = document.createElement('div');
    userInfo.style.cssText = 'display: flex; align-items: center; gap: 8px;';
    userInfo.innerHTML = `
        <img src="${currentUser.picture}" alt="${currentUser.name}" style="width: 32px; height: 32px; border-radius: 50%; border: 2px solid #007AFF;">
        <span style="font-size: 14px; color: #333; font-weight: 500;">${currentUser.name}</span>
    `;
    
    // Logout button
    const logoutBtn = document.createElement('button');
    logoutBtn.textContent = 'Logout';
    logoutBtn.className = 'btn';
    logoutBtn.style.cssText = 'padding: 8px 16px; font-size: 14px; background: #f5f5f5; color: #333; border: 1px solid #d0d0d0;';
    logoutBtn.onclick = () => {
        window.location.href = '/auth/logout';
    };
    
    userProfile.appendChild(userInfo);
    userProfile.appendChild(logoutBtn);
    
    // Insert before window controls
    const windowControls = navbar.querySelector('.window-controls');
    if (windowControls) {
        navbar.insertBefore(userProfile, windowControls);
    } else {
        navbar.appendChild(userProfile);
    }
}

// Initialize authentication on page load
document.addEventListener('DOMContentLoaded', () => {
    // Don't check auth on login page
    if (!window.location.pathname.includes('login.html') && !window.location.pathname.includes('/auth/')) {
        checkAuth();
    }
});

// Handle file selection
function handleFileSelect(event) {
    const file = event.target.files[0];
    if (file) {
        const input = document.getElementById('projectDescription');
        input.value = file.name;
        selectedFile = file; // Store file for API call
        console.log('File selected:', file.name);
    }
}

// Generate User Stories - send file to backend API
async function generateUserStories() {
    const input = document.getElementById('projectDescription');
    const fileInput = document.getElementById('fileInput');
    
    // Check if file is selected
    if (!selectedFile && fileInput.files.length === 0) {
        alert('Please select a file to upload');
        return;
    }
    
    const file = selectedFile || fileInput.files[0];
    
    // Show loading state
    const generateBtn = document.querySelector('.btn-primary');
    const originalText = generateBtn.textContent;
    generateBtn.textContent = 'Generating...';
    generateBtn.disabled = true;
    
    try {
        // Create FormData to send file
        const formData = new FormData();
        formData.append('file', file);
        
        // Send file to backend API
        const response = await fetch('/api/generate-stories', {
            method: 'POST',
            body: formData
        });
        
        // Get response text first to check content type
        const responseText = await response.text();
        
        if (!response.ok) {
            // Try to parse as JSON, but handle HTML/plain text errors
            let errorMessage = `Server error: ${response.status}`;
            try {
                const errorData = JSON.parse(responseText);
                errorMessage = errorData.error || errorData.message || errorMessage;
                if (errorData.details && Array.isArray(errorData.details)) {
                    console.error('Error details:', errorData.details);
                }
            } catch (e) {
                // Response is not JSON (might be HTML error page)
                console.error('Server returned non-JSON error:', responseText.substring(0, 200));
                errorMessage = `Server error ${response.status}. Check server logs for details.`;
            }
            throw new Error(errorMessage);
        }
        
        // Parse JSON response
        let data;
        try {
            data = JSON.parse(responseText);
        } catch (e) {
            console.error('Failed to parse JSON response:', responseText.substring(0, 200));
            throw new Error('Invalid JSON response from server. Check server logs.');
        }
        
        if (data.success && data.stories) {
            // Store stories in sessionStorage
            sessionStorage.setItem('userStories', JSON.stringify(data.stories));
            sessionStorage.setItem('projectDescription', file.name);
            
            // Navigate to stories page
            window.location.href = 'stories.html';
        } else {
            throw new Error('Invalid response from server');
        }
    } catch (error) {
        console.error('Error generating stories:', error);
        console.error('Full error:', error);
        
        // Show user-friendly error message
        let errorMsg = `Error generating user stories: ${error.message}`;
        if (error.message.includes('Failed to fetch') || error.message.includes('NetworkError')) {
            errorMsg += '\n\nCannot connect to server. Please make sure the Flask server is running on port 5000.';
        } else if (error.message.includes('500')) {
            errorMsg += '\n\nServer error occurred. Check the Flask server terminal for detailed error messages.';
        }
        
        alert(errorMsg);
    } finally {
        // Restore button state
        generateBtn.textContent = originalText;
        generateBtn.disabled = false;
    }
}

// Global array to store user stories (will be populated from backend API)
let userStories = [];

// Load user stories from backend API or sessionStorage
async function loadUserStories() {
    // Check if stories are in sessionStorage (for demo purposes)
    const storedStories = sessionStorage.getItem('userStories');
    
    if (storedStories) {
        try {
            userStories = JSON.parse(storedStories);
        } catch (e) {
            console.error('Error parsing stored stories:', e);
            userStories = [];
        }
    }
    
    // Stories are loaded from sessionStorage (set after generation)
    // This allows the stories page to display the generated stories
    // without needing a separate GET endpoint
    
    // If no stories loaded, show message
    if (userStories.length === 0) {
        console.log('No stories found. Please generate stories first.');
    }
    
    renderStoryList();
    
    // Select first story by default if available
    if (userStories.length > 0) {
        selectStory(0);
    }
}


// Render the story list dynamically
function renderStoryList() {
    const storyList = document.getElementById('storyList');
    // Clear existing items safely
    while (storyList.firstChild) {
        storyList.removeChild(storyList.firstChild);
    }
    
    if (userStories.length === 0) {
        const noStoriesItem = document.createElement('li');
        noStoriesItem.className = 'no-stories';
        noStoriesItem.textContent = 'No user stories available';
        storyList.appendChild(noStoriesItem);
        return;
    }
    
    userStories.forEach((story, index) => {
        const listItem = document.createElement('li');
        listItem.className = 'story-item';
        listItem.setAttribute('data-story-index', index);
        listItem.textContent = `User story ${index + 1}`;
        listItem.onclick = () => selectStory(index);
        storyList.appendChild(listItem);
    });
}

// Select a story from the list by index
function selectStory(storyIndex) {
    // Validate index
    if (storyIndex < 0 || storyIndex >= userStories.length) {
        console.error('Invalid story index:', storyIndex);
        return;
    }
    
    // Remove active class from all items
    const items = document.querySelectorAll('.story-item');
    items.forEach(item => item.classList.remove('active'));
    
    // Add active class to selected item
    const selectedItem = document.querySelector(`[data-story-index="${storyIndex}"]`);
    if (selectedItem) {
        selectedItem.classList.add('active');
    }
    
    // Update story details
    updateStoryDetails(storyIndex);
}

// Format test cases for display
function formatTestCases(testCasesStr) {
    if (!testCasesStr || testCasesStr === '-') {
        return '-';
    }
    
    // Check if it's already a formatted string (starts with "Test:", "Test Case:", etc.)
    const trimmed = testCasesStr.trim();
    if (trimmed.startsWith('Test:') || 
        trimmed.startsWith('Test Case:') || 
        trimmed.startsWith('1.') ||
        trimmed.startsWith('Test ') ||
        (trimmed.includes('\n') && !trimmed.startsWith('[') && !trimmed.startsWith('{'))) {
        // Already formatted, return as-is
        return testCasesStr;
    }
    
    try {
        // Try to parse as JSON
        const testCases = JSON.parse(testCasesStr);
        
        if (Array.isArray(testCases)) {
            // Format array of test cases
            return testCases.map((tc, idx) => {
                if (typeof tc === 'object' && tc !== null) {
                    // Handle different field name variations
                    const name = tc.testCaseName || tc.test_case_name || tc.name || `Test ${idx + 1}`;
                    const desc = tc.description || tc.test_description || '';
                    const steps = Array.isArray(tc.steps) ? tc.steps.join('\n  - ') : (tc.test_steps ? tc.test_steps : '');
                    const expected = tc.expectedResult || tc.expected_output || '';
                    const input = tc.inputData || tc.input_data || '';
                    const testType = tc.testType || tc.test_type || '';
                    
                    let formatted = `${idx + 1}. ${name}`;
                    if (desc) formatted += `\n   Description: ${desc}`;
                    if (input) formatted += `\n   Input: ${JSON.stringify(input)}`;
                    if (steps) formatted += `\n   Steps:\n  - ${steps}`;
                    if (expected) formatted += `\n   Expected: ${JSON.stringify(expected)}`;
                    if (testType) formatted += `\n   Type: ${testType}`;
                    return formatted;
                }
                return `${idx + 1}. ${tc}`;
            }).join('\n\n');
        } else if (typeof testCases === 'object' && testCases !== null) {
            // Check if it's a testCases object with scenarios
            if (testCases.testCases && Array.isArray(testCases.testCases)) {
                return formatTestCases(JSON.stringify(testCases.testCases));
            }
            // Format object/dictionary
            return JSON.stringify(testCases, null, 2);
        }
        
        return testCasesStr;
    } catch (e) {
        // Not JSON, return as-is (it's probably already formatted)
        return testCasesStr;
    }
}

// Update story details in the content panel
function updateStoryDetails(storyIndex) {
    const story = userStories[storyIndex];
    
    if (!story) {
        console.error('Story not found at index:', storyIndex);
        return;
    }
    
    // Set title
    document.getElementById('storyTitle').textContent = story.title || '-';
    
    // Set description
    document.getElementById('storyDescription').textContent = story.description || '-';
    
    // Set Definition of Done / Deliverables
    const dodElement = document.getElementById('storyDoD');
    if (story.definitionOfDone) {
        // Check if it contains bullet points
        if (story.definitionOfDone.includes('•')) {
            dodElement.textContent = story.definitionOfDone;
            dodElement.style.whiteSpace = 'pre-wrap';
        } else {
            dodElement.textContent = story.definitionOfDone;
        }
    } else {
        dodElement.textContent = '-';
    }
    
    // Set test cases
    document.getElementById('storyTestCases').textContent = formatTestCases(story.testCases) || '-';
}

// Integrate a single story
async function integrateStory() {
    const activeItem = document.querySelector('.story-item.active');
    if (!activeItem) {
        alert('Please select a user story to integrate.');
        return;
    }
    
    const storyIndex = parseInt(activeItem.getAttribute('data-story-index'));
    const story = userStories[storyIndex];
    
    if (!story) {
        alert('Story not found.');
        return;
    }
    
    try {
        const response = await fetch('/api/integrate-story', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                storyId: story.id || (storyIndex + 1),
                story: story  // Send full story data for saving
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
        alert(`Story ${story.id || (storyIndex + 1)} integrated successfully!`);
        console.log('Integration response:', data);
    } catch (error) {
        console.error('Error integrating story:', error);
        alert(`Error integrating story: ${error.message}`);
    }
}

// Integrate all stories
async function integrateAll() {
    if (userStories.length === 0) {
        alert('No user stories available to integrate.');
        return;
    }
    
    if (!confirm(`Are you sure you want to integrate all ${userStories.length} user stories?`)) {
        return;
    }
    
    try {
        const response = await fetch('/api/integrate-all', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                storyIds: userStories.map(s => s.id),
                stories: userStories  // Send full stories data for saving
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
        alert(`All ${userStories.length} stories integrated successfully!`);
        console.log('Integration response:', data);
    } catch (error) {
        console.error('Error integrating all stories:', error);
        alert(`Error integrating stories: ${error.message}`);
    }
}

// Initialize stories page
if (window.location.pathname.includes('stories.html')) {
    // Load and render user stories when page loads
    loadUserStories();
}

// Function to update stories from backend (call this when Python code generates stories)
function updateUserStories(stories) {
    userStories = stories;
    sessionStorage.setItem('userStories', JSON.stringify(stories));
    renderStoryList();
    
    // Select first story by default
    if (userStories.length > 0) {
        selectStory(0);
    }
}

