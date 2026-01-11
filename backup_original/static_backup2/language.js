document.addEventListener('DOMContentLoaded', function() {
    const langSelect = document.getElementById('languageSelect');
    if (langSelect) {
        langSelect.addEventListener('change', function() {
            const lang = this.value;
            fetch('/set_language', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: 'language=' + lang
            }).then(() => {
                location.reload();
            });
        });
    }
});
