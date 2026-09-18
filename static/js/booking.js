document.addEventListener('DOMContentLoaded', () => {
    initBookingPriceCalculator();
    initPaymentSimulator();
});


/* =========================================================
   BOOKING PRICE CALCULATOR
   ========================================================= */
function initBookingPriceCalculator() {
    const startInput = document.getElementById('start_date');
    const endInput = document.getElementById('end_date');
    const rateInput = document.getElementById('listing_daily_rate');

    const daysDisplay = document.getElementById('total_days');
    const subtotalDisplay = document.getElementById('subtotal_amount');
    const serviceFeeDisplay = document.getElementById('service_fee_amount');
    const taxDisplay = document.getElementById('tax_amount');
    const totalDisplay = document.getElementById('total_amount');

    if (!startInput || !endInput || !rateInput) {
        return;
    }

    function formatCurrency(amount) {
        return '₹' + Number(amount).toLocaleString('en-IN', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    function calculatePrice() {
        const startValue = startInput.value;
        const endValue = endInput.value;
        const rate = parseFloat(rateInput.value) || 0;

        if (!startValue || !endValue) {
            return;
        }

        const start = new Date(startValue);
        const end = new Date(endValue);

        const difference = end - start;
        const days = Math.ceil(difference / (1000 * 60 * 60 * 24));

        if (days <= 0) {
            return;
        }

        const subtotal = rate * days;
        const serviceFee = subtotal * 0.05;
        const tax = subtotal * 0.12;
        const total = subtotal + serviceFee + tax;

        if (daysDisplay) {
            daysDisplay.textContent = days;
        }

        if (subtotalDisplay) {
            subtotalDisplay.textContent = formatCurrency(subtotal);
        }

        if (serviceFeeDisplay) {
            serviceFeeDisplay.textContent = formatCurrency(serviceFee);
        }

        if (taxDisplay) {
            taxDisplay.textContent = formatCurrency(tax);
        }

        if (totalDisplay) {
            totalDisplay.textContent = formatCurrency(total);
        }
    }

    startInput.addEventListener('change', calculatePrice);
    endInput.addEventListener('change', calculatePrice);

    calculatePrice();
}


/* =========================================================
   PAYMENT METHOD SWITCHING
   ========================================================= */
function initPaymentMethodSwitcher() {
    const methodCards = document.querySelectorAll('.payment-method-card');

    const cardDetails = document.getElementById('method_details_card');
    const upiDetails = document.getElementById('method_details_upi');
    const netbankingDetails = document.getElementById('method_details_netbanking');

    if (!methodCards.length) {
        return;
    }

    methodCards.forEach(card => {
        const radio = card.querySelector('input[type="radio"]');

        card.addEventListener('click', () => {
            if (radio) {
                radio.checked = true;
            }

            methodCards.forEach(item => {
                item.style.border = '1px solid var(--ur-border)';
                item.style.background = 'var(--ur-white)';
            });

            card.style.border = '2px solid var(--ur-burnt-orange)';
            card.style.background = '#fffdf8';

            const selectedMethod = radio ? radio.value : '';

            if (cardDetails) {
                cardDetails.style.display =
                    selectedMethod === 'card' ? 'block' : 'none';
            }

            if (upiDetails) {
                upiDetails.style.display =
                    selectedMethod === 'upi' ? 'block' : 'none';
            }

            if (netbankingDetails) {
                netbankingDetails.style.display =
                    selectedMethod === 'netbanking' ? 'block' : 'none';
            }
        });
    });
}


/* =========================================================
   PAYMENT SIMULATOR
   ========================================================= */
function initPaymentSimulator() {
    const paymentForm = document.getElementById('razorpay_demo_form');

    if (!paymentForm) {
        return;
    }

    initPaymentMethodSwitcher();

    const payButton = document.getElementById('rzp_pay_submit_btn');
    const bookingRefInput = document.getElementById('hidden_booking_ref');
    const successMessage = document.getElementById('payment_success_message');

    if (!payButton || !bookingRefInput) {
        return;
    }

    paymentForm.addEventListener('submit', async (event) => {
        event.preventDefault();

        const bookingReference = bookingRefInput.value;

        const selectedMethod =
            paymentForm.querySelector('input[name="pay_method"]:checked');

        const paymentMethod = selectedMethod
            ? selectedMethod.value
            : 'card';

        /* Disable button while processing */
        payButton.disabled = true;
        payButton.innerHTML = `
            <span style="display:inline-flex;align-items:center;gap:0.6rem;">
                <span class="payment-spinner"></span>
                Processing Payment...
            </span>
        `;

        try {
            const response = await fetch('/payment/process', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    booking_reference: bookingReference,
                    payment_method: paymentMethod
                })
            });

            const result = await response.json();

            if (!response.ok || !result.success) {
                throw new Error(
                    result.error || 'Payment could not be completed.'
                );
            }

            /* ==========================================
               PAYMENT SUCCESS
               ========================================== */

            if (successMessage) {
                successMessage.innerHTML = `
                    <div class="payment-success-card">

                        <div class="payment-success-icon">
                            ✓
                        </div>

                        <h2>Payment Successful</h2>

                        <p class="payment-success-text">
                            Your payment has been received and your booking
                            has been confirmed successfully.
                        </p>

                        <div class="payment-transaction-box">
                            <span>Transaction ID</span>
                            <strong>
                                ${result.transaction_id || 'TXN-RPY-DEMO'}
                            </strong>
                        </div>

                        <button
                            type="button"
                            id="continue_to_confirmation"
                            class="btn btn-primary btn-lg"
                        >
                            Continue to Confirmation
                        </button>

                    </div>
                `;

                successMessage.style.display = 'block';
            }

            /* Hide the payment form controls */
            const paymentOptions =
                paymentForm.querySelectorAll(
                    'input, select, .form-group, .payment-method-card'
                );

            paymentOptions.forEach(element => {
                element.style.pointerEvents = 'none';
            });

            /* Hide everything except success message */
            const formChildren = Array.from(paymentForm.children);

            formChildren.forEach(element => {
                if (element.id !== 'payment_success_message') {
                    element.style.display = 'none';
                }
            });

            /* Make success button available */
            const continueButton =
                document.getElementById('continue_to_confirmation');

            if (continueButton) {
                continueButton.addEventListener('click', () => {
                    window.location.href =
                        `/confirmation?booking_id=${result.booking_id}`;
                });
            }

        } catch (error) {
            console.error('Payment error:', error);

            payButton.disabled = false;
            payButton.innerHTML = 'Pay Securely';

            alert(
                error.message ||
                'Something went wrong while processing the payment.'
            );
        }
    });
}