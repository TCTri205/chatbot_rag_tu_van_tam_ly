/**
 * Exercises Modal UI
 * Manages relaxation exercises display and interaction
 */

// Load and display exercises
async function loadExercises(category = null) {
    try {
        const url = category && category !== 'all'
            ? `/api/v1/exercises/?category=${category}`
            : '/api/v1/exercises/';

        const exercises = await fetch(url).then(r => r.json());

        const listDiv = document.getElementById('exercises-list');
        if (!listDiv) return;

        listDiv.innerHTML = exercises.map(ex => `
            <div class="exercise-card bg-white rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer border border-gray-200"
                 onclick="showExerciseDetail('${ex.id}')">
                <div class="flex items-start justify-between">
                    <div class="flex-1">
                        <h3 class="font-semibold text-lg text-gray-800">${ex.title}</h3>
                        <p class="text-sm text-gray-600 mt-1">${ex.description}</p>
                    </div>
                    <span class="ml-2 px-2 py-1 bg-${getCategoryColor(ex.category)}-100 text-${getCategoryColor(ex.category)}-700 text-xs rounded-full">
                        ${getCategoryLabel(ex.category)}
                    </span>
                </div>
                <div class="flex items-center mt-3 text-sm text-gray-500">
                    <i class="fas fa-clock mr-1"></i>
                    <span>${ex.duration_minutes} phút</span>
                    <span class="mx-2">•</span>
                    <span>${ex.benefits.length} lợi ích</span>
                </div>
            </div>
        `).join('');

    } catch (error) {
        console.error('Error loading exercises:', error);
        const listDiv = document.getElementById('exercises-list');
        if (listDiv) {
            listDiv.innerHTML = '<p class="text-red-600">Lỗi tải bài tập. Vui lòng thử lại sau.</p>';
        }
    }
}

// Show exercise detail modal
async function showExerciseDetail(exerciseId) {
    try {
        const exercises = await fetch('/api/v1/exercises/').then(r => r.json());
        const exercise = exercises.find(ex => ex.id === exerciseId);

        if (!exercise) return;

        const modal = document.getElementById('exercise-detail-modal');
        const content = document.getElementById('exercise-detail-content');

        content.innerHTML = `
            <div class="text-center mb-6">
                <h2 class="text-2xl font-bold text-gray-800">${exercise.title}</h2>
                <p class="text-gray-600 mt-2">${exercise.description}</p>
                <div class="mt-3 flex items-center justify-center text-sm text-gray-500">
                    <i class="fas fa-clock mr-1"></i>
                    <span>${exercise.duration_minutes} phút</span>
                </div>
            </div>
            
            <div class="bg-blue-50 rounded-lg p-4 mb-6">
                <h3 class="font-semibold text-blue-800 mb-2">
                    <i class="fas fa-clipboard-list mr-2"></i>Các bước thực hiện
                </h3>
                <ol class="list-decimal list-inside space-y-2 text-gray-700">
                    ${exercise.steps.map(step => `<li>${step}</li>`).join('')}
                </ol>
            </div>
            
            <div class="bg-green-50 rounded-lg p-4">
                <h3 class="font-semibold text-green-800 mb-2">
                    <i class="fas fa-heart mr-2"></i>Lợi ích
                </h3>
                <ul class="list-disc list-inside space-y-1 text-gray-700">
                    ${exercise.benefits.map(benefit => `<li>${benefit}</li>`).join('')}
                </ul>
            </div>
        `;

        modal.classList.remove('hidden');
        modal.classList.add('flex');

    } catch (error) {
        console.error('Error showing exercise detail:', error);
    }
}

// Close exercise detail modal
function closeExerciseDetail() {
    const modal = document.getElementById('exercise-detail-modal');
    modal.classList.add('hidden');
    modal.classList.remove('flex');
}

// Get category color for Tailwind classes
function getCategoryColor(category) {
    const colors = {
        'breathing': 'blue',
        'mindfulness': 'purple',
        'relaxation': 'green'
    };
    return colors[category] || 'gray';
}

// Get Vietnamese label for category
function getCategoryLabel(category) {
    const labels = {
        'breathing': 'Hơi Thở',
        'mindfulness': 'Chánh Niệm',
        'relaxation': 'Thư Giãn'
    };
    return labels[category] || category;
}

// Initialize exercises modal
document.addEventListener('DOMContentLoaded', () => {
    const exercisesButton = document.getElementById('exercises-button');
    const exercisesModal = document.getElementById('exercises-modal');
    const closeExercisesBtn = document.getElementById('close-exercises-modal');

    // Load categories with proper error handling
    fetch('/api/v1/exercises/categories')
        .then(r => {
            if (!r.ok) {
                throw new Error(`HTTP ${r.status}: ${r.statusText}`);
            }
            return r.json();
        })
        .then(data => {
            const tabsDiv = document.getElementById('exercise-tabs');
            if (tabsDiv && data && data.categories && Array.isArray(data.categories)) {
                tabsDiv.innerHTML = `
                    <button class="tab-btn active" data-category="all">Tất cả</button>
                    ${data.categories.map(cat => `
                        <button class="tab-btn" data-category="${cat.name}">
                            ${cat.label} (${cat.count})
                        </button>
                    `).join('')}
                `;

                // Add click handlers
                addTabClickHandlers();
            } else {
                console.warn('Invalid categories data:', data);
                showDefaultTabs();
            }
        })
        .catch(error => {
            console.error('Error loading exercise categories:', error);
            showDefaultTabs();
        });


    // Open modal
    if (exercisesButton) {
        exercisesButton.addEventListener('click', () => {
            exercisesModal.classList.remove('hidden');
            exercisesModal.classList.add('flex');
            loadExercises();
        });
    }

    // Close modal
    if (closeExercisesBtn) {
        closeExercisesBtn.addEventListener('click', () => {
            exercisesModal.classList.add('hidden');
            exercisesModal.classList.remove('flex');
        });
    }

    // Close on backdrop click
    if (exercisesModal) {
        exercisesModal.addEventListener('click', (e) => {
            if (e.target === exercisesModal) {
                exercisesModal.classList.add('hidden');
                exercisesModal.classList.remove('flex');
            }
        });
    }
});

// Helper function to add click handlers to tab buttons
function addTabClickHandlers() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            loadExercises(e.target.dataset.category);
        });
    });
}

// Helper function to show default tabs when API fails
function showDefaultTabs() {
    const tabsDiv = document.getElementById('exercise-tabs');
    if (!tabsDiv) return;

    tabsDiv.innerHTML = `
        <button class="tab-btn active" data-category="all">Tất cả</button>
        <button class="tab-btn" data-category="breathing">Hơi Thở</button>
        <button class="tab-btn" data-category="mindfulness">Chánh Niệm</button>
        <button class="tab-btn" data-category="relaxation">Thư Giãn</button>
    `;

    // Add click handlers for default tabs
    addTabClickHandlers();
}
