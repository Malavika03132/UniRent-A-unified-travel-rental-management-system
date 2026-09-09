// ==========================================================================
// UniRent - Dashboard JavaScript (Sidebar, Modals, Approvals & Moderation)
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  initDashboardSidebarToggle();
  initModalCloseHandlers();
});

function initDashboardSidebarToggle() {
  const toggleBtn = document.getElementById('dashboard_sidebar_toggle');
  const sidebar = document.querySelector('.dashboard-sidebar');
  
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
  }
}

function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('active');
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('active');
  }
}

function initModalCloseHandlers() {
  document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove('active');
      }
    });
  });
}

// Admin Approval Helper
function openRejectModal(itemType, itemId, itemName) {
  const form = document.getElementById('reject_form');
  const nameElem = document.getElementById('reject_item_name');
  const typeInput = document.getElementById('reject_item_type');
  const idInput = document.getElementById('reject_item_id');

  if (nameElem) nameElem.textContent = itemName;
  if (typeInput) typeInput.value = itemType;
  if (idInput) idInput.value = itemId;

  openModal('reject_reason_modal');
}

// Owner Complaint Response Helper
function openComplaintResponseModal(complaintId, ref, category) {
  const idInput = document.getElementById('response_complaint_id');
  const refElem = document.getElementById('response_complaint_ref');

  if (idInput) idInput.value = complaintId;
  if (refElem) refElem.textContent = `${ref} (${category})`;

  openModal('complaint_response_modal');
}
