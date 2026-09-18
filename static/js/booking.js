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

  if (!payForm || !payBtn) return;

  payForm.addEventListener('submit', async (e) => {
    e.preventDefault();

    const bookingRefElement =
      document.getElementById('hidden_booking_ref');

    const selectedMethod =
      document.querySelector('input[name="pay_method"]:checked');

    if (!bookingRefElement || !selectedMethod) {
      alert('Please select a payment method.');
      return;
    }

    const bookingRef = bookingRefElement.value;
    const paymentMethod = selectedMethod.value;

    // Disable button while processing
    payBtn.disabled = true;
    payBtn.innerHTML = '<span>Processing payment...</span>';

    try {
      const response = await fetch('/payment/process', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          booking_reference: bookingRef,
          payment_method: paymentMethod
        })
      });

    if (result.success) {

    payBtn.disabled = true;
    payBtn.innerHTML = '<span>✓ Payment Successful</span>';

    const successMessage =
        document.getElementById('payment_success_message');

    if (successMessage) {
        successMessage.style.display = 'block';

        successMessage.innerHTML = `
            <div style="
                margin-top: 1.5rem;
                padding: 1.5rem;
                border-radius: 12px;
                background: #e8f5e9;
                border: 1px solid #a5d6a7;
                text-align: center;
                color: #2e7d32;
            ">
                <div style="font-size: 2.5rem;">✓</div>

                <h3 style="margin: 0.5rem 0;">
                    Payment Successful
                </h3>

                <p>
                    Your booking has been confirmed.
                </p>

                <p style="font-size: 0.85rem;">
                    Transaction ID:
                    <strong>${result.transaction_reference}</strong>
                </p>

                <p style="font-size: 0.85rem;">
                    Booking Reference:
                    <strong>${result.booking_reference}</strong>
                </p>

                <p style="font-size: 0.8rem; color: #666;">
                    Redirecting to your confirmation...
                </p>
            </div>
        `;
    }

    setTimeout(() => {
        window.location.href =
            `/confirmation?booking_id=${result.booking_id}`;
    }, 2000);

}