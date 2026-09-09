// ==========================================================================
// UniRent - Authentication JavaScript (Tabs, Quick Demo Fill, Validation)
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  initPasswordToggles();
  initRegisterRoleTabs();
});

function initPasswordToggles() {
  const toggles = document.querySelectorAll('.password-toggle-btn');
  toggles.forEach(btn => {
    btn.addEventListener('click', () => {
      const input = btn.closest('.password-wrapper').querySelector('input');
      if (input.type === 'password') {
        input.type = 'text';
        btn.textContent = 'Hide';
      } else {
        input.type = 'password';
        btn.textContent = 'Show';
      }
    });
  });
}

function initRegisterRoleTabs() {
  const tabs = document.querySelectorAll('.auth-tab');
  const roleInput = document.getElementById('selected_role_input');
  const ownerFields = document.getElementById('owner_specific_fields');

  if (tabs.length && roleInput) {
    tabs.forEach(tab => {
      tab.addEventListener('click', (e) => {
        e.preventDefault();
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        
        const role = tab.dataset.role; // 'traveler' or 'owner'
        roleInput.value = role;

        if (ownerFields) {
          ownerFields.style.display = (role === 'owner') ? 'block' : 'none';
        }
      });
    });
  }
}

function fillDemoCredentials(role) {
  const emailInput = document.getElementById('login_email');
  const passwordInput = document.getElementById('login_password');

  if (!emailInput || !passwordInput) return;

  if (role === 'admin') {
    emailInput.value = 'admin@unirent.com';
    passwordInput.value = 'admin123';
  } else if (role === 'owner') {
    emailInput.value = 'owner@unirent.com';
    passwordInput.value = 'owner123';
  } else {
    emailInput.value = 'traveler@unirent.com';
    passwordInput.value = 'traveler123';
  }
}
