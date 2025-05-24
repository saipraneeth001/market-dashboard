document.addEventListener('DOMContentLoaded', function() {
    const updateInterval = 30000; // 30 seconds in milliseconds
    const dashboardContent = document.getElementById('dashboard-content');
    const lastUpdatedSpan = document.getElementById('last-updated');
    const navLinks = document.querySelectorAll('.main-nav a');

    let currentView = 'home'; // Default view

    // Templates for different views
    const homeTemplate = (data) => `
        <div class="card-container">
            <div class="card">
                <h2>NSE Data</h2>
                <p>LTP: <span>${data.nse_ltp !== undefined ? data.nse_ltp : 'N/A'}</span></p>
                <p>Prev Day High: <span>${data.nse_pdh !== undefined ? data.nse_pdh : 'N/A'}</span></p>
                <p>Prev Day Low: <span>${data.nse_pdl !== undefined ? data.nse_pdl : 'N/A'}</span></p>
                <p>Current Day High: <span>${data.nse_cdh !== undefined ? data.nse_cdh : 'N/A'}</span></p>
                <p>Current Day Low: <span>${data.nse_cdl !== undefined ? data.nse_cdl : 'N/A'}</span></p>
                <p>HH: <span>${data.nse_hh !== undefined ? data.nse_hh : 'N/A'}</span></p>
                <p>LL: <span>${data.nse_ll !== undefined ? data.nse_ll : 'N/A'}</span></p>
                <p>ILL: <span>${data.nse_ill !== undefined ? data.nse_ill : 'N/A'}</span></p>
                <p>IHH: <span>${data.nse_ihh !== undefined ? data.nse_ihh : 'N/A'}</span></p>
                <p>C2C: <span>${data.nse_c2c !== undefined ? data.nse_c2c : 'N/A'}</span></p>
            </div>

            <div class="card">
                <h2>BSE Data</h2>
                <p>LTP: <span>${data.bse_ltp !== undefined ? data.bse_ltp : 'N/A'}</span></p>
                <p>Prev Day High: <span>${data.bse_pdh !== undefined ? data.bse_pdh : 'N/A'}</span></p>
                <p>Prev Day Low: <span>${data.bse_pdl !== undefined ? data.bse_pdl : 'N/A'}</span></p>
                <p>Current Day High: <span>${data.bse_cdh !== undefined ? data.bse_cdh : 'N/A'}</span></p>
                <p>Current Day Low: <span>${data.bse_cdl !== undefined ? data.bse_cdl : 'N/A'}</span></p>
                <p>HH: <span>${data.bse_hh !== undefined ? data.bse_hh : 'N/A'}</span></p>
                <p>LL: <span>${data.bse_ll !== undefined ? data.bse_ll : 'N/A'}</span></p>
                <p>ILL: <span>${data.bse_ill !== undefined ? data.bse_ill : 'N/A'}</span></p>
                <p>IHH: <span>${data.bse_ihh !== undefined ? data.bse_ihh : 'N/A'}</span></p>
                <p>C2C: <span>${data.bse_c2c !== undefined ? data.bse_c2c : 'N/A'}</span></p>
            </div>
            
            <div class="card vix-card">
                <h2>VIX</h2>
                <p>Value: <span>${data.vix !== undefined ? data.vix : 'N/A'}</span></p>
            </div>
        </div>
    `;

    const nseTemplate = (data) => `
        <div class="card-container">
            <div class="card full-width">
                <h2>NSE Data & VIX</h2>
                <p>LTP: <span>${data.nse_ltp !== undefined ? data.nse_ltp : 'N/A'}</span></p>
                <p>Prev Day High: <span>${data.nse_pdh !== undefined ? data.nse_pdh : 'N/A'}</span></p>
                <p>Prev Day Low: <span>${data.nse_pdl !== undefined ? data.nse_pdl : 'N/A'}</span></p>
                <p>Current Day High: <span>${data.nse_cdh !== undefined ? data.nse_cdh : 'N/A'}</span></p>
                <p>Current Day Low: <span>${data.nse_cdl !== undefined ? data.nse_cdl : 'N/A'}</span></p>
                <p>HH: <span>${data.nse_hh !== undefined ? data.nse_hh : 'N/A'}</span></p>
                <p>LL: <span>${data.nse_ll !== undefined ? data.nse_ll : 'N/A'}</span></p>
                <p>ILL: <span>${data.nse_ill !== undefined ? data.nse_ill : 'N/A'}</span></p>
                <p>IHH: <span>${data.nse_ihh !== undefined ? data.nse_ihh : 'N/A'}</span></p>
                <p>C2C: <span>${data.nse_c2c !== undefined ? data.nse_c2c : 'N/A'}</span></p>
                <p>VIX: <span>${data.vix !== undefined ? data.vix : 'N/A'}</span></p>
            </div>
        </div>
    `;

    const bseTemplate = (data) => `
        <div class="card-container">
            <div class="card full-width">
                <h2>BSE Data</h2>
                <p>LTP: <span>${data.bse_ltp !== undefined ? data.bse_ltp : 'N/A'}</span></p>
                <p>Prev Day High: <span>${data.bse_pdh !== undefined ? data.bse_pdh : 'N/A'}</span></p>
                <p>Prev Day Low: <span>${data.bse_pdl !== undefined ? data.bse_pdl : 'N/A'}</span></p>
                <p>Current Day High: <span>${data.bse_cdh !== undefined ? data.bse_cdh : 'N/A'}</span></p>
                <p>Current Day Low: <span>${data.bse_cdl !== undefined ? data.bse_cdl : 'N/A'}</span></p>
                <p>HH: <span>${data.bse_hh !== undefined ? data.bse_hh : 'N/A'}</span></p>
                <p>LL: <span>${data.bse_ll !== undefined ? data.bse_ll : 'N/A'}</span></p>
                <p>ILL: <span>${data.bse_ill !== undefined ? data.bse_ill : 'N/A'}</span></p>
                <p>IHH: <span>${data.bse_ihh !== undefined ? data.bse_ihh : 'N/A'}</span></p>
                <p>C2C: <span>${data.bse_c2c !== undefined ? data.bse_c2c : 'N/A'}</span></p>
            </div>
        </div>
    `;

    // Function to fetch data and update the display
    async function updateDashboard() {
        let apiUrl = '';
        let templateFunction;

        if (currentView === 'home') {
            apiUrl = '/api/data';
            templateFunction = homeTemplate;
        } else if (currentView === 'nse') {
            apiUrl = '/api/nse_data';
            templateFunction = nseTemplate;
        } else if (currentView === 'bse') {
            apiUrl = '/api/bse_data';
            templateFunction = bseTemplate;
        }

        try {
            const response = await fetch(apiUrl);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();
            console.log(`Received data for ${currentView}:`, data); // For debugging

            dashboardContent.innerHTML = templateFunction(data);
            
            const now = new Date();
            lastUpdatedSpan.textContent = `Last Updated: ${now.toLocaleTimeString()}`;

        } catch (error) {
            console.error(`Error fetching data for ${currentView}:`, error);
            dashboardContent.innerHTML = `<p class="error-message">Error loading data for ${currentView}. Please try again later.</p>`;
            lastUpdatedSpan.textContent = `Last Updated: Error (${new Date().toLocaleTimeString()})`;
        }
    }

    // Event listeners for navigation links
    navLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent default link behavior (page reload)

            // Remove active class from all links
            navLinks.forEach(item => item.classList.remove('active'));
            // Add active class to the clicked link
            this.classList.add('active');

            currentView = this.dataset.view; // Get the data-view attribute
            updateDashboard(); // Update content for the new view immediately
        });
    });

    // Initialize the dashboard on page load (defaults to home view)
    updateDashboard();

    // Set up interval to update the dashboard for the currently selected view
    setInterval(updateDashboard, updateInterval);
});