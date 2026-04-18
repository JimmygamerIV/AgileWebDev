function showTab(tabName) {
  // hide both sections
  document.getElementById("friends").classList.add("hidden");
  document.getElementById("requests").classList.add("hidden");

  // remove active class from tabs
  const tabs = document.querySelectorAll(".tab");
  tabs.forEach((tab) => tab.classList.remove("active"));

  // show selected tab
  document.getElementById(tabName).classList.remove("hidden");

  // highlight active tab
  if (tabName === "friends") {
    tabs[0].classList.add("active");
  } else {
    tabs[1].classList.add("active");
  }

  window.onload = function () {
    const params = new URLSearchParams(window.location.search);
    const tab = params.get("tab");

    if (tab === "requests") {
      showTab("requests");
    } else {
      showTab("friends");
    }
  };
}
