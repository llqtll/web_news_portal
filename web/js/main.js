// Валидация формы регистрации
function initRegisterForm() {
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        // Валидация в реальном времени
        const usernameInput = document.getElementById('username');
        const emailInput = document.getElementById('email');
        const passwordInput = document.getElementById('password');
        const confirmPasswordInput = document.getElementById('confirm-password');

        // Валидация имени пользователя при вводе
        if (usernameInput) {
            usernameInput.addEventListener('input', function() {
                validateUsername(this.value);
            });
            usernameInput.addEventListener('blur', function() {
                validateUsername(this.value);
            });
        }

        // Валидация email при вводе
        if (emailInput) {
            emailInput.addEventListener('input', function() {
                validateEmail(this.value);
            });
            emailInput.addEventListener('blur', function() {
                validateEmail(this.value);
            });
        }

        // Валидация пароля при вводе
        if (passwordInput) {
            passwordInput.addEventListener('input', function() {
                validatePassword(this.value);
                // Также валидируем подтверждение пароля
                validateConfirmPassword(confirmPasswordInput.value, this.value);
            });
            passwordInput.addEventListener('blur', function() {
                validatePassword(this.value);
            });
        }

        // Валидация подтверждения пароля при вводе
        if (confirmPasswordInput) {
            confirmPasswordInput.addEventListener('input', function() {
                validateConfirmPassword(this.value, passwordInput.value);
            });
            confirmPasswordInput.addEventListener('blur', function() {
                validateConfirmPassword(this.value, passwordInput.value);
            });
        }

        // Обработчик отправки формы
        registerForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                username: usernameInput.value.trim(),
                email: emailInput.value.trim(),
                password: passwordInput.value,
                confirmPassword: confirmPasswordInput.value
            };

            // Финальная валидация перед отправкой
            if (!validateRegisterForm(formData)) {
                return;
            }

            // Если валидация прошла, отправляем форму
            registerForm.submit();
        });
    }
}

// Валидация имени пользователя в реальном времени
function validateUsername(username) {
    const value = username.trim();
    hideError('username');

    if (!value) {
        return false;
    }

    if (value.length < 3) {
        showError('username', 'Имя пользователя должно содержать минимум 3 символа');
        return false;
    }

    if (!/^[a-zA-Z0-9_]+$/.test(value)) {
        showError('username', 'Имя пользователя может содержать только буквы, цифры и символ подчеркивания');
        return false;
    }

    return true;
}

// Валидация email в реальном времени
function validateEmail(email) {
    const value = email.trim();
    hideError('email');

    if (!value) {
        return false;
    }

    if (!isValidEmail(value)) {
        showError('email', 'Введите корректный email адрес');
        return false;
    }

    return true;
}

// Валидация пароля в реальном времени
function validatePassword(password) {
    hideError('password');

    if (!password) {
        return false;
    }

    if (password.length < 6) {
        showError('password', 'Пароль должен содержать минимум 6 символов');
        return false;
    }

    return true;
}

// Валидация подтверждения пароля в реальном времени
function validateConfirmPassword(confirmPassword, password) {
    hideError('confirm-password');

    if (!confirmPassword) {
        return false;
    }

    if (confirmPassword !== password) {
        showError('confirm-password', 'Пароли не совпадают');
        return false;
    }

    return true;
}

// Финальная валидация всей формы
function validateRegisterForm(formData) {
    let isValid = true;

    // Проверяем все поля
    if (!validateUsername(formData.username)) {
        isValid = false;
    }

    if (!validateEmail(formData.email)) {
        isValid = false;
    }

    if (!validatePassword(formData.password)) {
        isValid = false;
    }

    if (!validateConfirmPassword(formData.confirmPassword, formData.password)) {
        isValid = false;
    }

    return isValid;
}

// Функция для очистки ошибок
function clearErrors() {
    const errorElements = document.querySelectorAll('.error-message');
    errorElements.forEach(element => {
        element.textContent = '';
        element.style.display = 'none';
    });
}

// Функция для показа ошибки
function showError(fieldId, message) {
    const errorElement = document.getElementById(fieldId + 'Error');
    if (errorElement) {
        errorElement.textContent = message;
        errorElement.style.display = 'block';
        
        // Добавляем класс ошибки к родительскому элементу
        const inputElement = document.getElementById(fieldId);
        if (inputElement) {
            inputElement.classList.add('error');
        }
    }
}

// Функция для скрытия ошибки
function hideError(fieldId) {
    const errorElement = document.getElementById(fieldId + 'Error');
    if (errorElement) {
        errorElement.textContent = '';
        errorElement.style.display = 'none';
        
        // Убираем класс ошибки с поля ввода
        const inputElement = document.getElementById(fieldId);
        if (inputElement) {
            inputElement.classList.remove('error');
        }
    }
}

// Проверка email с помощью регулярного выражения
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initRegisterForm();
});






// -------------------article.html-----------------------
// Функция для генерации slug из заголовка
function generateSlug(title) {
    return title
        .toLowerCase()
        .trim()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_-]+/g, '-')
        .replace(/^-+|-+$/g, '');
}

// Автозаполнение slug при вводе заголовка
if (document.getElementById('articleTitle')) {
    document.getElementById('articleTitle').addEventListener('input', function() {
        const title = this.value;
        const slugField = document.getElementById('articleSlug');
        if (!slugField.value || slugField.dataset.manual !== 'true') {
            slugField.value = generateSlug(title);
        }
    });

    // Пометить slug как измененный вручную
    document.getElementById('articleSlug').addEventListener('input', function() {
        this.dataset.manual = 'true';
    });
}








// Drag & Drop для изображения
function initImageUpload() {
    const fileInput = document.getElementById('articleImage');
    const imagePreview = document.getElementById('imagePreview');
    const previewImage = document.getElementById('previewImage');
    const removeButton = document.getElementById('removeImage');

    if (!fileInput) return;

    // Обработка выбора файла
    fileInput.addEventListener('change', function(e) {
        handleFileSelect(e.target.files[0]);
    });

    // Drag & Drop события
    const dropZone = fileInput.closest('.form-group') || fileInput;
    
    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        this.classList.add('drag-over');
    });

    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.classList.remove('drag-over');
    });

    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        this.classList.remove('drag-over');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            handleFileSelect(files[0]);
        }
    });

    // Удаление изображения
    removeButton.addEventListener('click', function() {
        fileInput.value = '';
        imagePreview.style.display = 'none';
        previewImage.src = '';
    });

    function handleFileSelect(file) {
        if (file && file.type.startsWith('image/')) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                previewImage.src = e.target.result;
                imagePreview.style.display = 'block';
            };
            
            reader.readAsDataURL(file);
        } else {
            alert('Пожалуйста, выберите файл изображения');
        }
    }
}

// Обновите обработчик формы для отправки файла
if (document.getElementById('createArticleForm')) {
    document.getElementById('createArticleForm').addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData(this);
        const imageFile = document.getElementById('articleImage').files[0];
        
        // Добавляем файл изображения в FormData
        if (imageFile) {
            formData.append('featured_image_file', imageFile);
        }
        
        try {
            const response = await fetch('/api/articles', {
                method: 'POST',
                body: formData // Отправляем как FormData
            });
            
            const result = await response.json();
            
            if (result.success) {
                alert('Статья успешно создана!');
                window.location.href = '/';
            } else {
                alert('Ошибка: ' + (result.error || 'Неизвестная ошибка'));
            }
        } catch (error) {
            console.error('Error creating article:', error);
            alert('Ошибка сети');
        }
    });
}



// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initImageUpload();
    
});







