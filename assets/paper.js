// Copy buttons, the language switch, and the redaction of the hero word.
(() => {
  document.documentElement.classList.add("js");
  const body = document.body;
  const toast = document.getElementById("toast");
  let timer;
  const say = (text) => {
    toast.textContent = text;
    toast.classList.add("show");
    clearTimeout(timer);
    timer = setTimeout(() => toast.classList.remove("show"), 1600);
  };

  document.querySelectorAll(".cmd").forEach((box) => {
    const btn = box.querySelector(".copy");
    btn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(box.dataset.copy);
        btn.classList.add("done");
        say(body.dataset.copied);
        setTimeout(() => btn.classList.remove("done"), 1400);
      } catch (e) {
        say(body.dataset.copyFailed);
      }
    });
  });

  const sel = document.getElementById("lang");
  if (sel) sel.addEventListener("change", () => { location.href = sel.value + location.hash; });

  // The word is visible for a moment, then the ink covers it.
  const word = document.querySelector(".rx-hero");
  if (word) requestAnimationFrame(() => requestAnimationFrame(() => word.classList.add("on")));
})();
