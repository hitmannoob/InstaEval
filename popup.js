let currentQuestionIndex = 0;
let quizData = [];

function showQuestion(index) {
  const container = document.getElementById("quiz");

  if (!quizData || index >= quizData.length || !quizData[index]) {
    container.innerHTML = `<div>Quiz completed!</div>`;
    return;
  }

  const questionObj = quizData[index];

  container.innerHTML = `
    <div class="question">${index + 1}. ${questionObj.question}</div>
    ${questionObj.options.map((opt, i) =>
      `<div class="option" data-index="${i}">${String.fromCharCode(65 + i)}. ${opt}</div>`
    ).join('')}
  `;

  document.querySelectorAll('.option').forEach(opt => {
    opt.addEventListener('click', (e) => {
      const selected = e.target.getAttribute('data-index');
      const correctIndex = questionObj.answer.charCodeAt(0) - 65;

      if (parseInt(selected) === correctIndex) {
        e.target.classList.add('correct');
        setTimeout(() => nextQuestion(), 1000);
      } else {
        e.target.classList.add('wrong');
        document.querySelectorAll('.option')[correctIndex].classList.add('correct');
        setTimeout(() => nextQuestion(), 2500);
      }
    });
  });
}

function nextQuestion() {
  currentQuestionIndex++;
  if (currentQuestionIndex < quizData.length) {
    showQuestion(currentQuestionIndex);
  } else {
    document.getElementById("quiz").innerHTML = `<div>🎉 Quiz completed!</div>`;
  }
}

async function loadQuiz() {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    console.log("Current tab URL:", tab.url);
    
    // Get user inputs
    const level = document.getElementById('level').value;
    const numQuestions = parseInt(document.getElementById('numQuestions').value);
    
    // Check if URL is accessible
    if (!tab.url || 
        tab.url.startsWith('chrome://') || 
        tab.url.startsWith('chrome-extension://') || 
        tab.url.startsWith('about:') ||
        tab.url.startsWith('edge://') ||
        tab.url.startsWith('brave://')) {
      document.getElementById("quiz").innerHTML = "⚠ Cannot access this page.<br>Please open a website with content.";
      return;
    }
    
    document.getElementById("quiz").innerHTML = "Generating quiz...";

    let requestBody = { level: level, numQuestions: numQuestions };
    
    // Check if it's YouTube
    if (tab.url && tab.url.includes('youtube.com/watch')) {
      console.log("Detected YouTube video");
      requestBody.url = tab.url;
    } else {
      console.log("Not YouTube, extracting text from page");
      // Extract text from any other website
      try {
        const response = await chrome.tabs.sendMessage(tab.id, { action: "extractText" });
        console.log("Extracted text response:", response);
        
        if (!response || !response.text) {
          document.getElementById("quiz").innerHTML = "⚠ Could not extract text from this page.<br>Try refreshing the page first.";
          return;
        }
        
        if (response.text.length < 100) {
          document.getElementById("quiz").innerHTML = "⚠ Not enough text content to generate quiz.";
          return;
        }
        
        requestBody.text = response.text;
      } catch (msgError) {
        console.error("Message error:", msgError);
        document.getElementById("quiz").innerHTML = "⚠ Cannot access this page.<br>Please refresh the page and try again.";
        return;
      }
    }

    console.log("Sending request with body:", requestBody);
    const apiResponse = await fetch("http://127.0.0.1:5000/generate_quiz", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody)
    });

    if (!apiResponse.ok) {
      throw new Error(`HTTP error! status: ${apiResponse.status}`);
    }

    const data = await apiResponse.json();
    console.log("Quiz data:", data);

    if (!data.quiz || data.quiz.length === 0) {
      document.getElementById("quiz").innerHTML = "⚠ No quiz questions generated.";
      return;
    }

    quizData = data.quiz;
    currentQuestionIndex = 0;
    showQuestion(currentQuestionIndex);

  } catch (error) {
    console.error("Error:", error);
    document.getElementById("quiz").innerHTML = `⚠ Error: ${error.message}<br>Make sure Flask server is running`;
  }
}

// Add event listener to generate button
document.getElementById('generateBtn').addEventListener('click', loadQuiz);