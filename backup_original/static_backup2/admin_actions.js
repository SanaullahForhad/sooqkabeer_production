document.addEventListener('DOMContentLoaded', function() {
    // Edit button
    document.querySelectorAll('.btn-edit').forEach(btn => {
        btn.addEventListener('click', function() {
            const row = this.closest('tr');
            const id = row.querySelector('td:first-child').textContent;
            alert('Edit product ID: ' + id);
        });
    });
    
    // Delete button
    document.querySelectorAll('.btn-delete').forEach(btn => {
        btn.addEventListener('click', function() {
            if (confirm('Are you sure?')) {
                const row = this.closest('tr');
                const id = row.querySelector('td:first-child').textContent;
                alert('Delete product ID: ' + id);
            }
        });
    });
});
