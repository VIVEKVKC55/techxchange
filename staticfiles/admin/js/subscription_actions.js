document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".approve-btn").forEach(button => {
        button.addEventListener("click", function (event) {
            event.preventDefault();
            let url = this.getAttribute("data-url");  // ✅ Get correct URL
            let collectedAmount = this.getAttribute("data-amount");  // ✅ Get amount

            if (!url) {
                Swal.fire("Error", "Subscription ID is missing!", "error");
                return;
            }

            Swal.fire({
                title: "Approve Subscription",
                html: `<p>Collected Amount: <strong>${collectedAmount} AED</strong></p>
                       <p>Are you sure you want to approve this subscription?</p>`,
                icon: "warning",
                showCancelButton: true,
                confirmButtonColor: "#28a745",
                cancelButtonColor: "#d33",
                confirmButtonText: "Yes, approve it!"
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;  // ✅ Redirect to correct URL
                }
            });
        });
    });

    document.querySelectorAll(".reject-btn").forEach(button => {
        button.addEventListener("click", function (event) {
            event.preventDefault();
            let url = this.getAttribute("data-url");  // ✅ Get correct URL

            if (!url) {
                Swal.fire("Error", "Subscription ID is missing!", "error");
                return;
            }

            Swal.fire({
                title: "Reject Subscription",
                text: "Are you sure you want to reject this subscription?",
                icon: "warning",
                showCancelButton: true,
                confirmButtonColor: "#d33",
                cancelButtonColor: "#3085d6",
                confirmButtonText: "Yes, reject it!"
            }).then((result) => {
                if (result.isConfirmed) {
                    window.location.href = url;  // ✅ Redirect to correct URL
                }
            });
        });
    });
});
