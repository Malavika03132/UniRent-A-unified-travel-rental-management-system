
document.addEventListener('DOMContentLoaded', () => {
    initBookingPriceCalculator();
    initRazorpayPayment();
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
        const days = Math.ceil(
            difference / (1000 * 60 * 60 * 24)
        );

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
   RAZORPAY TEST CHECKOUT
   ========================================================= */
function initRazorpayPayment() {

    const paymentForm = document.getElementById('razorpay_form');

    if (!paymentForm) {
        return;
    }

    const payButton = document.getElementById('rzp_pay_submit_btn');
    const bookingRefInput =
        document.getElementById('hidden_booking_ref');

    if (!payButton || !bookingRefInput) {
        return;
    }

    paymentForm.addEventListener('submit', async (event) => {

        event.preventDefault();

        const bookingReference = bookingRefInput.value;

        if (!bookingReference) {
            alert('Booking reference is missing.');
            return;
        }

        /* Disable button */
        payButton.disabled = true;

        payButton.innerHTML = `
            <span style="display:inline-flex;align-items:center;gap:0.6rem;">
                <span class="payment-spinner"></span>
                Starting Secure Payment...
            </span>
        `;

        try {

            /* =====================================================
               STEP 1 — CREATE RAZORPAY ORDER
               ===================================================== */

            const orderResponse = await fetch('/api/create-order', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    booking_reference: bookingReference
                })
            });

            const orderResult = await orderResponse.json();

            if (!orderResponse.ok || !orderResult.success) {
                throw new Error(
                    orderResult.error ||
                    'Unable to create Razorpay order.'
                );
            }


            /* =====================================================
               STEP 2 — OPEN RAZORPAY CHECKOUT
               ===================================================== */

            const options = {

                key: orderResult.key_id,

                amount: orderResult.amount,

                currency: orderResult.currency,

                name: 'UniRent',

                description: 'UniRent Kerala Rental Booking',

                order_id: orderResult.order_id,

                handler: async function (response) {

                    try {

                        /* =========================================
                           STEP 3 — VERIFY PAYMENT
                           ========================================= */

                        const verifyResponse = await fetch(
                            '/api/verify-payment',
                            {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({

                                    razorpay_payment_id:
                                        response.razorpay_payment_id,

                                    razorpay_order_id:
                                        response.razorpay_order_id,

                                    razorpay_signature:
                                        response.razorpay_signature,

                                    booking_reference:
                                        bookingReference

                                })
                            }
                        );

                        const verifyResult =
                            await verifyResponse.json();

                        if (
                            !verifyResponse.ok ||
                            !verifyResult.success
                        ) {
                            throw new Error(
                                verifyResult.error ||
                                'Payment verification failed.'
                            );
                        }


                        /* =========================================
                           STEP 4 — PAYMENT SUCCESS
                           ========================================= */

                        window.location.href =
                            `/confirmation?booking_id=${verifyResult.booking_id}`;

                    } catch (error) {

                        console.error(
                            'Payment verification error:',
                            error
                        );

                        alert(
                            error.message ||
                            'Payment verification failed.'
                        );

                        payButton.disabled = false;
                        payButton.innerHTML =
                            'Pay Securely';
                    }
                },


                /* =================================================
                   PAYMENT FAILED / CHECKOUT CLOSED
                   ================================================= */

                modal: {
                    ondismiss: function () {

                        payButton.disabled = false;

                        payButton.innerHTML =
                            'Pay Securely';
                    }
                }

            };


            /* =====================================================
               STEP 5 — OPEN RAZORPAY
               ===================================================== */

            const razorpay =
                new Razorpay(options);

            razorpay.on(
                'payment.failed',
                function (response) {

                    console.error(
                        'Razorpay payment failed:',
                        response.error
                    );

                    alert(
                        response.error.description ||
                        'Payment failed. Please try again.'
                    );

                    payButton.disabled = false;

                    payButton.innerHTML =
                        'Pay Securely';
                }
            );

            razorpay.open();


        } catch (error) {

            console.error(
                'Razorpay checkout error:',
                error
            );

            alert(
                error.message ||
                'Unable to start payment.'
            );

            payButton.disabled = false;

            payButton.innerHTML =
                'Pay Securely';
        }
    });
}

