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
                border-radius: 20px;
                cursor: pointer;
                transition: all 0.3s ease;
                font-size: 14px;
            }

            .logout-btn:hover {
                background-color: #1db954;
            }

            .container {
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px 20px;
            }

            .fetch-section {
                background: rgba(30, 30, 30, 0.8);
                border: 1px solid #282828;
                border-radius: 8px;
                padding: 24px;
                margin-bottom: 24px;
            }

            .fetch-section h2 {
                font-size: 20px;
                margin-bottom: 8px;
            }

            .fetch-section p {
                color: #b3b3b3;
                margin-bottom: 16px;
            }

            .fetch-btn {
                background-color: #1db954;
                color: #ffffff;
                border: none;
                padding: 10px 24px;
                border-radius: 24px;
                cursor: pointer;
                font-weight: 600;
                transition: all 0.3s ease;
            }

            .fetch-btn:hover:not(:disabled) {
                background-color: #1ed760;
                transform: scale(1.02);
            }

            .fetch-btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
            }

            .error {
                background-color: #ff4444;
                color: #ffffff;
                padding: 16px;
                border-radius: 8px;
                margin: 20px 0;
                display: none;
            }

            .success {
                background-color: #1db954;
                color: #ffffff;
                padding: 16px;
                border-radius: 8px;
                margin: 20px 0;
                display: none;
            }

            .loading {
                text-align: center;
                padding: 40px;
                display: none;
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

            .results {
                background: rgba(30, 30, 30, 0.8);
                border: 1px solid #282828;
                border-radius: 8px;
                padding: 24px;
                margin-top: 24px;
                display: none;
            }

            .results h3 {
                font-size: 20px;
                margin-bottom: 20px;
            }

            .artist-grid {
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
                gap: 16px;
                margin-bottom: 20px;
            }

            .artist-card {
                background: rgba(40, 40, 40, 0.6);
                border-radius: 8px;
                padding: 12px;
                text-align: center;
                cursor: pointer;
                transition: all 0.3s ease;
                border: 1px solid #282828;
            }

            .artist-card:hover {
                background: rgba(50, 50, 50, 0.8);
                border-color: #1db954;
            }

            .artist-image {
                width: 100%;
                aspect-ratio: 1;
                border-radius: 8px;
                background-color: #282828;
                margin-bottom: 12px;
                object-fit: cover;
            }

            .artist-name {
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 8px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }

            .artist-rank {
                font-size: 12px;
                color: #1db954;
                font-weight: 700;
            }

            .pagination {
                display: flex;
                gap: 8px;
                justify-content: center;
                margin-top: 20px;
            }

            .page-btn {
                background-color: #333333;
                color: #ffffff;
                border: 1px solid #282828;
                padding: 8px 12px;
                border-radius: 4px;
                cursor: pointer;
                transition: all 0.3s ease;
            }

            .page-btn:hover:not(:disabled) {
                background-color: #1db954;
            }

            .page-btn.active {
                background-color: #1db954;
            }

            .page-btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            .features-card {
                background: rgba(40, 40, 40, 0.6);
                border: 1px solid #282828;
                border-radius: 8px;
                padding: 20px;
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
                margin-bottom: 8px;
            }

            .feature-bar {
                background-color: #282828;
                border-radius: 4px;
                height: 8px;
                overflow: hidden;
            }

            .feature-bar-fill {
                background-color: #1db954;
                height: 100%;
                border-radius: 4px;
                transition: width 0.3s ease;
            }

            .track-name {
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
                try {
                    await fetch('/api/auth/logout', { 
                        method: 'POST',
                        credentials: 'include'
                    });
                } catch (err) {
                    console.error('Logout error:', err);
                }
                window.location.href = '/';
            }

            async function fetchTopArtists() {
                document.getElementById('fetch-btn').disabled = true;
                document.getElementById('loading').style.display = 'block';
                document.getElementById('error-message').style.display = 'none';
                document.getElementById('success-message').style.display = 'none';
                document.getElementById('results').style.display = 'none';

                try {
                    const res = await fetch(`/api/data/top-artists?limit=50`, {
                        credentials: 'include'
                    });
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

             window.addEventListener('load', () => {
                 // Session authentication is handled by cookies automatically
                 // If user is not authenticated, the API will return 401
                 // and redirect will happen from the fetch error handler
             });
        </script>
    </body>
    </html>
    """
