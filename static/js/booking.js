// ==========================================================================
// UniRent - Booking & Payment Flow JavaScript (Calculator, Razorpay Demo)
// ==========================================================================

document.addEventListener('DOMContentLoaded', () => {
  initBookingPriceCalculator();
  initPaymentSimulator();
});

function initBookingPriceCalculator() {
  const startDateInput = document.getElementById('booking_start_date');
  const endDateInput = document.getElementById('booking_end_date');
  const rateInput = document.getElementById('listing_daily_rate');

  if (!startDateInput || !endDateInput || !rateInput) return;

  function updateTotals() {
    const rate = parseFloat(rateInput.value) || 0;
    const sDate = new Date(startDateInput.value);
    const eDate = new Date(endDateInput.value);

    if (startDateInput.value && endDateInput.value && eDate > sDate) {
      const diffTime = Math.abs(eDate - sDate);
      const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

      const subtotal = rate * diffDays;
      const serviceFee = Math.round(subtotal * 0.05);
      const tax = Math.round(subtotal * 0.12);
      const total = subtotal + serviceFee + tax;

      document.getElementById('display_days').textContent = diffDays;
      document.getElementById('display_subtotal').textContent = `₹${subtotal.toLocaleString('en-IN')}`;
      document.getElementById('display_service_fee').textContent = `₹${serviceFee.toLocaleString('en-IN')}`;
      document.getElementById('display_tax').textContent = `₹${tax.toLocaleString('en-IN')}`;
      document.getElementById('display_total').textContent = `₹${total.toLocaleString('en-IN')}`;
    }
  }

  startDateInput.addEventListener('change', updateTotals);
  endDateInput.addEventListener('change', updateTotals);
}

function initPaymentSimulator() {
  const payForm = document.getElementById('razorpay_demo_form');
  const payBtn = document.getElementById('rzp_pay_submit_btn');

  if (payForm && payBtn) {
    payForm.addEventListener('submit', (e) => {
      e.preventDefault();
      payBtn.disabled = true;
      payBtn.innerHTML = '<span>Processing with Razorpay...</span>';

      setTimeout(() => {
        const bookingRef = document.getElementById('hidden_booking_ref').value;
        window.location.href = `/confirmation?ref=${bookingRef}`;
      }, 1500);
    });
  }
}
