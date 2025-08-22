// Custom javascript scripts here

// Global Bootstrap Popover Click-Outside Close Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Handle click outside to close popovers
    document.addEventListener('click', function(event) {
        // Skip if clicking on dropdown elements
        if (event.target.closest('[data-bs-toggle="dropdown"]') || 
            event.target.closest('.dropdown-menu')) {
            return;
        }
        
        // Get all popover trigger elements
        const popoverTriggers = document.querySelectorAll('[data-bs-toggle="popover"]');
        
        popoverTriggers.forEach(function(trigger) {
            const popoverInstance = bootstrap.Popover.getInstance(trigger);
            
            if (popoverInstance) {
                const popoverElement = document.querySelector('.popover');
                
                // Check if click is outside both trigger and popover
                if (!trigger.contains(event.target) && 
                    (!popoverElement || !popoverElement.contains(event.target))) {
                    popoverInstance.hide();
                }
            }
        });
    });
    
    // Also handle escape key to close popovers
    document.addEventListener('keydown', function(event) {
        if (event.key === 'Escape') {
            const popoverTriggers = document.querySelectorAll('[data-bs-toggle="popover"]');
            popoverTriggers.forEach(function(trigger) {
                const popoverInstance = bootstrap.Popover.getInstance(trigger);
                if (popoverInstance) {
                    popoverInstance.hide();
                }
            });
        }
    });
});
