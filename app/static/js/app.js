// Глобальні змінні
let currentPage = 1;
let totalPages = 1;
let currentView = 'grid'; // або 'list'
let currentFilters = {};
let currentSort = { sort_by: 'created_at', sort_order: -1 };

// DOM елементи, до яких будемо звертатися часто
const carsList = document.getElementById('carsList');
const pagination = document.getElementById('pagination');
const totalCars = document.getElementById('totalCars');
const filterForm = document.getElementById('filterForm');
const sortBy = document.getElementById('sortBy');
const sortOrder = document.getElementById('sortOrder');
const refreshCarsBtn = document.getElementById('refreshCars');
const runScraperBtn = document.getElementById('runScraper');
const startSearchBtn = document.getElementById('startSearch');

// Ініціалізація сторінки
document.addEventListener('DOMContentLoaded', () => {
    console.log('Сторінка завантажена, ініціалізація...');
    
    // Завантаження автомобілів
    loadCars();
    
    // Завантаження статистики
    loadStats();
    
    // Додаємо обробники подій
    setupEventListeners();
    
    // Встановлюємо вибраний вигляд (сітка або список)
    setView('grid');
});

// Налаштування всіх обробників подій
function setupEventListeners() {
    // Форма фільтрів
    filterForm.addEventListener('submit', (e) => {
        e.preventDefault();
        applyFilters();
    });
    
    // Зміна сортування
    sortBy.addEventListener('change', () => {
        currentSort.sort_by = sortBy.value;
        loadCars();
    });
    
    sortOrder.addEventListener('change', () => {
        currentSort.sort_order = Number(sortOrder.value);
        loadCars();
    });
    
    // Оновлення списку автомобілів
    refreshCarsBtn.addEventListener('click', () => {
        loadCars();
    });
    
    // Запуск скрапера
    runScraperBtn.addEventListener('click', () => {
        runScraper();
    });
    
    // Кнопка початку пошуку (прокрутка до списку)
    startSearchBtn.addEventListener('click', () => {
        document.querySelector('.content-section').scrollIntoView({ behavior: 'smooth' });
    });
    
    // Обробники зміни вигляду (сітка/список)
    document.querySelectorAll('.view-option').forEach(option => {
        option.addEventListener('click', (e) => {
            e.preventDefault();
            setView(e.target.closest('.view-option').dataset.view);
        });
    });
}

// Завантаження списку автомобілів з API
async function loadCars() {
    showLoading();
    
    try {
        // Формуємо URL з параметрами
        let url = `/api/v1/cars?page=${currentPage}&limit=10&sort_by=${currentSort.sort_by}&sort_order=${currentSort.sort_order}`;
        
        // Додаємо параметри фільтрації, якщо вони є
        if (currentFilters.make) url += `&make=${encodeURIComponent(currentFilters.make)}`;
        if (currentFilters.min_price) url += `&min_price=${currentFilters.min_price}`;
        if (currentFilters.max_price) url += `&max_price=${currentFilters.max_price}`;
        if (currentFilters.min_year) url += `&min_year=${currentFilters.min_year}`;
        if (currentFilters.max_year) url += `&max_year=${currentFilters.max_year}`;
        
        console.log(`Запит до API: ${url}`);
        
        // Виконуємо запит
        const response = await fetch(url);
        
        if (!response.ok) {
            throw new Error(`HTTP помилка: ${response.status}`);
        }
        
        const data = await response.json();
        console.log('Отримано відповідь від API:', data);
        
        // Зберігаємо дані пагінації
        currentPage = data.page;
        totalPages = data.total_pages;
        
        // Оновлюємо лічильник автомобілів
        totalCars.textContent = `Знайдено: ${data.total}`;
        
        // Відображаємо автомобілі
        displayCars(data.data);
        
        // Оновлюємо пагінацію
        updatePagination();
        
    } catch (error) {
        console.error('Помилка при завантаженні автомобілів:', error);
        carsList.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="alert alert-danger" role="alert">
                    <i class="fas fa-exclamation-triangle"></i> Помилка завантаження даних: ${error.message}
                </div>
                <button class="btn btn-primary mt-3" onclick="loadCars()">
                    <i class="fas fa-sync-alt"></i> Спробувати знову
                </button>
            </div>
        `;
    }
}

// Завантаження статистики
async function loadStats() {
    try {
        const response = await fetch('/api/v1/cars/stats');
        
        if (!response.ok) {
            throw new Error(`HTTP помилка: ${response.status}`);
        }
        
        const stats = await response.json();
        
        // Оновлюємо статистику на сторінці
        document.getElementById('totalCarsCount').textContent = stats.total_cars;
        document.getElementById('avgPrice').textContent = '$' + formatNumber(stats.avg_price);
        document.getElementById('avgYear').textContent = stats.avg_year;
        document.getElementById('avgMileage').textContent = formatNumber(stats.avg_mileage) + ' км';
        
    } catch (error) {
        console.error('Помилка при завантаженні статистики:', error);
    }
}

// Відображення автомобілів
function displayCars(cars) {
    // Очищаємо контейнер
    carsList.innerHTML = '';
    
    // Перевіряємо, чи є автомобілі
    if (!cars || cars.length === 0) {
        carsList.innerHTML = `
            <div class="col-12 text-center py-5">
                <div class="alert alert-info" role="alert">
                    <i class="fas fa-info-circle"></i> Автомобілі не знайдено.
                </div>
                <button class="btn btn-primary mt-3" id="clearFilters">
                    <i class="fas fa-filter"></i> Скинути фільтри
                </button>
            </div>
        `;
        
        document.getElementById('clearFilters').addEventListener('click', clearFilters);
        return;
    }
    
    // Відображаємо автомобілі відповідно до вибраного вигляду
    if (currentView === 'list') {
        displayListView(cars);
    } else {
        displayGridView(cars);
    }
}

// Відображення у вигляді сітки
function displayGridView(cars) {
    cars.forEach((car, index) => {
        const carCard = document.createElement('div');
        carCard.className = 'col-md-6 col-lg-4 mb-4 animate-fade-in';
        carCard.style.animationDelay = `${index * 0.05}s`;
        
        carCard.innerHTML = `
            <div class="car-card">
                <div class="car-image-wrapper">
                    <img src="${car.image_url || 'https://via.placeholder.com/300x200?text=Немає+фото'}" 
                         class="car-image" alt="${car.make} ${car.model}">
                    <span class="car-year">${car.year}</span>
                </div>
                <div class="car-body">
                    <h5 class="car-title">${car.make} ${car.model}</h5>
                    <div class="car-price">$${formatNumber(car.price)}</div>
                    <div class="car-features">
                        <div class="car-feature">
                            <i class="fas fa-tachometer-alt"></i>
                            <span>${formatNumber(car.mileage)} км</span>
                        </div>
                        <div class="car-feature">
                            <i class="fas fa-gas-pump"></i>
                            <span>${car.engine_type}, ${car.engine_volume} л</span>
                        </div>
                        <div class="car-feature">
                            <i class="fas fa-cog"></i>
                            <span>${car.transmission}</span>
                        </div>
                        <div class="car-feature">
                            <i class="fas fa-map-marker-alt"></i>
                            <span>${car.location}</span>
                        </div>
                    </div>
                    <div class="car-actions">
                        <button class="btn btn-sm btn-outline-primary view-details" data-car-id="${car.id}">
                            <i class="fas fa-info-circle"></i> Деталі
                        </button>
                        <a href="${car.url}" target="_blank" class="btn btn-sm btn-primary">
                            <i class="fas fa-external-link-alt"></i> AUTO.RIA
                        </a>
                    </div>
                </div>
            </div>
        `;
        
        carsList.appendChild(carCard);
        
        // Додаємо обробник для кнопки деталей
        carCard.querySelector('.view-details').addEventListener('click', () => {
            showCarDetails(car);
        });
    });
}

// Відображення у вигляді списку
function displayListView(cars) {
    cars.forEach((car, index) => {
        const carCard = document.createElement('div');
        carCard.className = 'col-12 mb-3 animate-fade-in';
        carCard.style.animationDelay = `${index * 0.05}s`;
        
        carCard.innerHTML = `
            <div class="car-list-item">
                <a href="${car.url}" target="_blank" class="car-image-container">
                    <img src="${car.image_url || 'https://via.placeholder.com/300x200?text=Немає+фото'}" 
                         class="car-image" alt="${car.make} ${car.model}">
                    <div class="car-image-overlay">
                        <i class="fas fa-external-link-alt"></i>
                    </div>
                </a>
                <div class="car-details">
                    <h5 class="card-title">${car.make} ${car.model} (${car.year})</h5>
                    <div class="car-specs">
                        <div class="car-detail">
                            <i class="fas fa-tachometer-alt"></i>
                            <span>${formatNumber(car.mileage)} км</span>
                        </div>
                        <div class="car-detail">
                            <i class="fas fa-gas-pump"></i>
                            <span>${car.engine_type}, ${car.engine_volume} л</span>
                        </div>
                        <div class="car-detail">
                            <i class="fas fa-cog"></i>
                            <span>${car.transmission}</span>
                        </div>
                        <div class="car-detail">
                            <i class="fas fa-map-marker-alt"></i>
                            <span>${car.location}</span>
                        </div>
                    </div>
                </div>
                <div class="car-price-container">
                    <span class="car-price mb-2">$${formatNumber(car.price)}</span>
                    <div class="btn-group">
                        <button class="btn btn-sm btn-outline-primary view-details" data-car-id="${car.id}">
                            <i class="fas fa-info-circle"></i> Деталі
                        </button>
                        <a href="${car.url}" target="_blank" class="btn btn-sm btn-primary">
                            <i class="fas fa-external-link-alt"></i> AUTO.RIA
                        </a>
                    </div>
                </div>
            </div>
        `;
        carsList.appendChild(carCard);

        // Додаємо обробник для кнопки деталей
        carCard.querySelector('.view-details').addEventListener('click', () => {
            showCarDetails(car);
        });
    });
}

// Застосування фільтрів
function applyFilters() {
    // Збираємо значення фільтрів
    const make = document.getElementById('make').value.trim();
    const minPrice = document.getElementById('minPrice').value.trim();
    const maxPrice = document.getElementById('maxPrice').value.trim();
    const minYear = document.getElementById('minYear').value.trim();
    const maxYear = document.getElementById('maxYear').value.trim();
    
    // Оновлюємо об'єкт фільтрів
    currentFilters = {};
    
    if (make) currentFilters.make = make;
    if (minPrice) currentFilters.min_price = parseInt(minPrice);
    if (maxPrice) currentFilters.max_price = parseInt(maxPrice);
    if (minYear) currentFilters.min_year = parseInt(minYear);
    if (maxYear) currentFilters.max_year = parseInt(maxYear);
    
    // Скидаємо сторінку на першу
    currentPage = 1;
    
    // Завантажуємо автомобілі з новими фільтрами
    loadCars();
}

// Скидання фільтрів
function clearFilters() {
    // Очищаємо поля форми
    document.getElementById('make').value = '';
    document.getElementById('minPrice').value = '';
    document.getElementById('maxPrice').value = '';
    document.getElementById('minYear').value = '';
    document.getElementById('maxYear').value = '';
    
    // Скидаємо об'єкт фільтрів
    currentFilters = {};
    
    // Завантажуємо автомобілі без фільтрів
    loadCars();
}

// Оновлення пагінації
function updatePagination() {
    pagination.innerHTML = '';
    
    if (totalPages <= 1) {
        return;
    }
    
    // Кнопка "Попередня"
    const prevButton = document.createElement('li');
    prevButton.className = `page-item ${currentPage === 1 ? 'disabled' : ''}`;
    prevButton.innerHTML = `
        <a class="page-link" href="#" aria-label="Попередня">
            <span aria-hidden="true">&laquo;</span>
        </a>
    `;
    
    if (currentPage > 1) {
        prevButton.querySelector('a').addEventListener('click', (e) => {
            e.preventDefault();
            goToPage(currentPage - 1);
        });
    }
    
    pagination.appendChild(prevButton);
    
    // Номери сторінок
    const maxVisiblePages = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
    let endPage = Math.min(totalPages, startPage + maxVisiblePages - 1);
    
    if (endPage - startPage + 1 < maxVisiblePages) {
        startPage = Math.max(1, endPage - maxVisiblePages + 1);
    }
    
    for (let i = startPage; i <= endPage; i++) {
        const pageItem = document.createElement('li');
        pageItem.className = `page-item ${i === currentPage ? 'active' : ''}`;
        pageItem.innerHTML = `<a class="page-link" href="#">${i}</a>`;
        
        pageItem.querySelector('a').addEventListener('click', (e) => {
            e.preventDefault();
            goToPage(i);
        });
        
        pagination.appendChild(pageItem);
    }
    
    // Кнопка "Наступна"
    const nextButton = document.createElement('li');
    nextButton.className = `page-item ${currentPage === totalPages ? 'disabled' : ''}`;
    nextButton.innerHTML = `
        <a class="page-link" href="#" aria-label="Наступна">
            <span aria-hidden="true">&raquo;</span>
        </a>
    `;
    
    if (currentPage < totalPages) {
        nextButton.querySelector('a').addEventListener('click', (e) => {
            e.preventDefault();
            goToPage(currentPage + 1);
        });
    }
    
    pagination.appendChild(nextButton);
}

// Перехід на вказану сторінку
function goToPage(page) {
    if (page !== currentPage && page >= 1 && page <= totalPages) {
        currentPage = page;
        loadCars();
        window.scrollTo({
            top: document.querySelector('.content-section').offsetTop - 70,
            behavior: 'smooth'
        });
    }
}

// Запуск скрапера
async function runScraper() {
    try {
        // Показуємо повідомлення про запуск
        showMessage('Запуск скрапера...', 'info');
        
        // Відправляємо запит на запуск скрапера (3 сторінки)
        const response = await fetch('/api/v1/scraper/run?pages=3', {
            method: 'POST'
        });
        
        if (!response.ok) {
            throw new Error(`HTTP помилка: ${response.status}`);
        }
        
        const result = await response.json();
        
        // Показуємо повідомлення про успіх
        showMessage(result.message, 'success');
        
        // Через 5 секунд оновлюємо список автомобілів
        setTimeout(() => {
            loadCars();
            loadStats();
        }, 5000);
        
    } catch (error) {
        console.error('Помилка при запуску скрапера:', error);
        showMessage(`Помилка при запуску скрапера: ${error.message}`, 'danger');
    }
}

// Показати деталі автомобіля
function showCarDetails(car) {
    const modal = new bootstrap.Modal(document.getElementById('carModal'));
    const modalContent = document.getElementById('carModalContent');
    const originalLink = document.getElementById('originalLink');
    
    modalContent.innerHTML = `
        <div class="row">
            <div class="col-md-6">
                <img src="${car.image_url || 'https://via.placeholder.com/300x200?text=Немає+фото'}" 
                     class="img-fluid rounded mb-3" alt="${car.make} ${car.model}">
            </div>
            <div class="col-md-6">
                <h4>${car.make} ${car.model} (${car.year})</h4>
                <div class="car-price-large mb-3">$${formatNumber(car.price)}</div>
                
                <div class="car-detail-item">
                    <i class="fas fa-tachometer-alt"></i>
                    <strong>Пробіг:</strong> ${formatNumber(car.mileage)} км
                </div>
                
                <div class="car-detail-item">
                    <i class="fas fa-gas-pump"></i>
                    <strong>Двигун:</strong> ${car.engine_type}, ${car.engine_volume} л
                </div>
                
                <div class="car-detail-item">
                    <i class="fas fa-cog"></i>
                    <strong>Трансмісія:</strong> ${car.transmission}
                </div>
                
                <div class="car-detail-item">
                    <i class="fas fa-map-marker-alt"></i>
                    <strong>Розташування:</strong> ${car.location}
                </div>
                
                <div class="car-detail-item">
                    <i class="fas fa-calendar-alt"></i>
                    <strong>Додано:</strong> ${formatDate(car.created_at)}
                </div>
            </div>
        </div>
    `;
    
    originalLink.href = car.url;
    modal.show();
}

// Допоміжні функції
function formatNumber(num) {
    return new Intl.NumberFormat('uk-UA').format(num);
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('uk-UA', {
        day: 'numeric',
        month: 'long',
        year: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    }).format(date);
}

// Показати індикатор завантаження
function showLoading() {
    carsList.innerHTML = `
        <div class="col-12 text-center py-5">
            <div class="spinner-border" role="status">
                <span class="visually-hidden">Завантаження...</span>
            </div>
            <p class="mt-3">Завантаження даних...</p>
        </div>
    `;
}

// Показати повідомлення
function showMessage(message, type = 'info') {
    // Створюємо елемент повідомлення
    const alertElement = document.createElement('div');
    alertElement.className = `alert alert-${type} alert-dismissible fade show`;
    alertElement.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Закрити"></button>
    `;
    
    // Додаємо повідомлення на сторінку
    const alertContainer = document.querySelector('.container');
    alertContainer.insertBefore(alertElement, alertContainer.firstChild);
    
    // Автоматично закриваємо через 5 секунд
    setTimeout(() => {
        const alert = new bootstrap.Alert(alertElement);
        alert.close();
    }, 5000);
}

// Встановлення вигляду (сітка/список)
function setView(view) {
    currentView = view;
    
    // Оновлюємо активну кнопку
    document.querySelectorAll('.view-option').forEach(option => {
        if (option.dataset.view === view) {
            option.classList.add('active');
        } else {
            option.classList.remove('active');
        }
    });
    
    // Якщо є автомобілі, перемальовуємо їх
    if (carsList.querySelectorAll('.view-details').length > 0) {
        loadCars();
    }
}