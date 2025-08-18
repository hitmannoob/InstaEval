chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "extractText") {
    let text = "";
    
    // Google Docs specific extraction
    if (window.location.hostname === "docs.google.com") {
      const docsContent = document.querySelectorAll('.kix-page-content-wrapper');
      docsContent.forEach(el => {
        text += el.innerText + "\n";
      });
    } 
    // PDF extraction
    else if (document.querySelector('embed[type="application/pdf"]') || 
             window.location.pathname.endsWith('.pdf')) {
      const pdfViewer = document.querySelector('.textLayer');
      if (pdfViewer) {
        text = pdfViewer.innerText;
      } else {
        text = "PDF content cannot be extracted. Try opening it in Chrome's PDF viewer.";
      }
    }
    // Regular webpage extraction
    else {
      // Remove script and style elements
      const clonedDoc = document.cloneNode(true);
      const scripts = clonedDoc.querySelectorAll('script, style, noscript');
      scripts.forEach(el => el.remove());
      
      // Get main content areas
      const contentSelectors = [
        'main', 'article', '[role="main"]', 
        '#content', '.content', '#main', '.main',
        'body'
      ];
      
      for (const selector of contentSelectors) {
        const element = clonedDoc.querySelector(selector);
        if (element) {
          text = element.innerText || element.textContent;
          break;
        }
      }
      
      // Fallback to body if nothing found
      if (!text) {
        text = document.body.innerText;
      }
    }
    
    // Clean up text
    text = text.replace(/\s+/g, ' ').trim();
    
    // Limit text length to avoid token limits
    const maxLength = 50000;
    if (text.length > maxLength) {
      text = text.substring(0, maxLength) + "... (text truncated)";
    }
    
    sendResponse({ text: text });
  }
  return true;
});