let currentMatchIndex = 0;
let matchesData = [];
let radarChartInstance = null;

// DOM Elements
const loader = document.getElementById('loader');
const feed = document.getElementById('feed');
const scrollContainer = document.getElementById('scrollContainer');
const nextMatchBtn = document.getElementById('nextMatchBtn');

const userAliasEl = document.getElementById('userAlias');
const matchAliasEl = document.getElementById('matchAlias');
const matchScoreVal = document.getElementById('matchScoreVal');

const frontScore = document.getElementById('frontScore');
const dnaFlipCard = document.getElementById('dnaFlipCard');
const dnaList = document.getElementById('dnaList');

const quirksContainer = document.getElementById('quirksContainer');
const oppositesContainer = document.getElementById('oppositesContainer');
const radarCanvas = document.getElementById('radarChart');

const passBtn = document.getElementById('passBtn');
const likeBtn = document.getElementById('likeBtn');
const emptyStack = document.getElementById('emptyStack');
const floatingActions = document.getElementById('floatingActions');

// Fetch Data
async function loadData() {
    try {
        const res = await fetch('data.json');
        const data = await res.json();
        matchesData = data.matches;
        
        if (matchesData && matchesData.length > 0) {
            renderMatch(matchesData[currentMatchIndex]);
            loader.classList.add('hidden');
            feed.classList.remove('hidden');
        }
    } catch (e) {
        console.error("Failed to load data.json", e);
    }
}

// Render Logic
function renderMatch(match) {
    // Reset scroll and flip
    scrollContainer.scrollTop = 0;
    dnaFlipCard.classList.remove('flipped');

    // Headers
    userAliasEl.textContent = match.selected_user.alias;
    matchAliasEl.textContent = match.match_user.alias;
    
    const percentage = Math.round(match.predicted_similarity * 100);
    matchScoreVal.textContent = `${percentage}%`;
    frontScore.textContent = `${percentage}%`;

    // DNA List
    dnaList.innerHTML = '';
    match.dna.forEach(d => {
        const score = Math.round(d.match_score * 100);
        const li = document.createElement('li');
        li.className = 'dna-item';
        li.innerHTML = `
            <span class="dna-item-label">${d.label}</span>
            <span class="dna-item-score">${score}%</span>
        `;
        dnaList.appendChild(li);
    });

    // Quirks
    quirksContainer.innerHTML = '';
    match.quirks.forEach(q => {
        const div = document.createElement('div');
        div.className = 'quirk-tag';
        div.innerHTML = `
            <span class="quirk-label">${q.label}</span>
            <span class="quirk-desc">${q.description.substring(0, 40)}...</span>
        `;
        quirksContainer.appendChild(div);
    });

    // Opposites
    oppositesContainer.innerHTML = '';
    match.opposites.forEach(o => {
        const uScore = o.selected_score * 100;
        const mScore = o.match_score * 100;
        
        const minVal = Math.min(uScore, mScore);
        const maxVal = Math.max(uScore, mScore);
        const diff = maxVal - minVal;

        const div = document.createElement('div');
        div.className = 'dumbbell-row';
        div.innerHTML = `
            <div class="dumbbell-labels">
                <span>${o.label}</span>
            </div>
            <div class="dumbbell-track">
                <div class="dumbbell-bar" style="left: ${minVal}%; width: ${diff}%;"></div>
                <div class="dumbbell-point point-user" style="left: ${uScore}%"></div>
                <div class="dumbbell-point point-match" style="left: ${mScore}%"></div>
            </div>
            <div class="dumbbell-labels" style="color:var(--text-muted); font-size:0.7rem; justify-content:flex-end;">
                <span><span style="color:var(--accent-blue)">You</span> vs <span style="color:var(--accent-red)">Match</span></span>
            </div>
        `;
        oppositesContainer.appendChild(div);
    });

    // Radar Chart
    renderRadar(match.radar);

    // Fade-in animation class reset
    const sections = document.querySelectorAll('.section');
    sections.forEach((s, idx) => {
        s.style.animation = 'none';
        s.offsetHeight; /* trigger reflow */
        s.style.animation = `fadeInUp 0.6s ease ${idx * 0.1}s both`;
    });
}

function renderRadar(radarData) {
    const ctx = radarCanvas.getContext('2d');
    
    if (radarChartInstance) {
        radarChartInstance.destroy();
    }

    // Chart.js global defaults
    Chart.defaults.color = '#94a3b8';
    Chart.defaults.font.family = 'Inter';

    radarChartInstance = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: radarData.categories.map(c => c.replace('_', ' ')),
            datasets: [
                {
                    label: 'You',
                    data: radarData.selected,
                    backgroundColor: 'rgba(94, 194, 255, 0.2)',
                    borderColor: 'rgba(94, 194, 255, 1)',
                    pointBackgroundColor: 'rgba(94, 194, 255, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(94, 194, 255, 1)',
                    borderWidth: 2,
                },
                {
                    label: 'Match',
                    data: radarData.match,
                    backgroundColor: 'rgba(246, 80, 143, 0.2)',
                    borderColor: 'rgba(246, 80, 143, 1)',
                    pointBackgroundColor: 'rgba(246, 80, 143, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(246, 80, 143, 1)',
                    borderWidth: 2,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                r: {
                    angleLines: { color: 'rgba(255,255,255,0.1)' },
                    grid: { color: 'rgba(255,255,255,0.1)' },
                    pointLabels: {
                        color: 'rgba(255,255,255,0.7)',
                        font: { size: 10 }
                    },
                    ticks: { display: false }
                }
            },
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: '#fff' }
                }
            }
        }
    });
}

// Interactions
dnaFlipCard.addEventListener('click', () => {
    dnaFlipCard.classList.toggle('flipped');
});

function handleNextMatch() {
    currentMatchIndex++;
    if (currentMatchIndex >= matchesData.length) {
        // Out of matches!
        scrollContainer.classList.add('hidden');
        floatingActions.classList.add('hidden');
        emptyStack.classList.remove('hidden');
    } else {
        renderMatch(matchesData[currentMatchIndex]);
    }
}

nextMatchBtn.addEventListener('click', handleNextMatch);
passBtn.addEventListener('click', handleNextMatch);
likeBtn.addEventListener('click', handleNextMatch);

// Init
document.addEventListener('DOMContentLoaded', loadData);
