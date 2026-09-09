// ==========================================================================
// UniRent - Main Global JavaScript (Leaflet Maps, Navigation, Toast System)
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  initMobileNav();
  initFlashDismiss();
  initLeafletMaps();
});

function initMobileNav() {
  const toggle = document.querySelector('.mobile-toggle');
  const navLinks = document.querySelector('.nav-links');
  const navActions = document.querySelector('.nav-actions');
  
  if (toggle && navLinks) {
    toggle.addEventListener('click', () => {
      const isVisible = navLinks.style.display === 'flex';
      navLinks.style.display = isVisible ? 'none' : 'flex';
      if (navActions) navActions.style.display = isVisible ? 'none' : 'flex';
      
      if (!isVisible) {
        navLinks.style.flexDirection = 'column';
        navLinks.style.position = 'absolute';
        navLinks.style.top = 'var(--header-height)';
        navLinks.style.left = '0';
        navLinks.style.right = '0';
        navLinks.style.backgroundColor = 'var(--ur-light-ivory)';
        navLinks.style.padding = '1.5rem';
        navLinks.style.borderBottom = '1px solid var(--ur-border)';
        navLinks.style.boxShadow = 'var(--shadow-md)';
      }
    });
  }
}

function initFlashDismiss() {
  const alerts = document.querySelectorAll('.alert-auto-dismiss');
  alerts.forEach(alert => {
    setTimeout(() => {
      alert.style.transition = 'opacity 0.4s ease';
      alert.style.opacity = '0';
      setTimeout(() => alert.remove(), 400);
    }, 4500);
  });
}

function initLeafletMaps() {
  const mapElements = document.querySelectorAll('[data-leaflet-lat]');
  mapElements.forEach(elem => {
    const lat = parseFloat(elem.dataset.leafletLat) || 9.9312;
    const lng = parseFloat(elem.dataset.leafletLng) || 76.2673;
    const title = elem.dataset.leafletTitle || 'UniRent Location';
    const zoom = parseInt(elem.dataset.leafletZoom) || 14;

    if (typeof L !== 'undefined') {
      const map = L.map(elem).setView([lat, lng], zoom);
      
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors | UniRent Kerala'
      }).addTo(map);

      // Custom Heritage Pin Marker
      const customIcon = L.divIcon({
        className: 'unirent-map-pin',
        html: `<div style="background-color:#c65b2d;width:28px;height:28px;border-radius:50%;border:3px solid #fff;box-shadow:0 3px 10px rgba(0,0,0,0.3);display:flex;align-items:center;justify-content:center;color:#fff;font-size:12px;">📍</div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 28]
      });

      L.marker([lat, lng], { icon: customIcon }).addTo(map)
        .bindPopup(`<b>${title}</b><br>Kerala, India`)
        .openPopup();
    }
  });
}
