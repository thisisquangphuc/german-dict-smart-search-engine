class GermanQuiz {
    constructor() {
        this.currentSentence = null;
        this.words = [];
        this.correctWordOrder = [];  // Store correct order for hints
        this.selectedWords = [];
        this.correctCount = 0;
        this.totalCount = 0;
        this.currentIndex = 0;
        this.sentences = [];
        this.isAnswerChecked = false;  // Track if current answer has been checked
        this.hintCount = 0;  // Track hint clicks

        // DOM elements
        this.englishTranslation = document.getElementById('english-translation');
        this.sentenceBuilder = document.getElementById('sentence-builder');
        this.wordBank = document.getElementById('word-bank');
        this.checkBtn = document.getElementById('check-btn');
        this.hintBtn = document.getElementById('hint-btn');
        this.nextBtn = document.getElementById('next-btn');
        this.correctCountEl = document.getElementById('correct-count');
        this.totalCountEl = document.getElementById('total-count');
        this.lastDayResultEl = document.getElementById('last-day-result');  // Optional element

        // Create hint text element
        this.hintText = document.createElement('div');
        this.hintText.className = 'hint-text';
        this.wordBank.parentNode.insertBefore(this.hintText, this.wordBank.nextSibling);

        // Create correct sentence display element
        this.correctSentenceDisplay = document.createElement('div');
        this.correctSentenceDisplay.className = 'correct-sentence';
        this.englishTranslation.parentNode.insertBefore(this.correctSentenceDisplay, this.englishTranslation.nextSibling);

        // Bind event listeners
        this.checkBtn.addEventListener('click', () => this.checkAnswer());
        this.hintBtn.addEventListener('click', () => this.showHint());
        this.nextBtn.addEventListener('click', () => this.nextQuestion());
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => this.handleKeyboard(e));

        // Initialize
        this.loadProgress();
        this.fetchSentences();
    }

    async fetchSentences() {
        try {
            const response = await fetch('/api/quiz/sentences');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            this.sentences = await response.json();
            console.log('Fetched sentences:', this.sentences); // Debug log
            if (this.sentences && this.sentences.length > 0) {
                this.loadQuestion();
            } else {
                console.error('No sentences loaded');
                this.englishTranslation.textContent = 'No sentences available';
            }
        } catch (error) {
            console.error('Error fetching sentences:', error);
            this.englishTranslation.textContent = 'Error loading sentences';
        }
    }

    loadQuestion() {
        if (!this.sentences || this.sentences.length === 0) {
            console.error('No sentences available to load question');
            return;
        }

        if (this.currentIndex >= this.sentences.length) {
            this.currentIndex = 0;
        }

        this.currentSentence = this.sentences[this.currentIndex];
        
        if (!this.currentSentence || !this.currentSentence.english || !this.currentSentence.german) {
            console.error('Invalid sentence data:', this.currentSentence);
            return;
        }

        this.englishTranslation.textContent = this.currentSentence.english;
        this.correctSentenceDisplay.style.display = 'none';
        
        // Reset states for new question
        this.hintCount = 0;
        this.hintText.textContent = '';
        this.isAnswerChecked = false;
        this.selectedWords = [];
        
        // Split German sentence into words, keeping punctuation, numbers, and special characters with the preceding word
        this.correctWordOrder = this.currentSentence.german.match(/[a-zA-ZäöüÄÖÜß0-9:/-]+[.,!?]?|\s+/g)
            .filter(word => word.trim());
        
        // Create a shuffled copy for display using Fisher-Yates shuffle
        this.words = [...this.correctWordOrder];
        for (let i = this.words.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [this.words[i], this.words[j]] = [this.words[j], this.words[i]];
        }
        
        this.renderWords();
        
        // Enable next button for new question
        this.nextBtn.disabled = false;
        
        // Remove any previous correct/incorrect styling
        const words = this.sentenceBuilder.querySelectorAll('.word');
        words.forEach(word => word.classList.remove('correct'));
        this.sentenceBuilder.classList.remove('incorrect');
    }

    renderWords() {
        // Clear existing words
        this.wordBank.innerHTML = '';
        this.sentenceBuilder.innerHTML = '';

        if (!this.words || this.words.length === 0) {
            console.error('No words to render');
            return;
        }

        // Create a map to track remaining instances of each word
        const wordCount = new Map();
        this.words.forEach(word => {
            wordCount.set(word, (wordCount.get(word) || 0) + 1);
        });

        // Render word bank
        this.words.forEach((word, index) => {
            // Count how many times this word appears in selectedWords
            const selectedCount = this.selectedWords.filter(w => w === word).length;
            // Only render if this word hasn't been selected yet
            if (!this.selectedWords.includes(word)) {
                const wordEl = document.createElement('div');
                wordEl.className = 'word';
                wordEl.textContent = word;
                wordEl.tabIndex = 0;
                wordEl.dataset.index = index;
                wordEl.addEventListener('click', () => this.selectWord(word));
                this.wordBank.appendChild(wordEl);
            }
        });

        // Render selected words
        this.selectedWords.forEach((word, index) => {
            const wordEl = document.createElement('div');
            wordEl.className = 'word selected';
            wordEl.textContent = word;
            wordEl.tabIndex = 0;
            wordEl.dataset.index = index;
            wordEl.addEventListener('click', () => this.unselectWord(word));
            this.sentenceBuilder.appendChild(wordEl);
        });

        // Remove correct/incorrect styling when answer changes
        if (!this.isAnswerChecked) {
            const words = this.sentenceBuilder.querySelectorAll('.word');
            words.forEach(word => word.classList.remove('correct'));
            this.sentenceBuilder.classList.remove('incorrect');
        }
    }

    selectWord(word) {
        this.selectedWords.push(word);
        this.isAnswerChecked = false;  // Reset check state when user changes answer
        this.renderWords();
        this.checkBtn.focus();
    }

    unselectWord(word) {
        const index = this.selectedWords.indexOf(word);
        if (index > -1) {
            this.selectedWords.splice(index, 1);
            this.isAnswerChecked = false;  // Reset check state when user changes answer
            this.renderWords();
        }
    }

    checkAnswer() {
        if (this.isAnswerChecked) {
            return;  // Don't check again if already checked
        }

        const userAnswer = this.selectedWords.join(' ').toLowerCase().trim();
        const correctAnswer = this.currentSentence.german.toLowerCase().trim();
        
        // Increment total count when checking answer
        this.totalCount++;
        
        // Normalize strings for comparison (handle umlauts)
        const normalizedUserAnswer = userAnswer.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
        const normalizedCorrectAnswer = correctAnswer.normalize('NFD').replace(/[\u0300-\u036f]/g, '');
        
        if (normalizedUserAnswer === normalizedCorrectAnswer) {
            this.correctCount++;
            this.updateProgress();
            this.showConfetti();
            this.highlightCorrect();
            // Show correct sentence
            this.correctSentenceDisplay.textContent = this.currentSentence.german;
            this.correctSentenceDisplay.style.display = 'block';
        } else {
            this.highlightIncorrect();
            this.correctSentenceDisplay.style.display = 'none';
        }
        
        this.isAnswerChecked = true;  // Mark as checked
        this.nextBtn.disabled = false;  // Enable next button after checking
        this.nextBtn.focus();
    }

    showHint() {
        this.hintCount++;
        
        if (this.hintCount <= 2) {
            // Get the next correct word that hasn't been selected yet
            const nextCorrectWord = this.correctWordOrder[this.selectedWords.length];
            if (nextCorrectWord) {
                this.selectWord(nextCorrectWord);
            }
        } else {
            // Show the complete sentence after two hints
            this.hintText.textContent = this.currentSentence.german;
        }
    }

    nextQuestion() {
        // If user has made an attempt (selected words), check the answer first
        if (this.selectedWords.length > 0 && !this.isAnswerChecked) {
            this.checkAnswer();
            return;  // Stop here and let user click next again
        }
        
        this.currentIndex++;
        this.loadQuestion();
    }

    handleKeyboard(e) {
        if (e.key === 'Tab') {
            e.preventDefault();
            const focused = document.activeElement;
            const words = [...this.wordBank.children, ...this.sentenceBuilder.children];
            const currentIndex = words.indexOf(focused);
            
            if (currentIndex > -1) {
                const nextIndex = e.shiftKey ? 
                    (currentIndex - 1 + words.length) % words.length :
                    (currentIndex + 1) % words.length;
                words[nextIndex].focus();
            }
        } else if (e.key === 'Enter' && document.activeElement.classList.contains('word')) {
            const word = document.activeElement.textContent;
            if (document.activeElement.parentElement === this.wordBank) {
                this.selectWord(word);
            } else {
                this.unselectWord(word);
            }
        }
    }

    showConfetti() {
        confetti({
            particleCount: 100,
            spread: 70,
            origin: { y: 0.6 }
        });
    }

    highlightCorrect() {
        // Add correct class to each word in the sentence builder
        const words = this.sentenceBuilder.querySelectorAll('.word');
        words.forEach(word => word.classList.add('correct'));
        this.showConfetti();
    }

    highlightIncorrect() {
        this.sentenceBuilder.classList.add('incorrect');
        setTimeout(() => {
            this.sentenceBuilder.classList.remove('incorrect');
        }, 1000);
    }

    async loadProgress() {
        try {
            const response = await fetch('/api/quiz/progress');
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const progress = await response.json();
            const today = new Date().toISOString().split('T')[0];
            
            // Reset counts
            this.correctCount = 0;
            this.totalCount = 0;
            
            // Get today's progress if it exists
            if (progress[today]) {
                this.correctCount = progress[today].correct;
                this.totalCount = progress[today].total;
            }
            
            // Get last day's result
            const dates = Object.keys(progress).sort();
            if (dates.length > 0) {
                // Find the most recent date that's not today
                let lastDate = null;
                for (let i = dates.length - 1; i >= 0; i--) {
                    if (dates[i] !== today) {
                        lastDate = dates[i];
                        break;
                    }
                }
                
                if (lastDate && this.lastDayResultEl) {
                    const lastDayResult = progress[lastDate];
                    this.lastDayResultEl.textContent = `Last day (${lastDate}): ${lastDayResult.correct}`;
                } else if (this.lastDayResultEl) {
                    this.lastDayResultEl.textContent = '';
                }
            }
            
            this.updateProgressDisplay();
        } catch (error) {
            console.error('Error loading progress:', error);
        }
    }

    async updateProgress() {
        try {
            const today = new Date().toISOString().split('T')[0];
            const progress = {
                date: today,
                correct: this.correctCount,
                total: this.totalCount
            };

            const response = await fetch('/api/quiz/progress', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(progress)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Reload progress to update both today's and last day's results
            await this.loadProgress();
        } catch (error) {
            console.error('Error updating progress:', error);
        }
    }

    updateProgressDisplay() {
        if (this.correctCountEl) {
            this.correctCountEl.textContent = this.correctCount;
        }
        if (this.totalCountEl) {
            this.totalCountEl.textContent = this.totalCount;
        }
    }
}

// Initialize the quiz when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new GermanQuiz();
}); 