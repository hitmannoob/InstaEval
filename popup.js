let currentQuestionIndex = 0;
let quizData = [];
let score = 0;
let answering = false;

function showMessage(message, type = "info") {
  const container = document.getElementById("quiz");
  const messageElement = document.createElement("p");
  messageElement.className = `message ${type}`;
  messageElement.textContent = message;
  container.replaceChildren(messageElement);
}

function isValidQuiz(questions) {
  return Array.isArray(questions) && questions.length > 0 && questions.every((question) =>
    question &&
    typeof question.question === "string" &&
    question.question.trim() &&
    Array.isArray(question.options) &&
    question.options.length === 4 &&
    question.options.every((option) => typeof option === "string" && option.trim()) &&
    typeof question.answer === "string" &&
    /^[A-D]$/i.test(question.answer)
  );
}

function createTextElement(tagName, className, text) {
  const element = document.createElement(tagName);
  if (className) element.className = className;
  element.textContent = text;
  return element;
}

function showQuestion(index) {
  if (index >= quizData.length) {
    showResults();
    return;
  }

  currentQuestionIndex = index;
  answering = false;
  const question = quizData[index];
  const container = document.getElementById("quiz");
  container.replaceChildren();

  const progress = document.createElement("div");
  progress.className = "progress-row";
  progress.append(
    createTextElement("span", "progress-label", `Question ${index + 1} of ${quizData.length}`),
    createTextElement("span", "score-label", `Score: ${score}`)
  );
  container.appendChild(progress);

  const progressBar = document.createElement("progress");
  progressBar.className = "progress-bar";
  progressBar.max = quizData.length;
  progressBar.value = index + 1;
  progressBar.setAttribute("aria-label", `Question ${index + 1} of ${quizData.length}`);
  container.appendChild(progressBar);

  container.appendChild(createTextElement("h2", "question", question.question));

  const options = document.createElement("div");
  options.className = "options";
  question.options.forEach((option, optionIndex) => {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "option";
    button.append(
      createTextElement("span", "option-letter", `${String.fromCharCode(65 + optionIndex)}.`),
      createTextElement("span", "option-text", option)
    );
    button.addEventListener("click", () => selectAnswer(button, optionIndex, question, options));
    options.appendChild(button);
  });
  container.appendChild(options);
  options.querySelector("button")?.focus();
}

function selectAnswer(selectedButton, selectedIndex, question, options) {
  if (answering) return;
  answering = true;

  const buttons = Array.from(options.querySelectorAll("button"));
  buttons.forEach((button) => {
    button.disabled = true;
  });

  const correctIndex = question.answer.toUpperCase().charCodeAt(0) - 65;
  const correct = selectedIndex === correctIndex;
  if (correct) score++;
  selectedButton.classList.add(correct ? "correct" : "wrong");
  buttons[correctIndex].classList.add("correct");

  const container = document.getElementById("quiz");
  const feedback = createTextElement(
    "p",
    `feedback ${correct ? "feedback-correct" : "feedback-wrong"}`,
    correct ? "Correct!" : `Not quite. The correct answer is ${String.fromCharCode(65 + correctIndex)}.`
  );
  feedback.setAttribute("role", "status");

  const nextButton = document.createElement("button");
  nextButton.type = "button";
  nextButton.className = "primary-button next-button";
  nextButton.textContent = currentQuestionIndex === quizData.length - 1 ? "See results" : "Next question";
  nextButton.addEventListener("click", () => showQuestion(currentQuestionIndex + 1));
  container.append(feedback, nextButton);
  nextButton.focus();
}

function showResults() {
  const container = document.getElementById("quiz");
  const percentage = Math.round((score / quizData.length) * 100);
  container.replaceChildren(
    createTextElement("p", "results-kicker", "Quiz complete"),
    createTextElement("h2", "results-title", "Nice work!"),
    createTextElement("p", "results-score", `${score} of ${quizData.length} correct`),
    createTextElement("p", "results-detail", `${percentage}% score`)
  );

  const retryButton = document.createElement("button");
  retryButton.type = "button";
  retryButton.className = "primary-button retry-button";
  retryButton.textContent = "Generate another quiz";
  retryButton.addEventListener("click", loadQuiz);
  container.appendChild(retryButton);
}

function isYouTubeVideoUrl(rawUrl) {
  try {
    const url = new URL(rawUrl);
    const host = url.hostname.toLowerCase();
    const youtubeHosts = [
      "youtube.com", "www.youtube.com", "m.youtube.com", "music.youtube.com",
      "youtube-nocookie.com", "www.youtube-nocookie.com", "youtu.be", "www.youtu.be"
    ];
    if (!youtubeHosts.includes(host)) return false;

    const videoId = host === "youtu.be" || host === "www.youtu.be"
      ? url.pathname.split("/").filter(Boolean)[0]
      : url.pathname === "/watch"
        ? url.searchParams.get("v")
        : url.pathname.match(/^\/(?:embed|shorts|live|v)\/([\w-]{11})(?:\/|$)/)?.[1];
    return typeof videoId === "string" && /^[\w-]{11}$/.test(videoId);
  } catch {
    return false;
  }
}

async function loadQuiz() {
  const generateButton = document.getElementById("generateBtn");
  generateButton.disabled = true;
  generateButton.textContent = "Generating…";
  showMessage("Preparing your quiz…");

  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab || !tab.url) {
      showMessage("Could not read the current tab. Open a webpage and try again.", "error");
      return;
    }

    const level = document.getElementById("level").value;
    const numQuestions = Number(document.getElementById("numQuestions").value);
    if (!Number.isInteger(numQuestions) || numQuestions < 5 || numQuestions > 20) {
      showMessage("Choose between 5 and 20 questions.", "error");
      return;
    }

    const url = new URL(tab.url);
    if (!["http:", "https:"].includes(url.protocol)) {
      showMessage("Cannot access this page. Open a website with content and try again.", "error");
      return;
    }

    const requestBody = { level, numQuestions };
    if (isYouTubeVideoUrl(tab.url)) {
      requestBody.url = tab.url;
    } else {
      let response;
      try {
        response = await chrome.tabs.sendMessage(tab.id, { action: "extractText" });
      } catch {
        showMessage("Cannot read this page. Refresh it and try again.", "error");
        return;
      }

      if (!response || typeof response.text !== "string" || !response.text.trim()) {
        showMessage("Could not extract text from this page. Try refreshing it first.", "error");
        return;
      }
      if (response.text.trim().length < 100) {
        showMessage("There is not enough text on this page to make a quiz.", "error");
        return;
      }
      requestBody.text = response.text;
    }

    const apiResponse = await fetch("http://127.0.0.1:5000/generate_quiz", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody)
    });
    const data = await apiResponse.json().catch(() => ({}));
    if (!apiResponse.ok) {
      throw new Error(data.error || `The server returned an error (${apiResponse.status}).`);
    }
    if (!isValidQuiz(data.quiz)) {
      showMessage("The server returned an invalid quiz. Please try again.", "error");
      return;
    }

    quizData = data.quiz;
    currentQuestionIndex = 0;
    score = 0;
    showQuestion(currentQuestionIndex);
  } catch (error) {
    console.error("Quiz generation failed:", error);
    showMessage(`${error.message} Make sure the InstaEval server is running.`, "error");
  } finally {
    generateButton.disabled = false;
    generateButton.textContent = "Generate Quiz";
  }
}

document.getElementById("generateBtn").addEventListener("click", loadQuiz);
