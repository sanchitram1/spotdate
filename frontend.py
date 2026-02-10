"""Frontend HTML templates for Spotify Stats app"""


def get_login_page():
    """Return the login page HTML"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Spotify Stats</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #ffffff;
            }

            .container {
                max-width: 500px;
                width: 90%;
                text-align: center;
            }

            .logo {
                font-size: 48px;
                margin-bottom: 20px;
            }

            h1 {
                font-size: 32px;
                font-weight: 700;
                margin-bottom: 10px;
                letter-spacing: -0.5px;
            }

            .subtitle {
                color: #b3b3b3;
                font-size: 16px;
                margin-bottom: 40px;
            }

            .login-button {
                background-color: #1db954;
                color: #ffffff;
                border: none;
                padding: 14px 32px;
                font-size: 16px;
                font-weight: 600;
                border-radius: 24px;
                cursor: pointer;
                transition: all 0.3s ease;
                width: 100%;
                letter-spacing: 0.5px;
            }

            .login-button:hover {
                background-color: #1ed760;
                transform: scale(1.02);
            }

            .login-button:active {
                transform: scale(0.98);
            }

            .footer {
                margin-top: 60px;
                font-size: 12px;
                color: #666666;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🎵</div>
            <h1>Spotify Stats</h1>
            <p class="subtitle">Discover your top artists and music insights</p>
            <button class="login-button" onclick="authorize()">Login with Spotify</button>
            <div class="footer">
                <p>Secure • Private • No data stored</p>
            </div>
        </div>

        <script>
            async function authorize() {
                const res = await fetch('/api/auth/authorize');
                const data = await res.json();
                window.location.href = data.auth_url;
            }
        </script>
    </body>
    </html>
    """


def get_callback_page():
    """Return the OAuth callback page HTML"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Authenticating...</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #ffffff;
            }

            .container {
                text-align: center;
            }

            .spinner {
                border: 4px solid #333333;
                border-top: 4px solid #1db954;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            h1 {
                font-size: 24px;
                font-weight: 600;
            }

            .subtitle {
                color: #b3b3b3;
                margin-top: 10px;
                font-size: 14px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="spinner"></div>
            <h1>Authenticating...</h1>
            <p class="subtitle">One moment, we're logging you in with Spotify</p>
        </div>

        <script>
            async function handleCallback() {
                const params = new URLSearchParams(window.location.search);
                const code = params.get('code');
                
                if (code) {
                    try {
                        const res = await fetch('/api/auth/callback', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                            body: 'code=' + code
                        });
                        
                        if (!res.ok) {
                            throw new Error('Authentication failed');
                        }
                        
                        const data = await res.json();
                        localStorage.setItem('user_id', data.user_id);
                        localStorage.setItem('access_token', data.access_token);
                        window.location.href = '/dashboard';
                    } catch (err) {
                        console.error('Error:', err);
                        window.location.href = '/';
                    }
                }
            }
            
            handleCallback();
        </script>
    </body>
    </html>
    """


def get_dashboard_page():
    """Return the authenticated dashboard page HTML"""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Spotify Stats - Dashboard</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }

            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                background: linear-gradient(135deg, #0f0f0f 0%, #1a1a1a 100%);
                min-height: 100vh;
                color: #ffffff;
            }

            .header {
                background: rgba(0, 0, 0, 0.4);
                padding: 20px;
                border-bottom: 1px solid #282828;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }

            .header h1 {
                font-size: 24px;
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 10px;
            }

            .logout-btn {
                background-color: #333333;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                font-size: 14px;
                border-radius: 20px;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }

            .logout-btn:hover {
                background-color: #404040;
            }

            .container {
                max-width: 1000px;
                margin: 0 auto;
                padding: 40px 20px;
            }

            .fetch-section {
                background: rgba(29, 185, 84, 0.1);
                border: 1px solid #1db954;
                border-radius: 8px;
                padding: 30px;
                text-align: center;
                margin-bottom: 40px;
            }

            .fetch-section h2 {
                font-size: 20px;
                margin-bottom: 10px;
            }

            .fetch-section p {
                color: #b3b3b3;
                margin-bottom: 20px;
                font-size: 14px;
            }

            .fetch-btn {
                background-color: #1db954;
                color: #ffffff;
                border: none;
                padding: 12px 28px;
                font-size: 16px;
                font-weight: 600;
                border-radius: 24px;
                cursor: pointer;
                transition: all 0.3s ease;
            }

            .fetch-btn:hover:not(:disabled) {
                background-color: #1ed760;
                transform: scale(1.02);
            }

            .fetch-btn:disabled {
                background-color: #666666;
                cursor: not-allowed;
            }

            .loading {
                display: none;
                text-align: center;
                padding: 20px;
            }

            .spinner {
                border: 4px solid #333333;
                border-top: 4px solid #1db954;
                border-radius: 50%;
                width: 30px;
                height: 30px;
                animation: spin 1s linear infinite;
                margin: 0 auto 15px;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            .error {
                background-color: #d32f2f;
                border: 1px solid #ff6b6b;
                color: #ffffff;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                display: none;
            }

            .success {
                background-color: #1db954;
                border: 1px solid #1ed760;
                color: #ffffff;
                padding: 15px;
                border-radius: 8px;
                margin-bottom: 20px;
                display: none;
            }

            .results {
                display: none;
            }

            .results h3 {
                font-size: 18px;
                margin-bottom: 20px;
                color: #1db954;
            }

            .artist-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
                gap: 20px;
            }

            .artist-card {
                background: rgba(30, 30, 30, 0.6);
                border: 1px solid #282828;
                border-radius: 8px;
                padding: 15px;
                text-align: center;
                transition: all 0.3s ease;
            }

            .artist-card:hover {
                border-color: #1db954;
                transform: translateY(-4px);
                background: rgba(29, 185, 84, 0.1);
            }

            .artist-image {
                width: 100%;
                aspect-ratio: 1;
                border-radius: 8px;
                object-fit: cover;
                margin-bottom: 12px;
                background: #282828;
            }

            .artist-name {
                font-size: 16px;
                font-weight: 600;
                margin-bottom: 5px;
            }

            .artist-rank {
                font-size: 12px;
                color: #b3b3b3;
            }

            .pagination {
                display: flex;
                justify-content: center;
                gap: 10px;
                margin-top: 30px;
            }

            .page-btn {
                background-color: #333333;
                color: #ffffff;
                border: none;
                padding: 8px 12px;
                border-radius: 4px;
                cursor: pointer;
                transition: background-color 0.3s ease;
            }

            .page-btn:hover:not(:disabled) {
                background-color: #1db954;
            }

            .page-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            .page-btn.active {
                 background-color: #1db954;
             }

             .features-card {
                 background: rgba(30, 30, 30, 0.6);
                 border: 1px solid #282828;
                 border-radius: 8px;
                 padding: 25px;
                 max-width: 500px;
             }

             .feature-item {
                 margin-bottom: 20px;
             }

             .feature-label {
                 font-size: 14px;
                 color: #b3b3b3;
                 margin-bottom: 8px;
             }

             .feature-value {
                 font-size: 18px;
                 font-weight: 600;
                 color: #1db954;
             }

             .feature-bar {
                 background: #282828;
                 height: 6px;
                 border-radius: 3px;
                 margin-top: 8px;
                 overflow: hidden;
             }

             .feature-bar-fill {
                 background: linear-gradient(90deg, #1db954, #1ed760);
                 height: 100%;
                 border-radius: 3px;
             }

             .track-title {
                 margin-bottom: 20px;
             }

             .track-title .track-name {
                 font-size: 22px;
                 font-weight: 700;
                 color: #ffffff;
             }

             .track-title .track-artist {
                 font-size: 14px;
                 color: #b3b3b3;
                 margin-top: 5px;
             }
            </style>
    </head>
    <body>
        <div class="header">
            <h1>🎵 Spotify Stats</h1>
            <button class="logout-btn" onclick="logout()">Logout</button>
        </div>

        <div class="container">
             <div class="fetch-section">
                 <h2>Explore Your Top Artists</h2>
                 <p>Fetch your top 50 artists from Spotify and save them locally</p>
                 <button class="fetch-btn" id="fetch-btn" onclick="fetchTopArtists()">Fetch Top 50 Artists</button>
             </div>

             <div class="fetch-section">
                 <h2>Export Track Features</h2>
                 <p>Get audio features for your #1 track</p>
                 <button class="fetch-btn" id="export-btn" onclick="exportTrackFeatures()">Get Track Features</button>
             </div>

             <div class="error" id="error-message"></div>
             <div class="success" id="success-message"></div>

             <div class="loading" id="loading">
                 <div class="spinner"></div>
                 <p>Fetching your top artists...</p>
             </div>

             <div class="results" id="results">
                 <h3>Your Top 50 Artists</h3>
                 <div class="artist-grid" id="artists-grid"></div>
                 <div class="pagination" id="pagination"></div>
             </div>

             <div class="results" id="features-results">
                 <h3 id="features-title"></h3>
                 <div class="features-card" id="features-card"></div>
             </div>
        </div>

        <script>
            const ARTISTS_PER_PAGE = 10;
            let allArtists = [];
            let currentPage = 1;

            async function logout() {
                localStorage.removeItem('user_id');
                localStorage.removeItem('access_token');
                window.location.href = '/';
            }

            async function fetchTopArtists() {
                const userId = localStorage.getItem('user_id');
                const token = localStorage.getItem('access_token');

                if (!userId || !token) {
                    showError('Not authenticated. Please log in again.');
                    window.location.href = '/';
                    return;
                }

                document.getElementById('fetch-btn').disabled = true;
                document.getElementById('loading').style.display = 'block';
                document.getElementById('error-message').style.display = 'none';
                document.getElementById('success-message').style.display = 'none';
                document.getElementById('results').style.display = 'none';

                try {
                    const res = await fetch(`/api/data/top-artists?user_id=${userId}&limit=50`);
                    if (!res.ok) throw new Error('Failed to fetch artists');

                    const data = await res.json();
                    allArtists = data.items || [];

                    if (allArtists.length === 0) {
                        showError('No artists found. Try again later.');
                        return;
                    }

                    currentPage = 1;
                    displayArtists();
                    showSuccess(`Successfully fetched and saved ${allArtists.length} artists!`);
                    document.getElementById('results').style.display = 'block';
                } catch (err) {
                    console.error('Error:', err);
                    showError('Failed to fetch artists. Please try again.');
                } finally {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('fetch-btn').disabled = false;
                }
            }

            function displayArtists() {
                const grid = document.getElementById('artists-grid');
                grid.innerHTML = '';

                const start = (currentPage - 1) * ARTISTS_PER_PAGE;
                const end = start + ARTISTS_PER_PAGE;
                const pageArtists = allArtists.slice(start, end);

                pageArtists.forEach((artist, index) => {
                    const rank = start + index + 1;
                    const card = document.createElement('div');
                    card.className = 'artist-card';
                    card.innerHTML = `
                        ${artist.images && artist.images[0] ? `<img src="${artist.images[0].url}" alt="${artist.name}" class="artist-image">` : '<div class="artist-image"></div>'}
                        <div class="artist-name">${artist.name}</div>
                        <div class="artist-rank">#${rank}</div>
                    `;
                    grid.appendChild(card);
                });

                updatePagination();
            }

            function updatePagination() {
                const totalPages = Math.ceil(allArtists.length / ARTISTS_PER_PAGE);
                const pagination = document.getElementById('pagination');
                pagination.innerHTML = '';

                for (let i = 1; i <= totalPages; i++) {
                    const btn = document.createElement('button');
                    btn.className = `page-btn ${i === currentPage ? 'active' : ''}`;
                    btn.textContent = i;
                    btn.disabled = i === currentPage;
                    btn.onclick = () => {
                        currentPage = i;
                        displayArtists();
                    };
                    pagination.appendChild(btn);
                }
            }

            function showError(message) {
                const errorDiv = document.getElementById('error-message');
                errorDiv.textContent = message;
                errorDiv.style.display = 'block';
            }

            function showSuccess(message) {
                 const successDiv = document.getElementById('success-message');
                 successDiv.textContent = message;
                 successDiv.style.display = 'block';
             }

             async function exportTrackFeatures() {
                 const userId = localStorage.getItem('user_id');
                 const token = localStorage.getItem('access_token');

                 if (!userId || !token) {
                     showError('Not authenticated. Please log in again.');
                     window.location.href = '/';
                     return;
                 }

                 document.getElementById('export-btn').disabled = true;
                 document.getElementById('loading').style.display = 'block';
                 document.getElementById('error-message').style.display = 'none';
                 document.getElementById('success-message').style.display = 'none';
                 document.getElementById('results').style.display = 'none';
                 document.getElementById('features-results').style.display = 'none';
                 document.getElementById('loading').querySelector('p').textContent = 'Fetching track features...';

                 try {
                     const res = await fetch(`/api/data/export-track-features?user_id=${userId}&time_range=short_term`);
                     if (!res.ok) throw new Error('Failed to fetch track features');

                     const data = await res.json();
                     displayTrackFeatures(data);
                 } catch (err) {
                     console.error('Error:', err);
                     showError('Failed to fetch track features. Please try again.');
                 } finally {
                     document.getElementById('loading').style.display = 'none';
                     document.getElementById('export-btn').disabled = false;
                     document.getElementById('loading').querySelector('p').textContent = 'Fetching your top artists...';
                 }
             }

             function displayTrackFeatures(data) {
                 const track = data.track;
                 const features = data.audio_features;

                 document.getElementById('features-title').textContent = '#1 Track: Audio Features';
                 const card = document.getElementById('features-card');
                 
                 card.innerHTML = `
                     <div class="track-title">
                         <div class="track-name">${track.name}</div>
                         <div class="track-artist">by ${track.artist}</div>
                     </div>
                     <div class="feature-item">
                         <div class="feature-label">Danceability</div>
                         <div class="feature-value">${(features.danceability * 100).toFixed(1)}%</div>
                         <div class="feature-bar">
                             <div class="feature-bar-fill" style="width: ${features.danceability * 100}%"></div>
                         </div>
                     </div>
                     <div class="feature-item">
                         <div class="feature-label">Energy</div>
                         <div class="feature-value">${(features.energy * 100).toFixed(1)}%</div>
                         <div class="feature-bar">
                             <div class="feature-bar-fill" style="width: ${features.energy * 100}%"></div>
                         </div>
                     </div>
                     <div class="feature-item">
                         <div class="feature-label">Valence (Happiness)</div>
                         <div class="feature-value">${(features.valence * 100).toFixed(1)}%</div>
                         <div class="feature-bar">
                             <div class="feature-bar-fill" style="width: ${features.valence * 100}%"></div>
                         </div>
                     </div>
                     <div class="feature-item">
                         <div class="feature-label">Acousticness</div>
                         <div class="feature-value">${(features.acousticness * 100).toFixed(1)}%</div>
                         <div class="feature-bar">
                             <div class="feature-bar-fill" style="width: ${features.acousticness * 100}%"></div>
                         </div>
                     </div>
                     <div class="feature-item">
                         <div class="feature-label">Tempo</div>
                         <div class="feature-value">${features.tempo.toFixed(1)} BPM</div>
                     </div>
                 `;
                 
                 document.getElementById('features-results').style.display = 'block';
             }

             window.addEventListener('load', () => {
                 const userId = localStorage.getItem('user_id');
                 const token = localStorage.getItem('access_token');
                 if (!userId || !token) {
                     window.location.href = '/';
                 }
             });
        </script>
    </body>
    </html>
    """
