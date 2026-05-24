let API = 'http://localhost:8000';
if (window.location.hostname.includes('onrender.com') || window.location.port === '8000') { API = ''; }
let currentUser = null;
let allResults = [];
let userFavorites = [];

// ── Auth Guard ────────────────────────────────────────
(function() {
    try {
        const saved = localStorage.getItem('pagespark_user');
        if (!saved) {
            window.location.href = 'index.html';
            return;
        }
        currentUser = JSON.parse(saved);
    } catch (e) {
        console.error("Auth Guard Error:", e);
        localStorage.removeItem('pagespark_user');
        window.location.href = 'index.html';
    }
})();

document.addEventListener('DOMContentLoaded', () => {
    // Hiển thị lời chào
    const greet = document.getElementById('nav-greeting');
    if (greet && currentUser) greet.textContent = `Hi, ${currentUser.username}`;

    // Load user favorites and stats immediately on load
    fetchFavoritesAndStats();

    const searchBtn = document.getElementById('search-btn'); // Nút này giờ là type="button"
    const textarea = document.getElementById('description');
    const charCounter = document.getElementById('char-counter');
    const topNInput = document.getElementById('top_n');
    const topNDisplay = document.getElementById('top-n-display');
    const minRatingInput = document.getElementById('min-rating');
    const ratingDisplay = document.getElementById('rating-display');
    const genreSelect = document.getElementById('genre-filter');
    const sortSelect = document.getElementById('sort-select');
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('error-message');
    const errorText = document.getElementById('error-text');
    const resultsGrid = document.getElementById('results-grid');
    const resultsHeader = document.getElementById('results-header');
    const resultsCount = document.getElementById('results-count');
    const resultsQuery = document.getElementById('results-query');
    const emptyState = document.getElementById('empty-state');
    const modal = document.getElementById('book-modal');
    const modalContent = document.getElementById('modal-content');

    // Load danh mục
    fetch(`${API}/categories`).then(r => r.json()).then(d => {
        if (d.categories) d.categories.forEach(c => {
            const o = document.createElement('option'); o.value = c; o.textContent = c;
            genreSelect.appendChild(o);
        });
    }).catch(err => console.error(err));

    // Logout
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', (e) => {
            e.preventDefault();
            localStorage.removeItem('pagespark_user');
            window.location.href = 'index.html';
        });
    }

    // Slider & Char counter
    textarea.addEventListener('input', () => { charCounter.textContent = textarea.value.length; });
    topNInput.addEventListener('input', e => { topNDisplay.textContent = e.target.value; });
    minRatingInput.addEventListener('input', e => {
        const v = parseFloat(e.target.value);
        ratingDisplay.textContent = v === 0 ? 'Any' : v + '★';
    });

    // Listen for sort changes
    if (sortSelect) {
        sortSelect.addEventListener('change', () => {
            if (allResults.length > 0) {
                renderResults(sortBooks([...allResults]));
            }
        });
    }

    // Nút Clear
    const clearBtn = document.getElementById('clear-btn');
    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            textarea.value = '';
            charCounter.textContent = '0';
            genreSelect.value = '';
            minRatingInput.value = '0';
            ratingDisplay.textContent = 'Any';
            topNInput.value = '5';
            topNDisplay.textContent = '5';
            resultsGrid.innerHTML = '';
            resultsHeader.classList.add('hidden');
            emptyState.classList.remove('hidden');
            textarea.focus();
        });
    }

    // Example chips
    document.querySelectorAll('.example-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            textarea.value = chip.dataset.text;
            charCounter.textContent = textarea.value.length;
            startSearch();
        });
    });

    // Close Modal
    const modalClose = document.getElementById('modal-close');
    if (modalClose) modalClose.addEventListener('click', closeModal);
    window.addEventListener('click', (e) => { if (e.target === modal) closeModal(); });

    // Close Error
    const errorClose = document.getElementById('error-close');
    if (errorClose) {
        errorClose.addEventListener('click', () => errorEl.classList.add('hidden'));
    }


    // Xử lý tìm kiếm qua Form Submit (Cả khi nhấn nút và nhấn Enter)
    const searchForm = document.getElementById('search-form');
    if (searchForm) {
        searchForm.addEventListener('submit', (e) => {
            e.preventDefault();
            e.stopPropagation();
            startSearch();
        });
    }

    let isSearching = false;
    async function startSearch() {
        if (isSearching) return;
        const desc = textarea.value.trim();

        isSearching = true;

        // Reset UI
        loadingEl.classList.remove('hidden');
        errorEl.classList.add('hidden');
        emptyState.classList.add('hidden');
        resultsHeader.classList.add('hidden');
        resultsGrid.innerHTML = '';
        searchBtn.disabled = true;

        try {
            const body = {
                description: desc,
                top_n: parseInt(topNInput.value) || 5,
                genre_filter: genreSelect.value || null,
                min_rating: parseFloat(minRatingInput.value) || null,
                user_id: currentUser ? currentUser.id : null
            };

            const res = await fetch(`${API}/recommend`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });

            if (!res.ok) {
                if (res.status === 401 || res.status === 403) {
                    // Nếu lỗi auth, mới chuyển về login
                    localStorage.removeItem('pagespark_user');
                    window.location.href = 'index.html';
                    return;
                }
                throw new Error('Server returned an error');
            }
            const data = await res.json();
            
            allResults = data.recommendations || [];
            
            // Hiển thị kết quả
            resultsCount.textContent = `${allResults.length} book${allResults.length !== 1 ? 's' : ''} found`;
            resultsQuery.textContent = desc ? `for "${desc.slice(0, 40)}..."` : `by filters`;
            resultsHeader.classList.remove('hidden');

            renderResults(sortBooks([...allResults]));

            if (allResults.length === 0) {
                emptyState.classList.remove('hidden');
            }

        } catch (err) {
            errorText.textContent = err.message;
            errorEl.classList.remove('hidden');
        } finally {
            loadingEl.classList.add('hidden');
            searchBtn.disabled = false;
            isSearching = false;
        }
    }

    function renderResults(books) {
        resultsGrid.innerHTML = '';
        books.forEach((book, i) => {
            const genres = Array.isArray(book.genres) ? book.genres : [];
            const card = document.createElement('article');
            card.className = 'book-card';
            card.style.animationDelay = `${i * 0.05}s`;
            
            // Link Goodreads - xử lý nếu link là # để không bị nhảy trang
            const bookUrl = (book.url && book.url !== '#') ? book.url : 'javascript:void(0)';

            const isFav = userFavorites.some(f => f.book_title === book.title);

            // Compute hash index for consistent gorgeous gradient covers
            const hash = Array.from(book.title || '').reduce((acc, char) => acc + char.charCodeAt(0), 0);
            const gradIndex = hash % 6;

            card.innerHTML = `
                <div class="book-cover-container">
                    <div class="book-cover-placeholder cover-grad-${gradIndex}">
                        <div class="cover-spine"></div>
                        <div class="cover-title-text">${esc(book.title)}</div>
                        <div class="cover-author-text">${esc(book.author)}</div>
                    </div>
                    <img class="book-cover-img hidden" alt="${esc(book.title)} cover">
                </div>
                <div class="book-info-container">
                    <div class="book-header">
                        <div class="book-header-text">
                            <h3 class="book-title" title="${esc(book.title)}">${esc(book.title)}</h3>
                            <p class="book-author">by ${esc(book.author)}</p>
                        </div>
                        <div class="book-rating"><i data-lucide="star"></i><span>${book.rating || 'N/A'}</span></div>
                    </div>
                    <p class="book-description">${esc(book.description)}</p>
                    <div class="book-genres">
                        ${genres.slice(0,2).map(g => `<span class="genre-tag">${esc(g.trim())}</span>`).join('')}
                    </div>
                    <div class="book-footer">
                        <span class="score-badge">Match ${Math.round(book.score*100)}%</span>
                        <a href="${bookUrl}" target="${bookUrl.startsWith('http') ? '_blank' : '_self'}" class="view-link" onclick="event.stopPropagation()">
                            Goodreads <i data-lucide="external-link"></i>
                        </a>
                    </div>
                </div>`;
            
            // Add Heart/Favorite Button
            const heartBtn = document.createElement('button');
            heartBtn.className = `btn-fav ${isFav ? 'active' : ''}`;
            heartBtn.innerHTML = `<i data-lucide="heart" style="width:16px; height:16px; ${isFav ? 'fill:#ef4444' : ''}"></i>`;
            heartBtn.addEventListener('click', (e) => {
                e.stopPropagation();
                toggleFavorite(book, heartBtn);
            });
            card.appendChild(heartBtn);
            
            card.addEventListener('click', () => openModal(book));
            resultsGrid.appendChild(card);

            // Fetch cover asynchronously (passing database image_url if available)
            loadBookCover(book.title, book.author, card.querySelector('.book-cover-container'), book.image_url);
        });
        if (window.lucide) lucide.createIcons();
    }

    async function loadBookCover(title, author, container, dbImageUrl) {
        if (!container) return;
        const img = container.querySelector('.book-cover-img');
        const placeholder = container.querySelector('.book-cover-placeholder');
        
        // 1. If database has a direct cover image URL, use it immediately!
        if (dbImageUrl && dbImageUrl.trim() && dbImageUrl !== 'nan' && dbImageUrl !== 'None') {
            img.src = dbImageUrl;
            img.onload = () => {
                img.classList.remove('hidden');
                if (placeholder) placeholder.classList.add('hidden');
            };
            img.onerror = () => {
                // If it fails (e.g. broken or blocked link), try fallback fetch APIs
                fetchFallbackCovers(title, author, container);
            };
            return;
        }

        // Otherwise, query cover APIs directly
        fetchFallbackCovers(title, author, container);
    }

    async function fetchFallbackCovers(title, author, container) {
        const cleanTitle = String(title || '').replace(/[\(\[].*?[\)\]]/g, '').trim();
        const cleanAuthor = String(author || '').trim();
        const cacheKey = `cover_${cleanTitle}_${cleanAuthor}`;
        const cachedUrl = sessionStorage.getItem(cacheKey);
        
        const img = container.querySelector('.book-cover-img');
        const placeholder = container.querySelector('.book-cover-placeholder');

        if (cachedUrl) {
            if (cachedUrl === 'none') return;
            img.src = cachedUrl;
            img.onload = () => {
                img.classList.remove('hidden');
                if (placeholder) placeholder.classList.add('hidden');
            };
            return;
        }

        // 1. Try Open Library Search API first (Free, CORS enabled, Zero rate-limiting)
        try {
            const olRes = await fetch(`https://openlibrary.org/search.json?title=${encodeURIComponent(cleanTitle)}&author=${encodeURIComponent(cleanAuthor)}&limit=1`);
            if (olRes.ok) {
                const olData = await olRes.json();
                if (olData.docs && olData.docs[0]) {
                    const coverId = olData.docs[0].cover_i;
                    if (coverId) {
                        const coverUrl = `https://covers.openlibrary.org/b/id/${coverId}-M.jpg`;
                        sessionStorage.setItem(cacheKey, coverUrl);
                        img.src = coverUrl;
                        img.onload = () => {
                            img.classList.remove('hidden');
                            if (placeholder) placeholder.classList.add('hidden');
                        };
                        return;
                    }
                }
            }
        } catch (e) {
            console.warn("Open Library Cover search fallback triggered:", e);
        }

        // 2. Try Google Books API as solid fallback
        try {
            const query = `${cleanTitle} ${cleanAuthor}`;
            const res = await fetch(`https://www.googleapis.com/books/v1/volumes?q=${encodeURIComponent(query)}&maxResults=1`);
            if (res.ok) {
                const data = await res.json();
                if (data.items && data.items[0]) {
                    const volumeInfo = data.items[0].volumeInfo;
                    const thumbnail = volumeInfo.imageLinks?.thumbnail || volumeInfo.imageLinks?.smallThumbnail;
                    if (thumbnail) {
                        const secureUrl = thumbnail.replace('http://', 'https://');
                        sessionStorage.setItem(cacheKey, secureUrl);
                        img.src = secureUrl;
                        img.onload = () => {
                            img.classList.remove('hidden');
                            if (placeholder) placeholder.classList.add('hidden');
                        };
                        return;
                    }
                }
            }
        } catch (e) {
            console.warn("Google Books Cover search fallback error:", e);
        }

        sessionStorage.setItem(cacheKey, 'none');
    }

    function openModal(book) {
        const genres = Array.isArray(book.genres) ? book.genres : [];
        const bookUrl = (book.url && book.url !== '#') ? book.url : 'javascript:void(0)';
        
        // Compute hash index for consistency in modal too
        const hash = Array.from(book.title || '').reduce((acc, char) => acc + char.charCodeAt(0), 0);
        const gradIndex = hash % 6;

        modalContent.innerHTML = `
            <div class="modal-genre-strip"></div>
            <div class="modal-body-layout">
                <div class="modal-cover-container">
                    <div class="modal-cover-placeholder cover-grad-${gradIndex}">
                        <div class="cover-spine" style="width:12px;"></div>
                        <div class="cover-title-text" style="font-size:0.85rem; padding: 0 0.8rem 0 1rem; -webkit-line-clamp: 5;">${esc(book.title)}</div>
                        <div class="cover-author-text" style="font-size:0.65rem; padding-left: 1rem;">by ${esc(book.author)}</div>
                    </div>
                    <img class="modal-cover-img hidden" alt="${esc(book.title)} cover">
                </div>
                <div class="modal-info-container">
                    <h2 class="modal-title">${esc(book.title)}</h2>
                    <p class="modal-author">by ${esc(book.author)}</p>
                    <div class="modal-rating"><i data-lucide="star"></i><span>${book.rating || 'N/A'} / 5.0</span></div>
                    <p class="modal-desc">${esc(book.description)}</p>
                    <div class="modal-genres">${genres.map(g => `<span class="genre-tag">${esc(g.trim())}</span>`).join('')}</div>
                    <a href="${bookUrl}" target="${bookUrl.startsWith('http') ? '_blank' : '_self'}" class="modal-link">
                        <i data-lucide="book-open"></i> View on Goodreads
                    </a>
                </div>
            </div>`;
        
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        
        // Fetch large cover in modal (passing database image_url if available)
        loadBookCover(book.title, book.author, modalContent.querySelector('.modal-cover-container'), book.image_url);
        
        if (window.lucide) lucide.createIcons();
    }

    function closeModal() {
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    }

    function sortBooks(books) {
        const by = sortSelect.value;
        if (by === 'rating') {
            return books.sort((a, b) => (Number(b.rating) || 0) - (Number(a.rating) || 0));
        }
        if (by === 'title') {
            return books.sort((a, b) => String(a.title || '').localeCompare(String(b.title || '')));
        }
        return books.sort((a, b) => (Number(b.score) || 0) - (Number(a.score) || 0));
    }

    // Favorites & Library helper functions
    async function toggleFavorite(book, btn) {
        if (!currentUser) return alert('Vui lòng đăng nhập để lưu sách yêu thích!');
        const isFav = btn.classList.contains('active');
        
        try {
            if (isFav) {
                const favItem = userFavorites.find(f => f.book_title === book.title);
                if (favItem) {
                    const res = await fetch(`${API}/favorites/${favItem.id}`, {
                        method: 'DELETE'
                    });
                    if (!res.ok) throw new Error('Không thể xóa sách khỏi danh sách yêu thích');
                    
                    userFavorites = userFavorites.filter(f => f.id !== favItem.id);
                    btn.classList.remove('active');
                }
            } else {
                const res = await fetch(`${API}/favorites`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        user_id: currentUser.id,
                        book_title: book.title,
                        book_author: book.author || null,
                        book_url: book.url || null,
                        book_rating: parseFloat(book.rating) || null
                    })
                });
                if (!res.ok) throw new Error('Không thể thêm sách vào danh sách yêu thích');
                const data = await res.json();
                
                userFavorites.push({
                    id: data.favorite_id,
                    book_title: book.title,
                    book_author: book.author,
                    book_url: book.url,
                    book_rating: book.rating
                });
                btn.classList.add('active');
            }
            updateLibraryStats();
        } catch (err) {
            alert(err.message);
        }
    }

    window.openLibraryModal = async function() {
        if (!currentUser) return;
        const modal = document.getElementById('library-modal');
        modal.classList.remove('hidden');
        document.body.style.overflow = 'hidden';
        await fetchFavoritesAndStats();
    };

    window.closeLibraryModal = function() {
        const modal = document.getElementById('library-modal');
        modal.classList.add('hidden');
        document.body.style.overflow = '';
    };

    async function fetchFavoritesAndStats() {
        if (!currentUser) return;
        try {
            // Fetch stats
            const statsRes = await fetch(`${API}/users/${currentUser.id}/stats`);
            if (statsRes.ok) {
                const stats = await statsRes.json();
                document.getElementById('user-stat-searches').textContent = stats.search_count;
                document.getElementById('user-stat-favorites').textContent = stats.favorite_count;
            }

            // Fetch favorites
            const favRes = await fetch(`${API}/favorites/${currentUser.id}`);
            if (favRes.ok) {
                const data = await favRes.json();
                userFavorites = data.favorites || [];
                renderFavoritesList();
            }
        } catch (err) {
            console.error("Error fetching library data:", err);
        }
    }

    function renderFavoritesList() {
        const container = document.getElementById('favorites-list-container');
        container.innerHTML = '';
        
        if (userFavorites.length === 0) {
            container.innerHTML = `<div style="text-align: center; color: var(--text-muted); padding: 2rem 0;">No books saved yet. Click the heart icon on book cards to save them!</div>`;
            return;
        }

        userFavorites.forEach(f => {
            const item = document.createElement('div');
            item.className = 'fav-item';
            
            const bookUrl = (f.book_url && f.book_url !== '#') ? f.book_url : 'javascript:void(0)';
            
            item.innerHTML = `
                <div>
                    <div class="fav-title">${esc(f.book_title)}</div>
                    <div class="fav-meta">by ${esc(f.book_author || 'Unknown')} • ★ ${f.book_rating || 'N/A'}</div>
                </div>
                <div style="display: flex; gap: 0.75rem; align-items: center;">
                    <a href="${bookUrl}" target="${bookUrl.startsWith('http') ? '_blank' : '_self'}" class="view-link" style="font-size: 0.75rem; padding: 0.25rem 0.5rem; display: flex; align-items: center; gap: 0.25rem;">
                        View <i data-lucide="external-link" style="width:12px; height:12px;"></i>
                    </a>
                    <button class="btn-ghost" onclick="removeFavoriteFromList(${f.id})" style="color: #ef4444; padding: 0.25rem; border-radius: 4px;" title="Xóa khỏi danh sách"><i data-lucide="trash-2" style="width:16px; height:16px;"></i></button>
                </div>
            `;
            container.appendChild(item);
        });
        if (window.lucide) lucide.createIcons();
    }

    window.removeFavoriteFromList = async function(favId) {
        if (confirm("Bạn có chắc chắn muốn xóa cuốn sách này khỏi danh sách yêu thích?")) {
            try {
                const res = await fetch(`${API}/favorites/${favId}`, {
                    method: 'DELETE'
                });
                if (!res.ok) throw new Error('Không thể xóa sách');
                
                userFavorites = userFavorites.filter(f => f.id !== favId);
                renderFavoritesList();
                
                // Update stats counter
                document.getElementById('user-stat-favorites').textContent = userFavorites.length;
                
                // Re-render search results if they are visible to update heart state
                if (allResults.length > 0) {
                    renderResults(sortBooks([...allResults]));
                }
            } catch (err) {
                alert(err.message);
            }
        }
    };

    function updateLibraryStats() {
        const statsFavCount = document.getElementById('user-stat-favorites');
        if (statsFavCount) {
            statsFavCount.textContent = userFavorites.length;
        }
        renderFavoritesList();
    }

    function esc(s) {
        if (!s) return '';
        return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }
});
