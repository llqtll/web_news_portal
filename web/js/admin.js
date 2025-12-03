document.addEventListener('DOMContentLoaded', function() {
    // Код для переключения разделов админ-панели
    const navLinks = document.querySelectorAll('.nav-link');
    const contentSections = document.querySelectorAll('.content-section');
    const navItems = document.querySelectorAll('.nav-item');

    // Проверяем, что мы в админ-панели
    if (contentSections.length > 0) {
        function switchSection(sectionId) {
            contentSections.forEach(section => {
                section.classList.remove('active');
            });

            const targetSection = document.getElementById(sectionId);
            if (targetSection) {
                targetSection.classList.add('active');
            }

            navItems.forEach(item => {
                item.classList.remove('active');
            });

            const activeNavItem = document.querySelector(`[href="#${sectionId}"]`).parentElement;
            if (activeNavItem) {
                activeNavItem.classList.add('active');
            }
        }

        navLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const sectionId = this.getAttribute('href').substring(1);
                switchSection(sectionId);
            });
        });

        switchSection('dashboard');
    }

    // Инициализация функций админ-панели
    initAddUserForm();
    initModalClose();
});


let currentArticleId = null;
function generateSlug(name) {
    return name
        .toLowerCase()
        .trim()
        .replace(/[^\w\s-]/g, '')
        .replace(/[\s_-]+/g, '-')
        .replace(/^-+|-+$/g, '');
}
document.getElementById('categoryName').addEventListener('input', function() {
    const name = this.value;
    const slugField = document.getElementById('categorySlug');
    if (!slugField.value || slugField.dataset.manual !== 'true') {
        slugField.value = generateSlug(name);
    }
});
document.getElementById('categorySlug').addEventListener('input', function() {
    this.dataset.manual = 'true';
});




// Открытие модального окна категории
function openCategoryModal(category = null) {
    const modal = document.getElementById('categoryModal');
    const form = document.getElementById('categoryForm');
    const title = document.getElementById('categoryModalTitle');
    
    form.reset();
    document.getElementById('categorySlug').dataset.manual = 'false';
    
    if (category) {
        title.textContent = 'Редактировать категорию';
        document.getElementById('categoryId').value = category.id;
        document.getElementById('categoryName').value = category.name;
        document.getElementById('categorySlug').value = category.slug;
        document.getElementById('categorySlug').dataset.manual = 'true';
        document.getElementById('categoryDescription').value = category.description || '';
    } else {
        title.textContent = 'Добавить категорию';
    }
    
    modal.style.display = 'block';
}

function closeCategoryModal() {
    document.getElementById('categoryModal').style.display = 'none';
}


async function deleteCategory(id) {
    if (!confirm('Вы уверены, что хотите удалить эту категорию?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/categories/' + id, {
            method: 'DELETE'
        });
        
        const result = await response.json();
        
        if (result.success) {
            location.reload(); // Перезагружаем страницу для обновления данных
        } else {
            alert('Ошибка: ' + (result.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Error deleting category:', error);
        alert('Ошибка сети');
    }
}
function showNotification(message, type = 'info') {
    // Реализация показа уведомлений
    console.log(`${type}: ${message}`);
}

document.getElementById('categoryForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const categoryData = {
        name: formData.get('name'),
        slug: formData.get('slug'),
        description: formData.get('description')
    };
    
    const categoryId = formData.get('id');
    if (categoryId) {
        categoryData.id = categoryId;
        updateCategory(categoryData);
    } else {
        createCategory(categoryData);
    }
});
async function updateCategory(categoryData) {
    try {
        const response = await fetch('/api/categories/' + categoryData.id, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(categoryData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            closeCategoryModal();
            location.reload(); // Перезагружаем страницу для обновления данных
        } else {
            alert('Ошибка: ' + (result.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Error updating category:', error);
        alert('Ошибка сети');
    }
}



//--------------------------------------------------------
async function createCategory(categoryData) {
    try {
        const response = await fetch('/api/categories', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(categoryData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            closeCategoryModal();
            location.reload(); // Перезагружаем страницу для обновления данных
        } else {
            alert('Ошибка: ' + (result.error || 'Неизвестная ошибка'));
        }
    } catch (error) {
        console.error('Error creating category:', error);
        alert('Ошибка сети');
    }
}
async function loadCategories() {
    try {
        const response = await fetch('../api/categories.php?action=get_all');
        const categories = await response.json();
        
        const tbody = document.querySelector('#categories tbody');
        tbody.innerHTML = '';
        
        categories.forEach(category => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${category.id}</td>
                <td>${escapeHtml(category.name)}</td>
                <td>${escapeHtml(category.description || '')}</td>
                <td>0</td> <!-- Количество статей -->
                <td>
                    <button class="btn-edit" onclick="openCategoryModal(${JSON.stringify(category).replace(/"/g, '&quot;')})">
                        Редактировать
                    </button>
                    <button class="btn-delete" onclick="deleteCategory(${category.id})">
                        Удалить
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading categories:', error);
    }
}
function escapeHtml(unsafe) {
    return unsafe
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}
function showNotification(message, type = 'info') {
    // Реализация показа уведомлений
    console.log(`${type}: ${message}`);
}
// Загрузка категорий при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    loadCategories();
});











function deleteUser(userId) {
    if (confirm('Вы уверены, что хотите деактивировать этого пользователя?')) {
        fetch(`/api/users/${userId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert('Пользователь успешно деактивирован!');
                location.reload();
            } else {
                alert('Ошибка: ' + data.error);
            }
        })
        .catch(error => {
            alert('Ошибка при деактивации пользователя');
        });
    }
}


// Функции для inline-редактирования пользователей
function startEditUser(userId) {
    // Скрываем кнопку редактирования и показываем кнопки сохранения/отмены
    document.getElementById(`editBtn_${userId}`).style.display = 'none';
    document.getElementById(`saveBtn_${userId}`).style.display = 'inline-block';
    document.getElementById(`cancelBtn_${userId}`).style.display = 'inline-block';
    
    // Переключаем режимы просмотра/редактирования
    document.querySelectorAll(`#userRow_${userId} .view-mode`).forEach(el => {
        el.style.display = 'none';
    });
    document.querySelectorAll(`#userRow_${userId} .edit-mode`).forEach(el => {
        el.style.display = 'inline-block';
    });
    
    // Подсвечиваем строку
    document.getElementById(`userRow_${userId}`).style.backgroundColor = '#fff3cd';
}

function cancelEditUser(userId) {
    // Показываем кнопку редактирования и скрываем кнопки сохранения/отмены
    document.getElementById(`editBtn_${userId}`).style.display = 'inline-block';
    document.getElementById(`saveBtn_${userId}`).style.display = 'none';
    document.getElementById(`cancelBtn_${userId}`).style.display = 'none';
    
    // Переключаем режимы редактирования/просмотра
    document.querySelectorAll(`#userRow_${userId} .edit-mode`).forEach(el => {
        el.style.display = 'none';
    });
    document.querySelectorAll(`#userRow_${userId} .view-mode`).forEach(el => {
        el.style.display = 'inline';
    });
    
    // Убираем подсветку
    document.getElementById(`userRow_${userId}`).style.backgroundColor = '';
}

function saveUser(userId) {
    const username = document.getElementById(`usernameEdit_${userId}`).value;
    const email = document.getElementById(`emailEdit_${userId}`).value;
    const role = document.getElementById(`roleEdit_${userId}`).value;
    const is_active = document.getElementById(`activeEdit_${userId}`).value;
    
    if (!username || !email) {
        alert('Имя пользователя и email обязательны для заполнения');
        return;
    }
    
    const formData = {
        username: username,
        email: email,
        role: role,
        is_active: parseInt(is_active)
    };

    fetch(`/api/users/${userId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Обновляем данные в режиме просмотра
            document.getElementById(`usernameView_${userId}`).textContent = username;
            document.getElementById(`emailView_${userId}`).textContent = email;
            document.getElementById(`roleView_${userId}`).textContent = role;
            document.getElementById(`roleView_${userId}`).className = `view-mode ${role === 'admin' ? 'role-admin' : 'role-user'}`;
            
            // Обновляем статус активности
            const activeText = is_active == 1 ? 'Активен' : 'Неактивен';
            const activeClass = is_active == 1 ? 'status-active' : 'status-inactive';
            document.getElementById(`activeView_${userId}`).textContent = activeText;
            document.getElementById(`activeView_${userId}`).className = activeClass;
            
            // Возвращаем к обычному режиму
            cancelEditUser(userId);
            
            //alert('Данные пользователя успешно обновлены!');
        } else {
            alert('Ошибка: ' + data.error);
            cancelEditUser(userId); // Отменяем редактирование при ошибке
        }
    })
    .catch(error => {
        alert('Ошибка при сохранении данных пользователя');
        cancelEditUser(userId); // Отменяем редактирование при ошибке
    });
}

// Закрытие модального окна при клике вне его
window.addEventListener('click', function(event) {
    const modal = document.getElementById('categoryModal');
    if (event.target === modal) {
        closeCategoryModal();
    }
});




// ----------------------------------------
// Функции для работы с модальным окном добавления пользователя
function openAddUserModal() {
    document.getElementById('addUserModal').style.display = 'block';
    clearErrors(); // Очищаем ошибки при открытии
}

function closeAddUserModal() {
    document.getElementById('addUserModal').style.display = 'none';
    document.getElementById('addUserForm').reset();
    clearErrors(); // Очищаем ошибки при закрытии
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
    }
}

// Функция для скрытия ошибки
function hideError(fieldId) {
    const errorElement = document.getElementById(fieldId + 'Error');
    if (errorElement) {
        errorElement.textContent = '';
        errorElement.style.display = 'none';
    }
}

// Валидация формы
function validateForm(formData) {
    let isValid = true;
    clearErrors();

    // Валидация имени пользователя
    if (!formData.username) {
        showError('username', 'Введите имя пользователя');
        isValid = false;
    } else if (formData.username.length < 3) {
        showError('username', 'Имя пользователя должно содержать минимум 3 символа');
        isValid = false;
    }

    // Валидация email
    if (!formData.email) {
        showError('email', 'Введите email');
        isValid = false;
    } else if (!isValidEmail(formData.email)) {
        showError('email', 'Введите корректный email адрес');
        isValid = false;
    }

    // Валидация пароля
    if (!formData.password) {
        showError('password', 'Введите пароль');
        isValid = false;
    } else if (formData.password.length < 6) {
        showError('password', 'Пароль должен содержать минимум 6 символов');
        isValid = false;
    }

    return isValid;
}

// Проверка email с помощью регулярного выражения
function isValidEmail(email) {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
}

// Обработчик формы добавления пользователя
function initAddUserForm() {
    const addUserForm = document.getElementById('addUserForm');
    if (addUserForm) {
        addUserForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                username: document.getElementById('newUserName').value.trim(),
                email: document.getElementById('newUserEmail').value.trim(),
                password: document.getElementById('newUserPassword').value,
                role: document.getElementById('newUserRole').value
            };

            // Валидация формы
            if (!validateForm(formData)) {
                return;
            }

            // Отправка данных на сервер
            fetch('/api/users', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    //alert('Пользователь успешно создан!');
                    closeAddUserModal();
                    location.reload();
                } else {
                    // Показываем ошибку от сервера
                    if (data.error.includes('email') || data.error.includes('email')) {
                        showError('email', data.error);
                    } else if (data.error.includes('имя') || data.error.includes('username')) {
                        showError('username', data.error);
                    } else {
                        alert('Ошибка: ' + data.error);
                    }
                }
            })
            .catch(error => {
                alert('Ошибка при создании пользователя');
            });
        });

        // Добавляем обработчики для скрытия ошибок при вводе
        document.getElementById('newUserName').addEventListener('input', function() {
            hideError('username');
        });

        document.getElementById('newUserEmail').addEventListener('input', function() {
            hideError('email');
        });

        document.getElementById('newUserPassword').addEventListener('input', function() {
            hideError('password');
        });
    }
}

// Закрытие модального окна при клике вне его
function initModalClose() {
    window.addEventListener('click', function(event) {
        const modal = document.getElementById('addUserModal');
        if (event.target === modal) {
            closeAddUserModal();
        }
    });
}







// Функции для работы с пользователями
function openUserModal(userId = null) {
    const modal = document.getElementById('userModal');
    const title = document.getElementById('userModalTitle');
    const form = document.getElementById('userForm');
    
    if (userId) {
        title.textContent = 'Редактировать пользователя';
        // Загружаем данные пользователя
        fetch(`/api/users/${userId}`)
            .then(response => response.json())
            .then(user => {
                document.getElementById('userId').value = user.id;
                document.getElementById('userName').value = user.user_name;
                document.getElementById('userEmail').value = user.email;
                document.getElementById('userRole').value = user.role;
                document.getElementById('userPassword').value = '';
            })
            .catch(error => {
                alert('Ошибка при загрузке данных пользователя');
            });
    } else {
        title.textContent = 'Добавить пользователя';
        form.reset();
        document.getElementById('userId').value = '';
    }
    
    modal.style.display = 'block';
}

function closeUserModal() {
    document.getElementById('userModal').style.display = 'none';
}

function deleteUser(userId) {
    if (confirm('Удалить этого пользователя?')) {
        fetch(`/api/users/${userId}`, {
            method: 'DELETE'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                //alert('Пользователь удален)');
                location.reload();
            } else {
                alert('Ошибка: ' + data.error);
            }
        })
        .catch(error => {
            alert('Ошибка удаления пользователя');
        });
    }
}

// Обработка формы пользователя
document.getElementById('userForm').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const formData = {
        username: document.getElementById('userName').value,
        email: document.getElementById('userEmail').value,
        password: document.getElementById('userPassword').value,
        role: document.getElementById('userRole').value
    };

    const userId = document.getElementById('userId').value;
    const method = userId ? 'PUT' : 'POST';
    const url = userId ? `/api/users/${userId}` : '/api/users';

    fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert('Пользователь успешно сохранен!');
            closeUserModal();
            location.reload();
        } else {
            alert('Ошибка: ' + data.error);
        }
    })
    .catch(error => {
        alert('Ошибка при сохранении пользователя');
    });
});

// Закрытие модального окна пользователя при клике вне его
window.addEventListener('click', function(event) {
    const modal = document.getElementById('userModal');
    if (event.target === modal) {
        closeUserModal();
    }
});







//-------------------------------------------------------------


// Функции для работы с формой категорий
function initCategoryForm() {
    const categoryForm = document.getElementById('categoryForm');
    if (categoryForm) {
        categoryForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = {
                name: document.getElementById('categoryName').value.trim(),
                description: document.getElementById('categoryDescription').value.trim()
            };

            // Валидация
            if (!formData.name) {
                alert('Введите название категории');
                return;
            }

            const categoryId = document.getElementById('categoryId').value;
            const method = categoryId ? 'PUT' : 'POST';
            const url = categoryId ? `/api/categories/${categoryId}` : '/api/categories';

            fetch(url, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(formData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Категория успешно сохранена!');
                    closeCategoryModal();
                    location.reload();
                } else {
                    alert('Ошибка: ' + data.error);
                }
            })
            .catch(error => {
                alert('Ошибка при сохранении категории');
            });
        });
    }
}

// Обнови функцию инициализации в DOMContentLoaded
document.addEventListener('DOMContentLoaded', function() {
    // Код для переключения разделов админ-панели
    const navLinks = document.querySelectorAll('.nav-link');
    const contentSections = document.querySelectorAll('.content-section');
    const navItems = document.querySelectorAll('.nav-item');

    // Проверяем, что мы в админ-панели
    if (contentSections.length > 0) {
        function switchSection(sectionId) {
            contentSections.forEach(section => {
                section.classList.remove('active');
            });

            const targetSection = document.getElementById(sectionId);
            if (targetSection) {
                targetSection.classList.add('active');
            }

            navItems.forEach(item => {
                item.classList.remove('active');
            });

            const activeNavItem = document.querySelector(`[href="#${sectionId}"]`).parentElement;
            if (activeNavItem) {
                activeNavItem.classList.add('active');
            }
        }

        navLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const sectionId = this.getAttribute('href').substring(1);
                switchSection(sectionId);
            });
        });

        switchSection('dashboard');
    }

    // Инициализация функций админ-панели
    initCategoryForm(); // ДОБАВЬ ЭТУ СТРОЧКУ
    initAddUserForm();
    initModalClose();
});



function debug(message) {
    console.log('[DEBUG] ' + message);
}

// Проверяем, загружены ли необходимые элементы
function checkModalElements() {
    const modal = document.getElementById('articleModal');
    const form = document.getElementById('articleForm');
    const title = document.getElementById('articleModalTitle');
    
    if (!modal) {
        console.error('Modal element not found');
        return false;
    }
    if (!form) {
        console.error('Form element not found');
        return false;
    }
    if (!title) {
        console.error('Modal title element not found');
        return false;
    }
    
    return true;
}

function openArticleModal(articleData = null) {
    debug('openArticleModal called with data: ' + JSON.stringify(articleData));
    
    // Проверяем элементы
    if (!checkModalElements()) {
        alert('Ошибка: не найдены необходимые элементы модального окна');
        return;
    }
    
    const modal = document.getElementById('articleModal');
    const form = document.getElementById('articleForm');
    const title = document.getElementById('articleModalTitle');
    
    if (articleData) {
        // Режим редактирования
        debug('Editing mode for article: ' + articleData.id);
        title.textContent = 'Редактировать статью';
        currentArticleId = articleData.id;
        
        // Заполняем форму данными
        document.getElementById('articleId').value = articleData.id || '';
        document.getElementById('articleTitle').value = articleData.title || '';
        document.getElementById('articleSlug').value = articleData.slug || '';
        document.getElementById('articleContent').value = articleData.content || '';
        document.getElementById('articleExcerpt').value = articleData.excerpt || '';
        document.getElementById('articleCategory').value = articleData.category_id || '';
        document.getElementById('articleStatus').value = articleData.status || 'draft';
        document.getElementById('articleFeaturedImage').value = articleData.featured_image || '';
    } else {
        // Режим создания
        debug('Creating new article');
        title.textContent = 'Создать статью';
        currentArticleId = null;
        form.reset();
        // Устанавливаем значения по умолчанию
        document.getElementById('articleStatus').value = 'draft';
    }
    
    // Показываем модальное окно
    modal.style.display = 'flex';
    debug('Modal displayed');
}


function closeArticleModal() {
    debug('closeArticleModal called');
    const modal = document.getElementById('articleModal');
    if (modal) {
        modal.style.display = 'none';
    }
    currentArticleId = null;
}

// Обработка отправки формы
document.getElementById('articleForm').addEventListener('submit', function(e) {
    e.preventDefault();
    saveArticle();
});

function saveArticle() {
    const formData = new FormData();
    const articleId = document.getElementById('articleId').value;
    
    // Собираем данные формы
    const articleData = {
        title: document.getElementById('articleTitle').value,
        slug: document.getElementById('articleSlug').value,
        content: document.getElementById('articleContent').value,
        excerpt: document.getElementById('articleExcerpt').value,
        category_id: document.getElementById('articleCategory').value,
        status: document.getElementById('articleStatus').value,
        featured_image: document.getElementById('articleFeaturedImage').value
    };
    
    // Добавляем файл изображения если есть
    const imageFile = document.getElementById('articleImageFile').files[0];
    if (imageFile) {
        formData.append('featured_image_file', imageFile);
    }
    
    // Добавляем остальные данные
    for (const key in articleData) {
        formData.append(key, articleData[key]);
    }
    
    const url = currentArticleId ? `/api/articles/${currentArticleId}` : '/api/articles';
    const method = currentArticleId ? 'PUT' : 'POST';
    
    // Показываем индикатор загрузки
    const submitBtn = document.querySelector('#articleForm button[type="submit"]');
    const originalText = submitBtn.textContent;
    submitBtn.textContent = 'Сохранение...';
    submitBtn.disabled = true;
    
    fetch(url, {
        method: method,
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            closeArticleModal();
            location.reload();
        } else {
            alert('Ошибка при сохранении: ' + data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при сохранении статьи');
    })
    .finally(() => {
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    });
}

function deleteArticle(articleId) {
    if (confirm('Вы уверены, что хотите удалить эту статью?')) {
        fetch(`/api/articles/${articleId}`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Ошибка при удалении статьи: ' + data.error);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка при удалении статьи');
        });
    }
}

// Автогенерация slug из заголовка
document.getElementById('articleTitle').addEventListener('input', function() {
    const slugField = document.getElementById('articleSlug');
    if (!slugField.value) {
        const slug = generateSlug(this.value);
        slugField.value = slug;
    }
});

function generateSlug(text) {
    return text
        .toLowerCase()
        .replace(/[^\w\u0400-\u04FF]+/g, '-')
        .replace(/^-+|-+$/g, '')
        .substring(0, 100);
}

// Закрытие модального окна при клике вне его
window.addEventListener('click', function(event) {
    const modal = document.getElementById('articleModal');
    if (event.target === modal) {
        closeArticleModal();
    }
});

document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('articleForm');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            saveArticle();
        });
        debug('Form submit listener attached');
    } else {
        console.error('Article form not found');
    }
});

















// Функции для редактирования статуса статьи
function startEditArticle(articleId) {
    // Скрыть кнопку редактирования
    document.getElementById(`editArticleBtn_${articleId}`).style.display = 'none';
    
    // Показать кнопки сохранения и отмены
    document.getElementById(`saveArticleBtn_${articleId}`).style.display = 'inline-block';
    document.getElementById(`cancelArticleBtn_${articleId}`).style.display = 'inline-block';
    
    // Переключить режим отображения статуса
    document.getElementById(`statusView_${articleId}`).style.display = 'none';
    document.getElementById(`statusEdit_${articleId}`).style.display = 'inline-block';
}

function cancelEditArticle(articleId) {
    // Показать кнопку редактирования
    document.getElementById(`editArticleBtn_${articleId}`).style.display = 'inline-block';
    
    // Скрыть кнопки сохранения и отмены
    document.getElementById(`saveArticleBtn_${articleId}`).style.display = 'none';
    document.getElementById(`cancelArticleBtn_${articleId}`).style.display = 'none';
    
    // Переключить режим отображения статуса
    document.getElementById(`statusView_${articleId}`).style.display = 'inline-block';
    document.getElementById(`statusEdit_${articleId}`).style.display = 'none';
}

function saveArticleStatus(articleId) {
    const newStatus = document.getElementById(`statusEdit_${articleId}`).value;
    
    fetch('/api/update_article_status', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            article_id: articleId,
            status: newStatus
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Обновляем отображение статуса
            const statusView = document.getElementById(`statusView_${articleId}`);
            const statusText = newStatus === 'published' ? 'Опубликовано' : 'Черновик';
            const statusClass = newStatus === 'published' ? 'status-published' : 'status-draft';
            
            statusView.textContent = statusText;
            statusView.className = `view-mode ${statusClass}`;
            
            // Выходим из режима редактирования
            cancelEditArticle(articleId);
            
            alert('Статус статьи успешно обновлен!');
        } else {
            alert('Ошибка при обновлении статуса: ' + (data.error || 'Неизвестная ошибка'));
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Ошибка при обновлении статуса статьи');
    });
}