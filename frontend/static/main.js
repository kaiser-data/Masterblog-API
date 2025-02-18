let currentPage = 1;
let currentSortField = null;
let currentSortDirection = "asc";

// Load posts from the API
function loadPosts(page) {
    currentPage = page;
    const baseUrl = document.getElementById('api-base-url').value;
    let url = `${baseUrl}/posts?page=${page}&per_page=5`;
    if (currentSortField) {
        url += `&sort=${currentSortField}&direction=${currentSortDirection}`;
    }

    fetch(url)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            const postContainer = document.getElementById('post-container');
            postContainer.innerHTML = ''; // Clear previous posts

            data.posts.forEach(post => {
                const postDiv = document.createElement('div');
                postDiv.className = 'post';
                postDiv.innerHTML = `
                    <h2>${post.title}</h2>
                    <p><strong>Author:</strong> ${post.author}</p>
                    <p><strong>Date:</strong> ${post.date}</p>
                    <p>${post.content}</p>
                    <button onclick="deletePost(${post.id})">Delete</button>
                    <button onclick="populateFormForUpdate(${post.id})">Edit</button>
                `;
                postContainer.appendChild(postDiv);
            });

            updatePaginationControls(data.page, data.total_pages);
        })
        .catch(error => console.error('Error:', error));
}

// Update pagination controls
function updatePaginationControls(currentPage, totalPages) {
    const paginationContainer = document.getElementById('pagination-container');
    paginationContainer.innerHTML = '';

    for (let i = 1; i <= totalPages; i++) {
        const button = document.createElement('button');
        button.innerText = i;
        button.disabled = i === currentPage;
        button.onclick = () => loadPosts(i);
        paginationContainer.appendChild(button);
    }
}

// Toggle sorting
function toggleSort(field) {
    if (currentSortField === field) {
        currentSortDirection = currentSortDirection === "asc" ? "desc" : "asc";
    } else {
        currentSortField = field;
        currentSortDirection = "asc";
    }
    loadPosts(currentPage);
}

// Delete a post
function deletePost(postId) {
    const baseUrl = document.getElementById('api-base-url').value;
    fetch(`${baseUrl}/posts/${postId}`, { method: 'DELETE' })
        .then(response => response.json())
        .then(() => loadPosts(currentPage))
        .catch(error => console.error('Error:', error));
}

// Populate form for updating a post
function populateFormForUpdate(postId) {
    const baseUrl = document.getElementById('api-base-url').value;

    fetch(`${baseUrl}/posts/${postId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error('Post not found');
            }
            return response.json();
        })
        .then(post => {
            document.getElementById('post-id').value = post.id || '';
            document.getElementById('post-title').value = post.title || '';
            document.getElementById('post-content').value = post.content || '';
            document.getElementById('post-author').value = post.author || '';
            document.getElementById('post-date').value = post.date || '';
        })
        .catch(error => {
            console.error('Error fetching post:', error);
            alert('Failed to load post details. Please try again.');
        });
}

// Add or update a post
function addOrUpdatePost() {
    const baseUrl = document.getElementById('api-base-url').value;
    const postId = document.getElementById('post-id').value;
    const title = document.getElementById('post-title').value.trim();
    const content = document.getElementById('post-content').value.trim();
    const author = document.getElementById('post-author').value.trim();
    const date = document.getElementById('post-date').value.trim();

    if (!title || !content || !author || !date) {
        alert('All fields are required.');
        return;
    }

    const url = postId ? `${baseUrl}/posts/${postId}` : `${baseUrl}/posts`;
    const method = postId ? 'PUT' : 'POST';
    const body = JSON.stringify({ title, content, author, date });

    fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body })
        .then(response => response.json())
        .then(() => {
            loadPosts(currentPage); // Reload posts after adding/updating
            clearForm(); // Clear the form fields
        })
        .catch(error => console.error('Error:', error));
}

// Clear the form
function clearForm() {
    document.getElementById('post-id').value = '';
    document.getElementById('post-title').value = '';
    document.getElementById('post-content').value = '';
    document.getElementById('post-author').value = '';
    document.getElementById('post-date').value = '';
}