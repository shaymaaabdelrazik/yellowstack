/**
 * Shows a popup notification
 * @param {string} message - message to display
 * @param {string} type - notification type: success, error, info, warning
 * @param {string} title - notification title (optional)
 * @param {number} duration - display time in ms (default 3000ms)
 */
function showToast(message, type = 'success', title = '', duration = 3000) {
    // Check if notification container exists
    let toastContainer = document.querySelector('.toast-container');
    
    if (!toastContainer) {
        // Create container if it doesn't exist
        toastContainer = document.createElement('div');
        toastContainer.className = 'toast-container';
        document.body.appendChild(toastContainer);
    }
    
    // Select icon based on notification type
    let iconClass = '';
    switch (type) {
        case 'success':
            iconClass = 'ti ti-check';
            title = title || 'Success';
            break;
        case 'error':
            iconClass = 'ti ti-alert-circle';
            title = title || 'Error';
            break;
        case 'warning':
            iconClass = 'ti ti-alert-triangle';
            title = title || 'Warning';
            break;
        case 'info':
            iconClass = 'ti ti-info-circle';
            title = title || 'Information';
            break;
    }
    
    // Create notification element
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <div class="toast-icon ${type}">
            <i class="${iconClass}"></i>
        </div>
        <div class="toast-content">
            <div class="toast-title">${title}</div>
            <div class="toast-message">${message}</div>
        </div>
        <div class="toast-close">
            <i class="ti ti-x"></i>
        </div>
    `;
    
    // Add to container
    toastContainer.appendChild(toast);
    
    // Start appearance animation
    setTimeout(() => {
        toast.classList.add('show');
    }, 10);
    
    // Configure notification hiding
    const closeToast = () => {
        toast.classList.remove('show');
        toast.classList.add('hide');
        
        // Remove element after animation completes
        setTimeout(() => {
            toast.remove();
        }, 300);
    };
    
    // Automatic hiding after specified time
    const autoHideTimeout = setTimeout(closeToast, duration);
    
    // Click handler for close button
    const closeBtn = toast.querySelector('.toast-close');
    closeBtn.addEventListener('click', () => {
        clearTimeout(autoHideTimeout);
        closeToast();
    });
    
    // Return notification element (may be useful)
    return toast;
}

function showConfirmDialog(message, onConfirm, onCancel) {
    // Check if modal window already exists
    let confirmModal = document.getElementById('confirmActionModal');
    
    if (!confirmModal) {
        // Create modal window
        confirmModal = document.createElement('div');
        confirmModal.className = 'modal fade';
        confirmModal.id = 'confirmActionModal';
        confirmModal.tabIndex = '-1';
        confirmModal.setAttribute('aria-labelledby', 'confirmActionModalLabel');
        confirmModal.setAttribute('aria-hidden', 'true');
        
        confirmModal.innerHTML = `
            <div class="modal-dialog modal-dialog-centered">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="confirmActionModalLabel">Confirmation</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body" id="confirmActionMessage">
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal" id="cancelConfirmBtn">Cancel</button>
                        <button type="button" class="btn btn-danger" id="confirmActionBtn">Confirm</button>
                    </div>
                </div>
            </div>
        `;
        
        document.body.appendChild(confirmModal);
    }
    
    // Update message
    const messageEl = document.getElementById('confirmActionMessage');
    messageEl.textContent = message;
    
    // Create modal instance
    const modal = new bootstrap.Modal(confirmModal);
    
    // Add event handlers
    const confirmBtn = document.getElementById('confirmActionBtn');
    const cancelBtn = document.getElementById('cancelConfirmBtn');
    const closeBtn = confirmModal.querySelector('.btn-close');
    
    // Remove old handlers if they exist
    const newConfirmBtn = confirmBtn.cloneNode(true);
    confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
    
    const newCancelBtn = cancelBtn.cloneNode(true);
    cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);
    
    const newCloseBtn = closeBtn.cloneNode(true);
    closeBtn.parentNode.replaceChild(newCloseBtn, closeBtn);
    
    // Add new handlers
    newConfirmBtn.addEventListener('click', function() {
        modal.hide();
        if (typeof onConfirm === 'function') {
            onConfirm();
        }
    });
    
    function handleCancel() {
        if (typeof onCancel === 'function') {
            onCancel();
        }
    }
    
    newCancelBtn.addEventListener('click', function() {
        modal.hide();
        handleCancel();
    });
    
    newCloseBtn.addEventListener('click', function() {
        handleCancel();
    });
    
    // Handler for modal window close
    confirmModal.addEventListener('hidden.bs.modal', function() {
        handleCancel();
    }, { once: true });
    
    // Show modal window
    modal.show();
}