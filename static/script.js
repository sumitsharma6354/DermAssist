const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const previewArea = document.getElementById('preview-area');
const userImage = document.getElementById('userImage');
const analyzeBtn = document.getElementById('analyzeBtn');
const resetBtn = document.getElementById('resetBtn');
const textSearchBtn = document.getElementById('textSearchBtn');
const textInput = document.getElementById('textInput');
const loadingState = document.getElementById('loadingState');
const emptyState = document.getElementById('emptyState');
const resultsGrid = document.getElementById('resultsGrid');

// --- TABS & UI SWITCHING ---
function switchTab(mode) {
    const imgSection = document.getElementById('image-search-section');
    const txtSection = document.getElementById('text-search-section');
    const btns = document.querySelectorAll('.tab-btn');

    if (mode === 'image') {
        imgSection.classList.remove('hidden');
        txtSection.classList.add('hidden');
        btns[0].classList.add('active');
        btns[1].classList.remove('active');
    } else {
        imgSection.classList.add('hidden');
        txtSection.classList.remove('hidden');
        btns[0].classList.remove('active');
        btns[1].classList.add('active');
    }
}

// --- IMAGE HANDLING ---
dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', handleFileSelect);
resetBtn.addEventListener('click', resetApp);
analyzeBtn.addEventListener('click', runImageAnalysis);
textSearchBtn.addEventListener('click', runTextAnalysis);

// Drag & Drop
dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.style.borderColor = '#2563eb'; });
dropZone.addEventListener('dragleave', () => { dropZone.style.borderColor = '#e2e8f0'; });
dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.style.borderColor = '#e2e8f0';
    if(e.dataTransfer.files.length) {
        fileInput.files = e.dataTransfer.files;
        handleFileSelect();
    }
});

function handleFileSelect() {
    const file = fileInput.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = (e) => {
            userImage.src = e.target.result;
            dropZone.classList.add('hidden');
            previewArea.classList.remove('hidden');
        };
        reader.readAsDataURL(file);
    }
}

function resetApp() {
    fileInput.value = '';
    textInput.value = '';
    dropZone.classList.remove('hidden');
    previewArea.classList.add('hidden');
    resultsGrid.classList.add('hidden');
    resultsGrid.innerHTML = '';
    emptyState.classList.remove('hidden');
}

// --- ANALYSIS FUNCTIONS ---

async function runImageAnalysis() {
    const file = fileInput.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);
    await fetchData(formData);
}

async function runTextAnalysis() {
    const query = textInput.value;
    if (!query) return;
    const formData = new FormData();
    formData.append('query', query);
    await fetchData(formData);
}

async function fetchData(formData) {
    // UI Loading State
    emptyState.classList.add('hidden');
    resultsGrid.classList.add('hidden');
    loadingState.classList.remove('hidden');

    try {
        const response = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        loadingState.classList.add('hidden');
        resultsGrid.classList.remove('hidden');
        
        if (data.error) {
            resultsGrid.innerHTML = `<div style="text-align:center; color:red; padding:20px;">⚠️ ${data.error}</div>`;
            return;
        }

        renderResults(data);

    } catch (err) {
        loadingState.classList.add('hidden');
        alert("System Error. Please check backend connection.");
    }
}

function renderResults(data) {
    resultsGrid.innerHTML = ''; 
    
    data.forEach((item, index) => {
        const imgSource = item.image_url ? item.image_url : 'https://placehold.co/120x120?text=No+Img';
        const scoreLabel = item.score === "Ref" ? "Reference" : `${item.score}% Match`;
        
        const card = document.createElement('div');
        card.className = 'result-card';
        card.style.animationDelay = `${index * 0.1}s`;
        
        card.innerHTML = `
            <img src="${imgSource}" class="match-image" alt="Case" onerror="this.src='https://placehold.co/120x120?text=Missing'">
            <div class="match-info">
                <div class="match-header">
                    <h3 class="match-diagnosis">${item.diagnosis}</h3>
                    <span class="match-score">${scoreLabel}</span>
                </div>
                <div class="meta-grid">
                    <div class="meta-item">
                        <span class="meta-label">Patient Age</span>
                        <div class="meta-value">${item.age} Years</div>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Gender</span>
                        <div class="meta-value">${item.sex}</div>
                    </div>
                    <div class="meta-item">
                        <span class="meta-label">Location</span>
                        <div class="meta-value">${item.location}</div>
                    </div>
                </div>
            </div>
        `;
        resultsGrid.appendChild(card);
    });
}