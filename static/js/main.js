// static/js/main.js

// Initialize Socket.IO connection
let socket;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize Socket.IO
    initializeSocket();
    
    // Add event listener for API key toggle
    const toggleApiKeyBtn = document.getElementById('toggleApiKeyBtn');
    if (toggleApiKeyBtn) {
        toggleApiKeyBtn.addEventListener('click', function() {
            const input = document.getElementById('openaiApiKey');
            const icon = this.querySelector('i');
            
            if (input.type === 'password') {
                input.type = 'text';
                icon.className = 'bi bi-eye-slash';
            } else {
                input.type = 'password';
                icon.className = 'bi bi-eye';
            }
        });
    }
    
    // Format dates and times
    formatDates();
});

// Initialize Socket.IO connection
function initializeSocket() {
    socket = io({
        withCredentials: true,
        transportOptions: {
            polling: {
                extraHeaders: {
                    'X-CSRFToken': document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || ''
                }
            }
        }
    });
    
    // Listen for script status updates
    socket.on('script_status_update', function(data) {
        console.log('Script status update received:', data);
        
        // Find elements that might need to be updated based on execution ID
        const statusElements = document.querySelectorAll(`[data-execution-id="${data.execution_id}"]`);
        if (statusElements.length > 0) {
            // Update status badges
            updateStatusBadges(statusElements, data.status);
            
            // Hide cancel button if the script is no longer running
            if (data.status !== 'Running') {
                const cancelButtons = document.querySelectorAll(`.cancel-execution-btn[data-execution-id="${data.execution_id}"]`);
                cancelButtons.forEach(button => {
                    button.style.display = 'none';
                });
            }
        }
        
        // Also check for table rows by execution ID
        const executionRow = document.querySelector(`tr[data-execution-id="${data.execution_id}"]`);
        if (executionRow) {
            // Find the status cell (should be the 3rd column)
            const statusCell = executionRow.querySelector('td:nth-child(3)');
            if (statusCell) {
                updateStatusCell(statusCell, data.status);
            }
        }
    });
    
    // Listen for script output updates
    socket.on('script_output_update', function(data) {
        console.log('Script output update for execution:', data.execution_id);
        
        // Find output container
        const outputContainer = document.getElementById('execution-output');
        if (outputContainer) {
            const preElement = outputContainer.querySelector('pre');
            
            if (preElement) {
                // Append new output
                preElement.textContent += data.output;
                // Scroll to bottom
                preElement.scrollTop = preElement.scrollHeight;
            } else {
                // Create new output display
                outputContainer.innerHTML = `<pre class="bg-dark text-light p-3" style="max-height: 500px; overflow-y: auto;">${data.output}</pre>`;
            }
            
            // Show interactive input if requested
            if (data.waiting_for_input) {
                const inputContainer = document.getElementById('interactive-input-container');
                if (inputContainer) {
                    inputContainer.style.display = 'block';
                    document.getElementById('interactive-input').focus();
                }
            }
        }
    });
}

// Update status cell in the table
function updateStatusCell(cell, status) {
    // Check that we are updating the correct cell
    if (!cell || cell.cellIndex === 1) { // 1 is the index of the SCRIPT column (second column, counting from 0)
        console.warn("Attempt to update an invalid cell or script column cell");
        return; // Abort update if this is the script column
    }
    
    // Clear the cell content to prevent duplication
    cell.innerHTML = '';
    
    // Create the appropriate badge based on status
    let badgeClass = '';
    let badgeIcon = '';
    let statusText = status;
    
    switch (status) {
        case 'Running':
            badgeClass = 'badge-running';
            badgeIcon = 'ti-player-play';
            statusText = `<span class="live-dot"></span>${status}`;
            break;
        case 'Success':
            badgeClass = 'bg-success';
            badgeIcon = 'ti-check';
            statusText = `<i class="ti ${badgeIcon} me-1"></i>${status}`;
            break;
        case 'Failed':
            badgeClass = 'bg-danger';
            badgeIcon = 'ti-x';
            statusText = `<i class="ti ${badgeIcon} me-1"></i>${status}`;
            break;
        case 'Cancelled':
            badgeClass = 'bg-warning';
            badgeIcon = 'ti-ban';
            statusText = `<i class="ti ${badgeIcon} me-1"></i>${status}`;
            break;
        default:
            badgeClass = 'bg-secondary';
            badgeIcon = 'ti-circle';
            statusText = `<i class="ti ${badgeIcon} me-1"></i>${status}`;
    }
    
    // Create badge
    const badge = document.createElement('span');
    badge.className = `badge ${badgeClass} status-changed`;
    badge.innerHTML = statusText;
    
    // Add to cell
    cell.appendChild(badge);
}

// Update status badges when status changes
function updateStatusBadges(elements, status) {
    elements.forEach(element => {
        // Skip elements that are not status badges
        if (!element.classList.contains('badge') && !element.querySelector('.badge')) {
            return;
        }
        
        // Remove existing status classes
        const badge = element.classList.contains('badge') ? element : element.querySelector('.badge');
        if (!badge) return; // Skip if no badge found
        
        badge.classList.remove('bg-primary', 'bg-success', 'bg-danger', 'bg-secondary', 'bg-warning', 'badge-running');
        
        // Add appropriate class and update text
        switch (status) {
            case 'Running':
                badge.classList.add('badge-running');
                badge.innerHTML = `<span class="live-dot"></span>${status}`;
                break;
            case 'Success':
                badge.classList.add('bg-success');
                badge.innerHTML = `<i class="ti ti-check me-1"></i>${status}`;
                break;
            case 'Failed':
                badge.classList.add('bg-danger');
                badge.innerHTML = `<i class="ti ti-x me-1"></i>${status}`;
                break;
            case 'Cancelled':
                badge.classList.add('bg-warning');
                badge.innerHTML = `<i class="ti ti-ban me-1"></i>${status}`;
                break;
            default:
                badge.classList.add('bg-secondary');
                badge.innerHTML = `<i class="ti ti-circle me-1"></i>${status}`;
        }
    });
    
    // If we're on the execution history page, we might want to refresh it
    if (window.location.pathname === '/execution_history') {
        setTimeout(() => {
            if (typeof loadExecutionHistory === 'function') {
                loadExecutionHistory();
            }
        }, 1000);
    }
}

// Format dates in a user-friendly way
function formatDates() {
    document.querySelectorAll('.format-date').forEach(element => {
        try {
            const dateString = element.textContent;
            if (dateString && dateString !== '-') {
                const date = new Date(dateString);
                element.textContent = date.toLocaleString();
            }
        } catch (e) {
            console.error('Error formatting date:', e);
        }
    });
}

// Helper function to calculate and display duration
function formatDuration(startTime, endTime) {
    if (!startTime || !endTime || startTime === '-' || endTime === '-') {
        return '-';
    }
    
    try {
        const start = new Date(startTime);
        const end = new Date(endTime);
        const diff = Math.floor((end - start) / 1000);
        
        const minutes = Math.floor(diff / 60);
        const seconds = diff % 60;
        
        return `${minutes}m ${seconds}s`;
    } catch (e) {
        console.error('Error calculating duration:', e);
        return '-';
    }
}

// Send interactive input to a running script
function sendInput(executionId, input) {
    if (!socket || !executionId || !input) {
        return;
    }
    
    // Send the input to the server
    socket.emit('send_input', {
        execution_id: executionId,
        input: input
    });
    
    console.log('Sent input for execution:', executionId);
}