// ==========================================================================
// UniRent - Authentication JavaScript (Tabs, KYC Validation, Password Matching)
// ==========================================================================

const KYC_CONFIGS = {
  pan_card: {
    label: "PAN Card Number",
    placeholder: "e.g. ABCDE1234F",
    regex: /^[A-Z]{5}[0-9]{4}[A-Z]{1}$/,
    hint: "10 characters: 5 letters, 4 digits, 1 letter (e.g. ABCDE1234F)"
  },
  passport: {
    label: "Passport Number",
    placeholder: "e.g. Z1234567",
    regex: /^[A-Z]{1}[0-9]{7}$/,
    hint: "8 characters: 1 uppercase letter followed by 7 digits (e.g. Z1234567)"
  },
  voter_id: {
    label: "Voter ID / EPIC Number",
    placeholder: "e.g. ABC1234567",
    regex: /^[A-Z]{3}[0-9]{7}$|^[A-Z0-9]{10,16}$/,
    hint: "3 letters followed by 7 digits (e.g. ABC1234567) or 10–16 alphanumeric characters"
  },
  driving_license: {
    label: "Driving Licence Number",
    placeholder: "e.g. KL0720210001234",
    regex: /^[A-Z]{2}[0-9]{2}[0-9A-Z]{7,12}$/,
    hint: "Starts with 2-letter state code + RTO + licence digits (e.g. KL0720210001234)"
  }
};

document.addEventListener('DOMContentLoaded', () => {
  initPasswordToggles();
  initRegisterRoleTabs();
  initKycValidation();
  initFormValidation();
});

function initPasswordToggles() {
  const toggles = document.querySelectorAll('.password-toggle-btn');
  toggles.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.preventDefault();
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

function initKycValidation() {
  const kycTypeSelect = document.getElementById('reg_kyc_type');
  const kycNumberInput = document.getElementById('reg_kyc_number');
  const kycNumberLabel = document.getElementById('reg_kyc_number_label');
  const kycHint = document.getElementById('kyc_hint');
  const kycFeedback = document.getElementById('kyc_validation_feedback');

  if (!kycTypeSelect || !kycNumberInput) return;

  function updateKycUI() {
    const selectedType = kycTypeSelect.value;
    const config = KYC_CONFIGS[selectedType];

    if (config) {
      if (kycNumberLabel) kycNumberLabel.textContent = config.label;
      kycNumberInput.placeholder = config.placeholder;
      if (kycHint) kycHint.textContent = config.hint;
      validateKycNumber();
    } else {
      if (kycNumberLabel) kycNumberLabel.textContent = "KYC Document Number";
      kycNumberInput.placeholder = "Select document type first";
      if (kycHint) kycHint.textContent = "Please select a government document type.";
      if (kycFeedback) kycFeedback.style.display = 'none';
    }
  }

  function validateKycNumber() {
    const selectedType = kycTypeSelect.value;
    const config = KYC_CONFIGS[selectedType];
    const val = kycNumberInput.value.trim().toUpperCase();

    if (!val) {
      if (kycFeedback) {
        kycFeedback.style.display = 'none';
      }
      kycNumberInput.style.borderColor = 'var(--ur-border)';
      return;
    }

    if (!config) return;

    if (config.regex.test(val)) {
      if (kycFeedback) {
        kycFeedback.style.display = 'block';
        kycFeedback.style.color = '#28a745';
        kycFeedback.textContent = '✓ Valid ' + config.label + ' format';
      }
      kycNumberInput.style.borderColor = '#28a745';
    } else {
      if (kycFeedback) {
        kycFeedback.style.display = 'block';
        kycFeedback.style.color = '#dc3545';
        kycFeedback.textContent = '✗ ' + config.hint;
      }
      kycNumberInput.style.borderColor = '#dc3545';
    }
  }

  kycTypeSelect.addEventListener('change', updateKycUI);

  kycNumberInput.addEventListener('input', function() {
    // Auto capitalize & remove internal spaces
    this.value = this.value.toUpperCase().replace(/\s/g, '');
    validateKycNumber();
  });

  // Run initial update if value is pre-selected (e.g. form redisplay after error)
  if (kycTypeSelect.value) {
    updateKycUI();
  }
}

function initFormValidation() {
  const passwordInput = document.getElementById('reg_password');
  const confirmInput = document.getElementById('reg_confirm_password');
  const pwFeedback = document.getElementById('password_match_feedback');

  if (passwordInput && confirmInput && pwFeedback) {
    function checkPasswords() {
      const p1 = passwordInput.value;
      const p2 = confirmInput.value;

      if (!p2) {
        pwFeedback.style.display = 'none';
        return;
      }

      pwFeedback.style.display = 'block';
      if (p1 === p2) {
        pwFeedback.style.color = '#28a745';
        pwFeedback.textContent = '✓ Passwords match';
      } else {
        pwFeedback.style.color = '#dc3545';
        pwFeedback.textContent = '✗ Passwords do not match';
      }
    }

    passwordInput.addEventListener('input', checkPasswords);
    confirmInput.addEventListener('input', checkPasswords);
  }

  // Phone input formatting
  const phoneInput = document.getElementById('reg_phone');
  if (phoneInput) {
    phoneInput.addEventListener('blur', function() {
      let raw = this.value.replace(/[\s\-\(\)]/g, '');
      if (raw.startsWith('+91') && raw.length === 13) {
        raw = raw.substring(3);
      } else if (raw.startsWith('91') && raw.length === 12) {
        raw = raw.substring(2);
      } else if (raw.startsWith('0') && raw.length === 11) {
        raw = raw.substring(1);
      }
      if (/^[6-9]\d{9}$/.test(raw)) {
        this.value = '+91 ' + raw.substring(0, 5) + ' ' + raw.substring(5);
        this.style.borderColor = '#28a745';
      }
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
