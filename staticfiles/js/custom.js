// Custom JavaScript for Church Management System

$(document).ready(function() {
    // Initialize tooltips
    $('[data-bs-toggle="tooltip"]').tooltip();
    
    // Initialize popovers
    $('[data-bs-toggle="popover"]').popover();
    
    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        $('.alert').alert('close');
    }, 5000);
    
    // Confirm before deleting
    $('.confirm-delete').on('click', function() {
        return confirm('Are you sure you want to delete this? This action cannot be undone.');
    });
    
    // Form validation
    $('.needs-validation').on('submit', function(event) {
        if (!this.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
        }
        $(this).addClass('was-validated');
    });
    
    // Image preview for file inputs
    $('.image-preview-input').on('change', function() {
        const input = this;
        const preview = $(this).data('preview');
        
        if (input.files && input.files[0]) {
            const reader = new FileReader();
            
            reader.onload = function(e) {
                $(preview).attr('src', e.target.result);
                $(preview).show();
            }
            
            reader.readAsDataURL(input.files[0]);
        }
    });
    
    // AJAX search
    let searchTimeout;
    $('.ajax-search').on('input', function() {
        clearTimeout(searchTimeout);
        const query = $(this).val().trim();
        const url = $(this).data('url');
        
        if (query.length < 2) {
            $('.search-results').hide();
            return;
        }
        
        searchTimeout = setTimeout(function() {
            $.ajax({
                url: url,
                data: { q: query },
                success: function(data) {
                    // Handle search results
                    console.log('Search results:', data);
                },
                error: function(xhr, status, error) {
                    console.error('Search error:', error);
                }
            });
        }, 300);
    });
    
    // Toggle password visibility
    $('.toggle-password').on('click', function() {
        const input = $(this).siblings('input');
        const icon = $(this).find('i');
        
        if (input.attr('type') === 'password') {
            input.attr('type', 'text');
            icon.removeClass('fa-eye').addClass('fa-eye-slash');
        } else {
            input.attr('type', 'password');
            icon.removeClass('fa-eye-slash').addClass('fa-eye');
        }
    });
    
    // Copy to clipboard
    $('.copy-to-clipboard').on('click', function() {
        const text = $(this).data('text');
        navigator.clipboard.writeText(text).then(function() {
            // Show success message
            alert('Copied to clipboard!');
        });
    });
    
    // Character counter for textareas
    $('.char-counter').each(function() {
        const textarea = $(this);
        const counter = $('<small class="text-muted float-end"></small>');
        textarea.after(counter);
        
        function updateCounter() {
            const length = textarea.val().length;
            const max = textarea.attr('maxlength') || 1000;
            counter.text(`${length}/${max}`);
            
            if (length > max * 0.9) {
                counter.addClass('text-warning');
            } else {
                counter.removeClass('text-warning');
            }
        }
        
        textarea.on('input', updateCounter);
        updateCounter();
    });
    
    // Date picker initialization
    if ($.fn.datepicker) {
        $('.datepicker').datepicker({
            format: 'yyyy-mm-dd',
            autoclose: true,
            todayHighlight: true
        });
    }
    
    // Select2 initialization
    if ($.fn.select2) {
        $('.select2').select2({
            theme: 'bootstrap-5'
        });
    }
    
    // DataTable initialization
    if ($.fn.DataTable) {
        $('.datatable').DataTable({
            pageLength: 25,
            responsive: true,
            order: [[0, 'desc']]
        });
    }
    
    // Smooth scrolling for anchor links
    $('a[href^="#"]').on('click', function(e) {
        e.preventDefault();
        const target = $(this.getAttribute('href'));
        if (target.length) {
            $('html, body').stop().animate({
                scrollTop: target.offset().top - 70
            }, 1000);
        }
    });
    
    // Back to top button
    $(window).on('scroll', function() {
        if ($(this).scrollTop() > 300) {
            $('.back-to-top').fadeIn();
        } else {
            $('.back-to-top').fadeOut();
        }
    });
    
    $('.back-to-top').on('click', function() {
        $('html, body').animate({ scrollTop: 0 }, 800);
        return false;
    });
});

// Utility functions
function formatPhoneNumber(phone) {
    if (!phone) return '';
    const cleaned = phone.replace(/\D/g, '');
    const match = cleaned.match(/^(\d{3})(\d{3})(\d{4})$/);
    if (match) {
        return '(' + match[1] + ') ' + match[2] + '-' + match[3];
    }
    return phone;
}

function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function showLoading() {
    $('#loading-spinner').show();
}

function hideLoading() {
    $('#loading-spinner').hide();
}

function showToast(message, type = 'success') {
    // Create toast container if it doesn't exist
    if (!$('#toast-container').length) {
        $('body').append(`
            <div id="toast-container" class="toast-container position-fixed bottom-0 end-0 p-3"></div>
        `);
    }
    
    const toastId = 'toast-' + Date.now();
    const toast = $(`
        <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="toast-header bg-${type} text-white">
                <strong class="me-auto">Notification</strong>
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="toast"></button>
            </div>
            <div class="toast-body">${message}</div>
        </div>
    `);
    
    $('#toast-container').append(toast);
    const bsToast = new bootstrap.Toast(toast[0]);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.on('hidden.bs.toast', function() {
        $(this).remove();
    });
}