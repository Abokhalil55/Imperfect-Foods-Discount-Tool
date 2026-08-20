const headlineRevenueFormatter = new Intl.NumberFormat("en-MY", {
  style: "currency",
  currency: "MYR",
  minimumFractionDigits: 1,
  maximumFractionDigits: 1,
});

function formatHeadlineRevenue() {
  document.querySelectorAll(".revenue-register > strong").forEach(element => {
    const value = Number(element.textContent.replace(/[^0-9.-]/g, ""));
    if (Number.isFinite(value)) {
      element.textContent = headlineRevenueFormatter.format(value);
      element.style.whiteSpace = "nowrap";
      element.style.overflowWrap = "normal";
    }
  });
}

const revenueObserver = new MutationObserver(formatHeadlineRevenue);
revenueObserver.observe(document.querySelector("#view-content"), { childList: true, subtree: true });
formatHeadlineRevenue();
