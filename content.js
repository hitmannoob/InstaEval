const excludedContentSelector = [
  "script", "style", "noscript", "template", "nav", "footer", "aside",
  "button", "input", "select", "textarea", "form", "[hidden]",
  '[aria-hidden="true"]', "[inert]", '[role="navigation"]',
  '[role="complementary"]', '[role="contentinfo"]', '[role="toolbar"]',
  '[role="dialog"]'
].join(",");

function isHidden(element) {
  for (let current = element; current; current = current.parentElement) {
    if (current.hidden || current.inert || current.getAttribute("aria-hidden") === "true") {
      return true;
    }

    const style = window.getComputedStyle(current);
    if (style.display === "none" || style.visibility === "hidden" ||
        style.visibility === "collapse" || style.contentVisibility === "hidden" ||
        style.opacity === "0") {
      return true;
    }
  }
  return false;
}

function getVisibleText(root) {
  if (!root) return "";
  if (root.matches(excludedContentSelector) || isHidden(root)) return "";

  const clone = root.cloneNode(true);
  const originalElements = [root, ...root.querySelectorAll("*")];
  const clonedElements = [clone, ...clone.querySelectorAll("*")];

  // Keep the live page untouched while removing hidden and non-content UI from
  // a copy. Walking both trees in document order keeps each pair aligned.
  for (let index = originalElements.length - 1; index >= 0; index--) {
    const element = originalElements[index];
    if (element.matches(excludedContentSelector) || isHidden(element)) {
      const copy = clonedElements[index];
      if (copy.parentNode) copy.remove();
    }
  }

  return (clone.innerText || clone.textContent || "").replace(/\s+/g, " ").trim();
}

function getPageText() {
  // Google Docs renders its document text in separate page wrappers.
  if (window.location.hostname === "docs.google.com") {
    return Array.from(document.querySelectorAll(".kix-page-content-wrapper"))
      .map(getVisibleText)
      .filter(Boolean)
      .join(" ");
  }

  // Chrome's PDF viewer exposes selectable text in its text layers.
  const isPdf = document.querySelector('embed[type="application/pdf"]') ||
    /\.pdf$/i.test(window.location.pathname);
  if (isPdf) {
    return Array.from(document.querySelectorAll(".textLayer"))
      .map(getVisibleText)
      .filter(Boolean)
      .join(" ");
  }

  // Try semantic content areas first. Collect all peer areas, avoiding nested
  // duplicates, rather than silently using only the first <main> or <article>.
  const contentGroups = [
    'main, [role="main"]',
    "article",
    "#content, .content, #main, .main"
  ];
  for (const selector of contentGroups) {
    const matches = Array.from(document.querySelectorAll(selector));
    if (!matches.length) continue;

    const topLevelMatches = matches.filter(element =>
      !matches.some(other => other !== element && other.contains(element))
    );
    const text = topLevelMatches.map(getVisibleText).filter(Boolean).join(" ");
    if (text) return text;
  }

  return getVisibleText(document.body);
}

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (!request || request.action !== "extractText") return false;

  let text = "";
  try {
    text = getPageText();
  } catch (error) {
    console.error("Could not extract page text:", error);
  }

  const maxLength = 50000;
  if (text.length > maxLength) {
    text = text.substring(0, maxLength) + "... (text truncated)";
  }

  sendResponse({ text });
  return false;
});
