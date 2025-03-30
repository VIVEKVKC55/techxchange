document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".approve-btn").forEach(button => {
        button.addEventListener("click", function () {
            var subscriptionId = this.dataset.id;
            var collectedAmount = this.dataset.amount;

            Swal.fire({
                title: "Confirm Approval",
                html: `<p>Collected Amount: <strong>${collectedAmount} AED</strong></p>
                       <p>Are you sure you want to approve this subscription?</p>`,
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: "Yes, Approve",
                cancelButtonText: "Cancel"
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = `/admin/customer/subscription/approve/${subscriptionId}/`;
                }
            });
        });
    });

    document.querySelectorAll(".reject-btn").forEach(button => {
        button.addEventListener("click", function () {
            var subscriptionId = this.dataset.id;

            Swal.fire({
                title: "Confirm Rejection",
                text: "Are you sure you want to reject this subscription?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonText: "Yes, Reject",
                cancelButtonText: "Cancel"
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = `/admin/customer/subscription/reject/${subscriptionId}/`;
                }
            });
        });
    });
});
