document.addEventListener('DOMContentLoaded', function() {
    // Set the interval for updating dashboard data (30 seconds)
    const updateInterval = 30000; // 30 seconds in milliseconds
    
    // Get references to DOM elements
    const dashboardContent = document.getElementById('dashboard-content');
    const lastUpdatedSpan = document.getElementById('last-updated');
    const navLinks = document.querySelectorAll('.main-nav a');

    // Initialize the current view to 'home'
    let currentView = 'home'; 

    // Template function for the 'Home' view (displays both NSE and BSE data, plus VIX)
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

    // Template function for the 'NSE' view (displays only NSE data and VIX)
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

    // Template function for the 'BSE' view (displays only BSE data)
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

    // Function to fetch data from the backend API and update the dashboard display
    async function updateDashboard() {
        let apiUrl = ''; // API endpoint to call
        let templateFunction; // Template to use for rendering

        // Determine the API URL and template function based on the current view
        if (currentView === 'home') {
            apiUrl = '/api/data'; // Fetches all data
            templateFunction = homeTemplate;
        } else if (currentView === 'nse') {
            apiUrl = '/api/nse_data'; // Fetches only NSE data
            templateFunction = nseTemplate;
        } else if (currentView === 'bse') {
            apiUrl = '/api/bse_data'; // Fetches only BSE data
            templateFunction = bseTemplate;
        }

        try {
            // Fetch data from the Flask backend
            const response = await fetch(apiUrl);
            // Check if the HTTP response was successful
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            // Parse the JSON response
            const data = await response.json();
            console.log(`Received data for ${currentView}:`, data); // For debugging purposes

            // Render the fetched data using the appropriate template
            dashboardContent.innerHTML = templateFunction(data);
            
            // Update the "Last Updated" timestamp
            const now = new Date();
            lastUpdatedSpan.textContent = `Last Updated: ${now.toLocaleTimeString()}`;

        } catch (error) {
            // Handle any errors during the fetch operation
            console.error(`Error fetching data for ${currentView}:`, error);
            dashboardContent.innerHTML = `<p class="error-message">Error loading data for ${currentView}. Please try again later.</p>`;
            lastUpdatedSpan.textContent = `Last Updated: Error (${new Date().toLocaleTimeString()})`;
        }
    }

    // Add event listeners to navigation links
    navLinks.forEach(link => {
        link.addEventListener('click', function(event) {
            event.preventDefault(); // Prevent default link behavior (page reload)

            // Remove 'active' class from all navigation links
            navLinks.forEach(item => item.classList.remove('active'));
            // Add 'active' class to the clicked link to highlight it
            this.classList.add('active');

            // Update the current view based on the data-view attribute of the clicked link
            currentView = this.dataset.view; 
            // Immediately update the dashboard content for the new view
            updateDashboard(); 
        });
    });

    // Initialize the dashboard display when the page loads (defaults to 'home' view)
    updateDashboard();

    // Set up an interval to periodically update the dashboard data
    // This will call updateDashboard() every 'updateInterval' milliseconds
    setInterval(updateDashboard, updateInterval);
});
