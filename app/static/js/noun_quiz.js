class NounQuiz {
    constructor() {
        this.nouns = [];
        this.currentNoun = null;
        this.currentMode = 'article';
        this.answerSubmitted = false;  // Add flag to track if answer is submitted
        this.initializeElements();
        this.loadNouns();
        this.setupEventListeners();
    }

    initializeElements() {
        // Mode selection
        this.modeButtons = document.querySelectorAll('.mode-btn');
        this.articleMode = document.getElementById('article-mode');
        this.typeMode = document.getElementById('type-mode');

        // Article mode elements
        this.nounDisplay = this.articleMode.querySelector('.noun');
        this.meaningDisplay = this.articleMode.querySelector('.meaning');
        this.articleButtons = this.articleMode.querySelectorAll('.article-btn');
        this.articleResult = this.articleMode.querySelector('.result');
        this.articleHintBtn = this.articleMode.querySelector('.hint-btn');
        this.articleNextBtn = this.articleMode.querySelector('.next-btn');

        // Type mode elements
        this.articleDisplay = this.typeMode.querySelector('.article');
        this.typeMeaningDisplay = this.typeMode.querySelector('.meaning');
        this.nounInput = this.typeMode.querySelector('.noun-input');
        this.typeResult = this.typeMode.querySelector('.result');
        this.typeHintBtn = this.typeMode.querySelector('.hint-btn');
        this.typeNextBtn = this.typeMode.querySelector('.next-btn');
    }

    async loadNouns() {
        try {
            const response = await fetch('/api/noun-quiz/nouns');
            this.nouns = await response.json();
            this.loadNextNoun();
        } catch (error) {
            console.error('Error loading nouns:', error);
        }
    }

    setupEventListeners() {
        // Mode selection
        this.modeButtons.forEach(btn => {
            btn.addEventListener('click', () => this.switchMode(btn.dataset.mode));
        });

        // Article mode
        this.articleButtons.forEach(btn => {
            btn.addEventListener('click', () => this.checkArticle(btn.dataset.article));
        });
        this.articleHintBtn.addEventListener('click', () => this.showHint());
        this.articleNextBtn.addEventListener('click', () => this.loadNextNoun());

        // Type mode
        this.nounInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                if (!this.answerSubmitted) {
                    // First Enter: Check the answer
                    this.checkNoun();
                } else {
                    // Second Enter: Move to next noun
                    this.loadNextNoun();
                }
            }
        });
        this.typeHintBtn.addEventListener('click', () => this.showHint());
        this.typeNextBtn.addEventListener('click', () => this.loadNextNoun());
    }

    switchMode(mode) {
        this.currentMode = mode;
        this.modeButtons.forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });
        this.articleMode.classList.toggle('active', mode === 'article');
        this.typeMode.classList.toggle('active', mode === 'type');
        this.loadNextNoun();
    }

    loadNextNoun() {
        if (this.nouns.length === 0) return;

        this.currentNoun = this.nouns[Math.floor(Math.random() * this.nouns.length)];
        console.log('Loaded new noun:', this.currentNoun);
        
        // Reset UI
        this.resetArticleMode();
        this.resetTypeMode();

        // Update displays
        if (this.currentMode === 'article') {
            this.nounDisplay.textContent = this.currentNoun.singular;
            this.meaningDisplay.textContent = this.currentNoun.meaning;
        } else {
            this.typeMeaningDisplay.textContent = this.currentNoun.meaning;
            this.nounInput.focus();  // Focus the input field
        }
    }

    resetArticleMode() {
        this.articleButtons.forEach(btn => {
            btn.classList.remove('correct', 'incorrect');
            btn.disabled = false;  // Re-enable buttons
        });
        this.articleResult.classList.add('hidden');
        this.articleHintBtn.classList.add('hidden');
        this.articleNextBtn.classList.remove('correct');  // Remove correct class from Next button
        this.answerSubmitted = false;  // Reset the flag
    }

    resetTypeMode() {
        this.nounInput.value = '';
        this.nounInput.classList.remove('error');
        this.typeResult.classList.add('hidden');
        this.typeHintBtn.classList.add('hidden');
        this.typeHintBtn.textContent = 'Hint';  // Reset hint button text
        this.typeNextBtn.classList.remove('correct');  // Remove correct class from Next button
        this.answerSubmitted = false;  // Reset the flag
        // Show input container again
        this.nounInput.parentElement.classList.remove('hidden');
        // Focus the input field for the next word
        this.nounInput.focus();
    }

    checkArticle(selectedArticle) {
        // If answer is already submitted, ignore clicks
        if (this.answerSubmitted) {
            return;
        }

        console.log('Selected article:', selectedArticle);
        console.log('Current noun article:', this.currentNoun.article);
        
        const isCorrect = selectedArticle === this.currentNoun.article;
        console.log('Is correct:', isCorrect);
        
        this.articleButtons.forEach(btn => {
            const btnArticle = btn.dataset.article;
            console.log('Button article:', btnArticle);
            
            if (btnArticle === selectedArticle) {
                if (isCorrect) {
                    btn.classList.add('correct');
                    console.log('Added correct class to selected button');
                } else {
                    btn.classList.add('incorrect');
                    console.log('Added incorrect class to selected button');
                }
            }
            // Only disable buttons if the answer is correct
            if (isCorrect) {
                btn.disabled = true;
            }
        });

        if (isCorrect) {
            this.answerSubmitted = true;  // Set flag when correct answer is submitted
            this.articleNextBtn.classList.add('correct');  // Add correct class to Next button
            this.showResult();
        } else {
            this.articleHintBtn.classList.remove('hidden');
        }
    }

    checkNoun() {
        const input = this.nounInput.value.trim();
        // Case-insensitive comparison
        const isCorrect = input.toLowerCase() === this.currentNoun.full_word.toLowerCase();

        if (isCorrect) {
            this.nounInput.classList.remove('error');
            this.answerSubmitted = true;  // Set flag when correct answer is submitted
            this.typeNextBtn.classList.add('correct');  // Add correct class to Next button
            this.showResult();
            this.showConfetti();
            // Hide input container when answer is correct
            this.nounInput.parentElement.classList.add('hidden');
            // Focus the Next button for the second Enter press
            this.typeNextBtn.focus();
        } else {
            this.nounInput.classList.add('error');
            this.typeHintBtn.classList.remove('hidden');
        }
    }

    showResult() {
        const result = this.currentMode === 'article' ? this.articleResult : this.typeResult;
        const hintBtn = this.currentMode === 'article' ? this.articleHintBtn : this.typeHintBtn;

        if (this.currentMode === 'article') {
            result.querySelector('.full-word').textContent = `Full word: ${this.currentNoun.full_word}`;
            result.querySelector('.plural').textContent = `Plural: ${this.currentNoun.plural}`;
            result.querySelector('.example').textContent = `Example: ${this.currentNoun.example}`;
        } else {
            // Show correct answer
            result.querySelector('.correct-answer').textContent = this.currentNoun.full_word;
            
            // Show plural if it exists and is not "N/A"
            const pluralBox = result.querySelector('.plural-box');
            const pluralText = result.querySelector('.plural');
            if (this.currentNoun.plural && this.currentNoun.plural !== "N/A") {
                pluralText.textContent = `Plural: ${this.currentNoun.plural}`;
                pluralBox.classList.remove('hidden');
            } else {
                pluralBox.classList.add('hidden');
            }
            
            // Show example if it exists and is not empty
            const exampleBox = result.querySelector('.example-box');
            const exampleText = result.querySelector('.example');
            if (this.currentNoun.example && this.currentNoun.example !== "No example available") {
                exampleText.textContent = this.currentNoun.example;
                exampleBox.classList.remove('hidden');
            } else {
                exampleBox.classList.add('hidden');
            }
        }
        
        result.classList.remove('hidden');
        hintBtn.classList.add('hidden');
    }

    showConfetti() {
        const duration = 3 * 1000;
        const animationEnd = Date.now() + duration;
        const defaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 0 };

        function randomInRange(min, max) {
            return Math.random() * (max - min) + min;
        }

        const interval = setInterval(function() {
            const timeLeft = animationEnd - Date.now();

            if (timeLeft <= 0) {
                return clearInterval(interval);
            }

            const particleCount = 50 * (timeLeft / duration);
            
            // since particles fall down, start a bit higher than random
            confetti({
                ...defaults,
                particleCount,
                origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 }
            });
            confetti({
                ...defaults,
                particleCount,
                origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 }
            });
        }, 250);
    }

    showHint() {
        const hintBtn = this.currentMode === 'article' ? this.articleHintBtn : this.typeHintBtn;
        if (this.currentMode === 'article') {
            hintBtn.textContent = `Hint: ${this.currentNoun.article}`;
        } else {
            // For type mode, show the full word
            hintBtn.textContent = `Hint: ${this.currentNoun.singular}`;
        }
    }
}

// Initialize the quiz when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new NounQuiz();
}); 