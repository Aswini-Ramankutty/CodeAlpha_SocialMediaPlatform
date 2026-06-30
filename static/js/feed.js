/* Feed page specific JS */
document.addEventListener('DOMContentLoaded', () => {
  // Auto-submit quick comment forms on Enter
  document.querySelectorAll('.comment-quick-form input').forEach(inp => {
    inp.addEventListener('keydown', e => {
      if (e.key === 'Enter') { e.preventDefault(); inp.closest('form').submit(); }
    });
  });
});
