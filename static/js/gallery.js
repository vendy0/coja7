let currentIndex = 0;
let touchStartX = 0;
let touchEndX = 0;
let isLightboxOpen = false;

function openLightbox(index) {
  if (galleryMedia.length === 0) return;
  currentIndex = index;
  updateLightboxContent();
  
  const lightbox = document.getElementById('lightbox');
  lightbox.classList.add('active');
  isLightboxOpen = true;

  // Interception du bouton retour physique/système
  history.pushState({ lightboxOpen: true }, '');

  document.addEventListener('keydown', handleKeyPress);
  window.addEventListener('popstate', handlePopState);
}

function updateLightboxContent() {
  const item = galleryMedia[currentIndex];
  const img = document.getElementById('lightbox-img');
  const video = document.getElementById('lightbox-video');
  const caption = document.getElementById('lightbox-caption');
  const loader = document.getElementById('lightbox-loader');
  // NOUVEAU : Sélection du bouton de téléchargement
  const downloadBtn = document.getElementById('lightbox-download');

  loader.style.display = 'block';
  img.style.display = 'none';
  video.style.display = 'none';
  video.pause();
  video.removeAttribute('src');
  img.removeAttribute('src');

  caption.innerText = (item.credit ? 'Crédit : ' + item.credit : '') + ` (${currentIndex + 1}/${galleryMedia.length})`;
  
  // NOUVEAU : Mise à jour du lien de téléchargement
  downloadBtn.href = item.url;
  // Optionnel : donner un nom de fichier par défaut dynamique
  downloadBtn.download = item.type === 'video' ? `video_${currentIndex + 1}.mp4` : `image_${currentIndex + 1}.jpg`;

  if (item.type === 'video') {
    video.src = item.url;
    video.load();
  } else {
    img.src = item.url;
  }
}

function navigateLightbox(direction) {
  if (galleryMedia.length <= 1) return;
  
  currentIndex += direction;
  
  if (currentIndex < 0) {
    currentIndex = galleryMedia.length - 1;
  } else if (currentIndex >= galleryMedia.length) {
    currentIndex = 0;
  }

  updateLightboxContent();
}

function closeLightbox(event) {
  if (!isLightboxOpen) return;

  const lightbox = document.getElementById('lightbox');
  const video = document.getElementById('lightbox-video');
  const img = document.getElementById('lightbox-img');

  lightbox.classList.remove('active');
  video.pause();
  video.removeAttribute('src');
  img.removeAttribute('src');
  isLightboxOpen = false;

  document.removeEventListener('keydown', handleKeyPress);
  window.removeEventListener('popstate', handlePopState);

  // Si la fermeture vient d'un clic UI et non du bouton retour navigateur
  if (history.state && history.state.lightboxOpen) {
    history.back();
  }
}

// Gestion de l'action "Retour" du navigateur / mobile
function handlePopState(e) {
  if (isLightboxOpen) {
    closeLightbox();
  }
}

function handleKeyPress(e) {
  if (e.key === 'ArrowLeft') {
    navigateLightbox(-1);
  } else if (e.key === 'ArrowRight') {
    navigateLightbox(1);
  } else if (e.key === 'Escape') {
    closeLightbox();
  }
}

// Swipe tactile
const lightboxElement = document.getElementById('lightbox');

lightboxElement.addEventListener('touchstart', (e) => {
  touchStartX = e.changedTouches[0].screenX;
}, { passive: true });

lightboxElement.addEventListener('touchend', (e) => {
  touchEndX = e.changedTouches[0].screenX;
  handleSwipe();
}, { passive: true });

function handleSwipe() {
  const swipeThreshold = 50;
  if (touchEndX < touchStartX - swipeThreshold) {
    navigateLightbox(1);
  }
  if (touchEndX > touchStartX + swipeThreshold) {
    navigateLightbox(-1);
  }
}

function onMediaLoaded() {
  const item = galleryMedia[currentIndex];
  const loader = document.getElementById('lightbox-loader');
  const img = document.getElementById('lightbox-img');
  const video = document.getElementById('lightbox-video');

  loader.style.display = 'none';

  if (item.type === 'video') {
    video.style.display = 'block';
    video.play().catch(() => {});
  } else {
    img.style.display = 'block';
  }
}

function onMediaError() {
  const loader = document.getElementById('lightbox-loader');
  const caption = document.getElementById('lightbox-caption');
  loader.style.display = 'none';
  caption.innerText = "Erreur de chargement du média (connexion lente ou interrompue).";
}