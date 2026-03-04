document.addEventListener("DOMContentLoaded", function () {
  var toastElList = [].slice.call(document.querySelectorAll(".toast"));
  var toastList = toastElList.map(function (toastEl) {
    return new bootstrap.Toast(toastEl, { autohide: true });
  });
  toastList.forEach((toast) => toast.show());
});




document.addEventListener("DOMContentLoaded", function () {

    const forms = document.querySelectorAll("form:not(#comment-form)");

    forms.forEach(form => {
        form.addEventListener("submit", function () {

            const button = form.querySelector("button[type='submit'], input[type='submit']");

            if (button) {

                const originalText = button.innerText || button.value;

                // Custom loading text if provided
                const loadingText = button.getAttribute("data-loading-text");

                if (button.tagName === "BUTTON") {
                    button.innerText = loadingText || "Processing...";
                } else {
                    button.value = loadingText || "Processing...";
                }

                button.disabled = true;

                // Optional: add spinner
                button.style.opacity = "0.8";
            }
        });
    });

});
