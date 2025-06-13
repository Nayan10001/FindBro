// API endpoint URL (adjust as needed)
const API_URL = 'http://localhost:8000/api/search';

// DOM elements
const searchInput = document.getElementById('search-input');
const searchButton = document.getElementById('search-button');
const resultsContainer = document.getElementById('results-list');
const loadingIndicator = document.getElementById('loading');
const noResultsMessage = document.getElementById('no-results');
const profileTemplate = document.getElementById('profile-template');

// Event listeners
searchButton.addEventListener('click', performSearch);
searchInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        performSearch();
    }
});

// Initialize with a sample search when the page loads
document.addEventListener('DOMContentLoaded', () => {
    searchInput.focus();

    // Trigger search on page load
    searchInput.value = "developer";
    searchButton.click();
});

// Search function
async function performSearch() {
    const query = searchInput.value.trim();
    
    if (!query) {
        alert('Please enter a search query');
        return;
    }
    
    // Show loading indicator and hide previous results
    loadingIndicator.classList.remove('hidden');
    resultsContainer.innerHTML = '';
    noResultsMessage.classList.add('hidden');
    
    try {
        const response = await fetch(`${API_URL}?query=${encodeURIComponent(query)}`);
        const data = await response.json();
        
        // Hide loading indicator
        loadingIndicator.classList.add('hidden');
        
        if (data.status === 'error') {
            console.error('Search error:', data.message);
            alert(`Error: ${data.message}`);
            return;
        }
        
        if (data.results.length === 0) {
            noResultsMessage.classList.remove('hidden');
            return;
        }
        
        // Display results
        displayResults(data.results);
        
    } catch (error) {
        console.error('Error fetching search results:', error);
        loadingIndicator.classList.add('hidden');
        alert('Failed to fetch search results. Please try again later.');
    }
}

// Display search results
function displayResults(results) {
    resultsContainer.innerHTML = '';
    
    results.forEach((profile, index) => {
        const profileCard = createProfileCard(profile);
        profileCard.style.animationDelay = `${index * 0.1}s`;
        resultsContainer.appendChild(profileCard);
    });
}

// Create profile card from template
function createProfileCard(profile) {
    const card = document.importNode(profileTemplate.content, true).firstElementChild;
    
    // Set basic profile information
    card.querySelector('.profile-name').textContent = profile.name;
    card.querySelector('.profile-handle').textContent = `@${profile.handle}`;
    
    // Format and display the matching score as percentage
    const scorePercent = Math.round(profile.score * 100);
    card.querySelector('.profile-score').textContent = `${scorePercent}% Match`;
    
    // Set experience and timezone
    card.querySelector('.profile-experience').textContent = 
        `Experience: ${profile.experience} ${profile.experience === 1 ? 'year' : 'years'}`;
    card.querySelector('.profile-timezone').textContent = 
        `Timezone: ${profile.timezone}`;
    
    // Create and append skill tags
    const skillsContainer = card.querySelector('.profile-skills');
    if (profile.skills && profile.skills.length > 0) {
        profile.skills.forEach(skill => {
            const tag = document.createElement('span');
            tag.className = 'tag skill';
            tag.textContent = skill;
            skillsContainer.appendChild(tag);
        });
    } else {
        skillsContainer.textContent = 'No skills listed';
        skillsContainer.style.color = '#64748b';
    }
    
    // Create and append role tags
    const rolesContainer = card.querySelector('.profile-roles');
    if (profile.roles && profile.roles.length > 0) {
        profile.roles.forEach(role => {
            const tag = document.createElement('span');
            tag.className = 'tag role';
            tag.textContent = role;
            rolesContainer.appendChild(tag);
        });
    } else {
        rolesContainer.textContent = 'No preferred roles listed';
        rolesContainer.style.color = '#64748b';
    }
    
    // Create and append interest tags
    const interestsContainer = card.querySelector('.profile-interests');
    if (profile.interests && profile.interests.length > 0) {
        profile.interests.forEach(interest => {
            const tag = document.createElement('span');
            tag.className = 'tag interest';
            tag.textContent = interest;
            interestsContainer.appendChild(tag);
        });
    } else {
        interestsContainer.textContent = 'No project interests listed';
        interestsContainer.style.color = '#64748b';
    }
    
    return card;
}
