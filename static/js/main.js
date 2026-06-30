(function() {
  var saved = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
})();

function toggleTheme() {
  var current = document.documentElement.getAttribute('data-theme');
  var next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  var icon = document.getElementById('themeIcon');
  if (icon) {
    icon.className = next === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
  }
}

function getCsrfToken() {
  return document.cookie.split('; ')
    .find(function(row) { return row.startsWith('csrftoken='); })
    ?.split('=')[1] || '';
}

function toggleLike(btn, postId) {
  fetch('/post/' + postId + '/like/', {
    method: 'POST',
    headers: { 'X-CSRFToken': getCsrfToken() }
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    var icon = btn.querySelector('i');
    if (data.liked) {
      icon.className = 'fas fa-heart';
      icon.style.color = '#ff4757';
      btn.classList.add('liked');
    } else {
      icon.className = 'far fa-heart';
      icon.style.color = '';
      btn.classList.remove('liked');
    }
    var countEl = document.getElementById('likes-' + postId);
    if (countEl) countEl.textContent = data.count;
  });
}

function toggleSave(btn, postId) {
  fetch('/post/' + postId + '/save/', {
    method: 'POST',
    headers: { 'X-CSRFToken': getCsrfToken() }
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    btn.querySelectorAll('i').forEach(function(i) {
      i.className = data.saved ? 'fas fa-bookmark' : 'far fa-bookmark';
      i.style.color = data.saved ? 'var(--accent-1)' : '';
    });
  });
}

function toggleFollow(btn, username) {
  fetch('/profile/' + username + '/follow/', {
    method: 'POST',
    headers: { 'X-CSRFToken': getCsrfToken() }
  })
  .then(function(r) { return r.json(); })
  .then(function(data) {
    if (data.following) {
      btn.textContent = 'Following';
      btn.className = btn.className.replace('btn-gradient', 'btn-glass');
    } else {
      btn.textContent = 'Follow';
      btn.className = btn.className.replace('btn-glass', 'btn-gradient');
    }
    var countEl = document.getElementById('followersCount');
    if (countEl) countEl.textContent = data.followers_count;
  });
}

function sharePost(postId) {
  var url = location.origin + '/post/' + postId + '/';
  if (navigator.clipboard) {
    navigator.clipboard.writeText(url).then(function() {
      showToast('Link copied!');
    });
  }
}

function showToast(message) {
  var toast = document.createElement('div');
  toast.style.cssText = 'position:fixed;top:20px;right:20px;z-index:9999;background:var(--accent-1);color:#fff;padding:12px 20px;border-radius:10px;font-size:14px;font-weight:500;box-shadow:0 4px 20px rgba(0,0,0,0.3);';
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(function() { toast.remove(); }, 3000);
}

function toggleCaption(postId) {
  var more = document.querySelector('#caption-' + postId + ' .caption-more');
  var btn = document.querySelector('#caption-' + postId + ' .caption-toggle');
  if (more && btn) {
    var hidden = more.classList.contains('d-none');
    more.classList.toggle('d-none', !hidden);
    btn.textContent = hidden ? ' less' : '... more';
  }
}

function handleDoubleTapLike(img, postId) {
  var likeBtn = document.querySelector('[data-post-id="' + postId + '"].like-btn');
  if (likeBtn && !likeBtn.classList.contains('liked')) {
    toggleLike(likeBtn, postId);
  }
}

document.addEventListener('DOMContentLoaded', function() {
  // Apply saved theme
  var saved = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
  var icon = document.getElementById('themeIcon');
  if (icon) {
    icon.className = saved === 'dark' ? 'fas fa-moon' : 'fas fa-sun';
  }

  // Media upload preview
  var input = document.getElementById('postMediaInput');
  var area = document.getElementById('mediaUploadArea');
  if (input && area) {
    area.addEventListener('click', function(e) {
      if (e.target !== input) input.click();
    });
    input.addEventListener('change', function() {
      if (!input.files.length) return;
      var file = input.files[0];
      var url = URL.createObjectURL(file);
      var img = document.getElementById('imagePreview');
      var vid = document.getElementById('videoPreview');
      var placeholder = document.getElementById('mediaPlaceholder');
      if (placeholder) placeholder.classList.add('d-none');
      if (file.type.startsWith('video/')) {
        if (img) img.classList.add('d-none');
        if (vid) { vid.src = url; vid.classList.remove('d-none'); }
      } else {
        if (vid) vid.classList.add('d-none');
        if (img) { img.src = url; img.classList.remove('d-none'); }
      }
    });
  }
});