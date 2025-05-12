// static/js/direct-navigation.js
document.addEventListener('DOMContentLoaded', function() {
    // Intercept both /view_execution/ and /execution_details/
    document.querySelectorAll('a[href^="/view_execution/"], a[href^="/execution_details/"]').forEach(link => {
        link.addEventListener('click', e => {
            e.preventDefault();
            window.location.href = link.href;
        });
    });
});
