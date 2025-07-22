// Configuration
const API_BASE_URL = 'http://localhost:8000/v1';

// DOM Elements
const searchInput = document.getElementById('searchInput');
const limitSelect = document.getElementById('limitSelect');
const searchButton = document.getElementById('searchButton');
const loadingSection = document.getElementById('loadingSection');
const resultsSection = document.getElementById('resultsSection');
const errorSection = document.getElementById('errorSection');
const resultsContainer = document.getElementById('resultsContainer');
const resultsTitle = document.getElementById('resultsTitle');
const resultsSubtitle = document.getElementById('resultsSubtitle');
const errorMessage = document.getElementById('errorMessage');
const retryButton = document.getElementById('retryButton');
const suggestionTags = document.querySelectorAll('.suggestion-tag');

// State management
let isSearching = false;
let currentQuery = '';

// Initialize app
document.addEventListener('DOMContentLoaded', function() {
    initializeEventListeners();
    focusSearchInput();
});

function initializeEventListeners() {
    // Search button click
    searchButton.addEventListener('click', handleSearch);
    
    // Enter key in search input
    searchInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSearch();
        }
    });
    
    // Retry button
    retryButton.addEventListener('click', handleSearch);
    
    // Suggestion tags
    suggestionTags.forEach(tag => {
        tag.addEventListener('click', function() {
            const suggestionText = this.getAttribute('data-text');
            searchInput.value = suggestionText;
            focusSearchInput();
            // Optionally trigger search immediately
            // handleSearch();
        });
    });
    
    // Auto-resize textarea
    searchInput.addEventListener('input', autoResizeTextarea);
}

function focusSearchInput() {
    searchInput.focus();
}

function autoResizeTextarea() {
    searchInput.style.height = 'auto';
    searchInput.style.height = Math.max(120, searchInput.scrollHeight) + 'px';
}

async function handleSearch() {
    const description = searchInput.value.trim();
    const limit = parseInt(limitSelect.value);
    
    // Validation
    if (!description) {
        showError('Por favor, describe el tipo de lugar que buscas.');
        focusSearchInput();
        return;
    }
    
    if (description.length < 3) {
        showError('La descripción debe tener al menos 3 caracteres.');
        focusSearchInput();
        return;
    }
    
    if (isSearching) {
        return; // Prevent multiple simultaneous requests
    }
    
    try {
        isSearching = true;
        currentQuery = description;
        
        showLoading();
        updateSearchButtonState(true);
        
        const recommendations = await searchPlaces(description, limit);
        
        if (recommendations.total_found > 0) {
            showResults(recommendations);
        } else {
            showNoResults(description);
        }
        
    } catch (error) {
        console.error('Search error:', error);
        showError(getErrorMessage(error));
    } finally {
        isSearching = false;
        updateSearchButtonState(false);
    }
}

async function searchPlaces(description, limit) {
    const requestBody = {
        description: description,
        limit: limit
    };
    
    const response = await fetch(`${API_BASE_URL}/places/recommendations`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const result = await response.json();
    
    if (!result.success) {
        throw new Error(result.message || 'Error en la respuesta del servidor');
    }
    
    return result.data;
}

function showLoading() {
    hideAllSections();
    loadingSection.classList.remove('hidden');
}

function showResults(recommendations) {
    hideAllSections();
    
    // Update results header
    const count = recommendations.total_found;
    resultsTitle.textContent = `${count} lugar${count !== 1 ? 'es' : ''} recomendado${count !== 1 ? 's' : ''} para ti`;
    resultsSubtitle.textContent = `Búsqueda: "${recommendations.query}"`;
    
    // Clear previous results
    resultsContainer.innerHTML = '';
    
    // Create place cards
    recommendations.recommendations.forEach(place => {
        const card = createPlaceCard(place);
        resultsContainer.appendChild(card);
    });
    
    resultsSection.classList.remove('hidden');
    
    // Smooth scroll to results
    setTimeout(() => {
        resultsSection.scrollIntoView({ 
            behavior: 'smooth', 
            block: 'start' 
        });
    }, 100);
}

function showNoResults(query) {
    hideAllSections();
    showError(`No se encontraron lugares que coincidan con: "${query}". Intenta con una descripción diferente.`, false);
}

function showError(message, isError = true) {
    hideAllSections();
    errorMessage.textContent = message;
    
    // Update error styling based on type
    const errorContent = errorSection.querySelector('.error-content');
    const icon = errorContent.querySelector('i');
    const title = errorContent.querySelector('h3');
    
    if (isError) {
        icon.className = 'fas fa-exclamation-triangle';
        icon.style.color = '#dc3545';
        title.textContent = 'Oops! Algo salió mal';
        retryButton.style.display = 'flex';
    } else {
        icon.className = 'fas fa-search';
        icon.style.color = '#6c757d';
        title.textContent = 'Sin resultados';
        retryButton.style.display = 'none';
    }
    
    errorSection.classList.remove('hidden');
}

function hideAllSections() {
    loadingSection.classList.add('hidden');
    resultsSection.classList.add('hidden');
    errorSection.classList.add('hidden');
}

function updateSearchButtonState(isLoading) {
    const icon = searchButton.querySelector('i');
    const buttonText = searchButton.childNodes[2]; // Text node after icon
    
    if (isLoading) {
        searchButton.disabled = true;
        icon.className = 'fas fa-spinner fa-spin';
        buttonText.textContent = ' Buscando...';
    } else {
        searchButton.disabled = false;
        icon.className = 'fas fa-sparkles';
        buttonText.textContent = ' Buscar Lugares';
    }
}

function createPlaceCard(place) {
    const card = document.createElement('div');
    card.className = 'place-card';
    
    // Ensure we have valid data
    const name = place.name || 'Nombre no disponible';
    const category = place.category || 'Sin categoría';
    const description = place.description || 'Descripción no disponible';
    const rating = place.rating ? parseFloat(place.rating) : null;
    const priceLevel = place.price_level || null;
    const address = place.address || 'Dirección no disponible';
    const similarityScore = place.similarity_score ? parseFloat(place.similarity_score) : 0;
    
    card.innerHTML = `
        <div class="place-header">
            <div>
                <div class="place-name">${escapeHtml(name)}</div>
                <div class="place-category">${escapeHtml(category)}</div>
            </div>
            <div class="similarity-score">
                <i class="fas fa-bullseye"></i>
                ${similarityScore.toFixed(1)}%
            </div>
        </div>
        
        <div class="place-info">
            ${rating !== null ? `
                <div class="info-item">
                    <i class="fas fa-star"></i>
                    <div class="rating">
                        <span class="stars">${generateStars(rating)}</span>
                        <span>${rating.toFixed(1)}</span>
                    </div>
                </div>
            ` : ''}
            
            ${priceLevel ? `
                <div class="info-item">
                    <i class="fas fa-dollar-sign"></i>
                    <span class="price-level">${escapeHtml(priceLevel)}</span>
                </div>
            ` : ''}
            
            <div class="info-item">
                <i class="fas fa-map-marker-alt"></i>
                <span>${escapeHtml(address)}</span>
            </div>
        </div>
        
        ${description !== 'Descripción no disponible' ? `
            <div class="place-description">
                ${escapeHtml(description)}
            </div>
        ` : ''}
    `;
    
    return card;
}

function generateStars(rating) {
    const fullStars = Math.floor(rating);
    const halfStar = rating % 1 >= 0.5;
    const emptyStars = 5 - fullStars - (halfStar ? 1 : 0);
    
    let stars = '';
    
    // Full stars
    for (let i = 0; i < fullStars; i++) {
        stars += '★';
    }
    
    // Half star
    if (halfStar) {
        stars += '☆';
    }
    
    // Empty stars
    for (let i = 0; i < emptyStars; i++) {
        stars += '☆';
    }
    
    return stars;
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function getErrorMessage(error) {
    if (error.message.includes('Failed to fetch')) {
        return 'No se pudo conectar al servidor. Verifica que la API esté ejecutándose en http://localhost:8000';
    }
    
    if (error.message.includes('HTTP 422')) {
        return 'Los datos enviados no son válidos. Verifica tu descripción e intenta nuevamente.';
    }
    
    if (error.message.includes('HTTP 500')) {
        return 'Error interno del servidor. Por favor, intenta nuevamente en unos momentos.';
    }
    
    if (error.message.includes('HTTP 404')) {
        return 'El endpoint de la API no fue encontrado. Verifica la configuración del servidor.';
    }
    
    return error.message || 'Ocurrió un error inesperado. Por favor, intenta nuevamente.';
}

// Utility function to detect if user is on mobile
function isMobile() {
    return window.innerWidth <= 768;
}

// Add some animations and smooth interactions
document.addEventListener('DOMContentLoaded', function() {
    // Add entrance animations
    const elements = document.querySelectorAll('.header-content, .search-section, .suggestions-section');
    elements.forEach((el, index) => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        
        setTimeout(() => {
            el.style.transition = 'all 0.6s ease';
            el.style.opacity = '1';
            el.style.transform = 'translateY(0)';
        }, index * 200);
    });
}); 