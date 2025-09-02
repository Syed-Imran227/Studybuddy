document.addEventListener('DOMContentLoaded', () => {
  const dropZone = document.getElementById('dropZone');
  const fileInput = document.getElementById('pdfFile');
  const uploadButton = document.getElementById('uploadButton');
  const progressContainer = document.getElementById('progressContainer');
  const progressBar = document.getElementById('uploadProgress');
  const processingSpinner = document.getElementById('processingSpinner');
  const processingStatus = document.getElementById('processingStatus');
  const resultsSection = document.getElementById('resultsSection');
  const imagePreview = document.getElementById('imagePreview');
  const chatBox = document.getElementById('chatBox');
  const chatForm = document.getElementById('chatForm');
  const userInput = document.getElementById('userInput');

  // Drag and drop handlers
  ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
  });

  ['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, highlight, false);
  });

  ['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, unhighlight, false);
  });

  dropZone.addEventListener('drop', handleDrop, false);
  dropZone.addEventListener('click', () => fileInput.click());
  fileInput.addEventListener('change', handleFileSelect);
  uploadButton.addEventListener('click', handleUpload);
  chatForm.addEventListener('submit', handleChat);

  function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
  }

  function highlight(e) {
    dropZone.classList.add('highlight');
  }

  function unhighlight(e) {
    dropZone.classList.remove('highlight');
  }

  function handleDrop(e) {
    const dt = e.dataTransfer;
    const files = dt.files;
    fileInput.files = files;
    handleUpload();
  }

  function handleFileSelect(e) {
    if (fileInput.files.length > 0) {
      handleUpload();
    }
  }

  async function handleUpload() {
    const file = fileInput.files[0];
    if (!file) {
      showAlert('Please select a PDF file first.', 'danger');
      return;
    }

    if (!file.type.includes('pdf')) {
      showAlert('Please upload a PDF file.', 'danger');
      return;
    }

    const formData = new FormData();
    formData.append('pdf_file', file);

    progressContainer.classList.remove('d-none');
    processingSpinner.style.display = 'block';
    processingStatus.classList.remove('d-none');
    uploadButton.disabled = true;

    try {
      const response = await fetch('/upload_pdf', {
        method: 'POST',
        body: formData,
        onUploadProgress: (progressEvent) => {
          const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          updateProgress(percentCompleted);
        }
      });

      if (!response.ok) {
        throw new Error('Upload failed');
      }

      const data = await response.json();
      displayResults(data);
    } catch (error) {
      showAlert('Error processing PDF: ' + error.message, 'danger');
    } finally {
      uploadButton.disabled = false;
      processingSpinner.style.display = 'none';
      processingStatus.classList.add('d-none');
    }
  }

  function updateProgress(percent) {
    progressBar.style.width = `${percent}%`;
    progressBar.setAttribute('aria-valuenow', percent);
    progressBar.textContent = `${percent}%`;
  }

  function displayResults(data) {
    resultsSection.classList.remove('d-none');
    
    // Display images
    imagePreview.innerHTML = '';
    data.images.forEach(imagePath => {
      const img = document.createElement('img');
      img.src = imagePath;
      img.alt = 'Extracted image';
      img.loading = 'lazy';
      imagePreview.appendChild(img);
    });

    // Display initial summary
    addMessage(data.reply, 'bot');
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth' });
  }

  async function handleChat(e) {
    e.preventDefault();
    const message = userInput.value.trim();
    if (!message) return;

    addMessage(message, 'user');
    userInput.value = '';
    userInput.disabled = true;

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `user_input=${encodeURIComponent(message)}`
      });

      const data = await response.json();
      addMessage(data.reply, 'bot');
    } catch (error) {
      showAlert('Error sending message: ' + error.message, 'danger');
    } finally {
      userInput.disabled = false;
      userInput.focus();
    }
  }

  function addMessage(content, type) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', `${type}-message`);
    messageDiv.textContent = content;
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function showAlert(message, type) {
    const alert = document.createElement('div');
    alert.classList.add('alert', `alert-${type}`, 'mt-3');
    alert.textContent = message;
    document.querySelector('.upload-section').appendChild(alert);
    setTimeout(() => alert.remove(), 5000);
  }
});
