// Show content as soon as DOM loads
document.addEventListener('DOMContentLoaded', function () {
    document.body.classList.add('content-loaded');
});

// Rest of your existing JavaScript...
// // Show loading screen immediately
document.documentElement.style.overflow = 'hidden';

// Loading Screen - Fixed
window.addEventListener('load', function () {
    const loadingScreen = document.getElementById('loadingScreen');

    // Minimum loading time of 2 seconds
    setTimeout(function () {
        loadingScreen.classList.add('fade-out');
        document.documentElement.style.overflow = 'auto';

        // Start counter animations AFTER loading screen starts fading
        setTimeout(function () {
            initCounters();
        }, 300);

        // Remove loading screen from DOM
        setTimeout(function () {
            if (loadingScreen) {
                loadingScreen.remove();
            }
        }, 500);
    }, 2000);
});

document.addEventListener('DOMContentLoaded', function () {
    // --- HERO IMAGE SLIDER ---
    function initHeroSlider() {
        const slides = document.querySelectorAll('.hero-slide');
        let currentSlide = 0;

        function nextSlide() {
            slides[currentSlide].classList.remove('active');
            currentSlide = (currentSlide + 1) % slides.length;
            slides[currentSlide].classList.add('active');
        }

        // Auto-advance slides every 5 seconds
        setInterval(nextSlide, 5000);
    }

    // Initialize hero slider
    initHeroSlider();

    // --- POPULATE TESTIMONIAL RATINGS ---
    function populateStars() {
        document.querySelectorAll('.testimonial-card').forEach(card => {
            const rating = parseInt(card.dataset.rating) || 5;
            const ratingContainer = card.querySelector('.rating');
            let starsHTML = '';

            for (let i = 0; i < 5; i++) {
                if (i < rating) {
                    starsHTML += '<i class="fas fa-star"></i>';
                } else {
                    starsHTML += '<i class="fas fa-star" style="opacity: 0.3;"></i>';
                }
            }

            if (ratingContainer) {
                ratingContainer.innerHTML = starsHTML;
            }
        });
    }

    // --- FIXED CAROUSEL INITIALIZATION ---
    const projectsSwiper = new Swiper('.projects-swiper', {
        slidesPerView: 1,
        spaceBetween: 20,
        loop: true,
        centeredSlides: true,
        preloadImages: false,
        lazy: false,
        watchSlidesProgress: false,
        watchSlidesVisibility: false,
        grabCursor: true,
        touchRatio: 1,
        touchAngle: 45,
        longSwipesRatio: 0.5,
        autoplay: {
            delay: 3000,
            disableOnInteraction: false,
            pauseOnMouseEnter: true,
            stopOnLastSlide: false
        },
        speed: 600,
        runCallbacksOnInit: false,
        pagination: {
            el: '.projects-swiper .swiper-pagination',
            clickable: true
        },
        breakpoints: {
            480: {
                slidesPerView: 1,
                spaceBetween: 15,
                centeredSlides: true
            },
            640: {
                slidesPerView: 1.2,
                spaceBetween: 20,
                centeredSlides: true
            },
            768: {
                slidesPerView: 1.5,
                spaceBetween: 25,
                centeredSlides: true
            },
            1024: {
                slidesPerView: 2.5,
                spaceBetween: 30,
                centeredSlides: true
            },
            1200: {
                slidesPerView: 3,
                spaceBetween: 30,
                centeredSlides: false
            }
        }
    });

    const testimonialsSwiper = new Swiper('.testimonials-swiper', {
        slidesPerView: 1,
        spaceBetween: 20,
        loop: true,
        centeredSlides: true,
        preloadImages: false,
        lazy: false,
        watchSlidesProgress: false,
        watchSlidesVisibility: false,
        grabCursor: true,
        touchRatio: 1,
        touchAngle: 45,
        longSwipesRatio: 0.5,
        autoplay: {
            delay: 4000,
            disableOnInteraction: false,
            pauseOnMouseEnter: true,
            stopOnLastSlide: false
        },
        speed: 800,
        runCallbacksOnInit: false,
        pagination: {
            el: '.testimonials-swiper .swiper-pagination',
            clickable: true
        },
        breakpoints: {
            480: {
                slidesPerView: 1,
                spaceBetween: 15,
                centeredSlides: true
            },
            640: {
                slidesPerView: 1.2,
                spaceBetween: 20,
                centeredSlides: true
            },
            768: {
                slidesPerView: 1.5,
                spaceBetween: 25,
                centeredSlides: true
            },
            1024: {
                slidesPerView: 2.5,
                spaceBetween: 30,
                centeredSlides: true
            },
            1200: {
                slidesPerView: 3,
                spaceBetween: 30,
                centeredSlides: false
            }
        },
        on: {
            init: function () {
                // Populate stars after swiper initialization
                setTimeout(populateStars, 100);
            },
            slideChange: function () {
                // Re-populate stars when slides change
                setTimeout(populateStars, 50);
            }
        }
    });

    // Initial population of stars
    populateStars();

    // --- DYNAMIC COPYRIGHT YEAR ---
    document.getElementById('copyrightYear').textContent = new Date().getFullYear();

    // --- MOBILE MENU TOGGLE (Fixed Version) ---
    const mobileMenuBtn = document.getElementById('mobileMenuBtn');
    const mobileNav = document.getElementById('mobileNav');

    if (mobileMenuBtn && mobileNav) {
        // Toggle mobile menu
        mobileMenuBtn.addEventListener('click', function (e) {
            e.preventDefault();
            mobileNav.classList.toggle('active');

            // Change hamburger icon to X when open
            const icon = mobileMenuBtn.querySelector('i');
            if (mobileNav.classList.contains('active')) {
                icon.classList.remove('fa-bars');
                icon.classList.add('fa-times');
            } else {
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });

        // Close mobile menu when clicking on links
        document.querySelectorAll('.mobile-nav a').forEach(link => {
            link.addEventListener('click', function () {
                mobileNav.classList.remove('active');
                const icon = mobileMenuBtn.querySelector('i');
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            });
        });

        // Close mobile menu when clicking outside
        document.addEventListener('click', function (e) {
            if (!mobileMenuBtn.contains(e.target) && !mobileNav.contains(e.target)) {
                mobileNav.classList.remove('active');
                const icon = mobileMenuBtn.querySelector('i');
                icon.classList.remove('fa-times');
                icon.classList.add('fa-bars');
            }
        });
    }

    // --- CONTACT FORM AJAX SUBMISSION ---
    const queryForm = document.getElementById('customerQueryForm');
    const formMsg = document.getElementById('formMsg');
    const submitBtn = document.getElementById('submitBtn');

    queryForm.addEventListener('submit', function (e) {
        e.preventDefault();
        submitBtn.disabled = true;
        submitBtn.innerHTML = 'Sending... <i class="fas fa-spinner fa-spin"></i>';

        fetch('/api/contact', {
            method: 'POST',
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(Object.fromEntries(new FormData(queryForm).entries()))
        })
            .then(resp => resp.json())
            .then(res => {
                showFormMessage(res.message, res.success ? 'success' : 'error');
                if (res.success) queryForm.reset();
            })
            .catch(() => showFormMessage('A network error occurred.', 'error'))
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = 'Send Query <i class="fas fa-paper-plane"></i>';
            });
    });

    function showFormMessage(message, type) {
        formMsg.textContent = message;
        formMsg.className = `form-msg-box ${type}`;
    }

    // --- SCROLL-BASED ANIMATIONS ---
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
            }
        });
    }, { threshold: 0.1, rootMargin: '0px 0px -50px 0px' });

    document.querySelectorAll('.fade-in-section').forEach(section => {
        observer.observe(section);
    });

    // --- ACTIVE NAV LINK ON SCROLL ---
    const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');
    const sections = document.querySelectorAll('section[id]');

    function updateActiveNav() {
        let current = '';
        const scrollY = window.pageYOffset;

        sections.forEach(section => {
            const sectionTop = section.offsetTop - 100;
            const sectionHeight = section.offsetHeight;

            if (scrollY >= sectionTop && scrollY < sectionTop + sectionHeight) {
                current = section.getAttribute('id');
            }
        });

        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    }

    window.addEventListener('scroll', updateActiveNav);
    updateActiveNav(); // Run once on load

    // Smart Navbar
    let lastScrollTop = 0;
    const navbar = document.querySelector('.navbar');

    function handleSmartNavbar() {
        const currentScroll = window.pageYOffset;

        if (currentScroll > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }

        if (currentScroll <= 100) {
            navbar.classList.remove('navbar-hidden');
            lastScrollTop = currentScroll;
            return;
        }

        if (currentScroll > lastScrollTop) {
            navbar.classList.add('navbar-hidden');
        } else {
            navbar.classList.remove('navbar-hidden');
        }

        lastScrollTop = currentScroll;
    }

    window.addEventListener('scroll', handleSmartNavbar);
});

// Counter Animation Functions
function startCounter(element, target) {
    let count = 0;
    const increment = target / 60;

    const timer = setInterval(() => {
        count += increment;
        if (count >= target) {
            element.textContent = target + '+';
            clearInterval(timer);
        } else {
            element.textContent = Math.floor(count) + '+';
        }
    }, 30);
}

function initCounters() {
    const counters = [
        { element: document.querySelector('.hero-stats .stat:nth-child(1) h3'), target: 300 },
        { element: document.querySelector('.hero-stats .stat:nth-child(2) h3'), target: 40 },
        { element: document.querySelector('.hero-stats .stat:nth-child(3) h3'), target: 400 }
    ];

    counters.forEach((counter, index) => {
        if (counter.element) {
            counter.element.textContent = '0+';
            setTimeout(() => {
                startCounter(counter.element, counter.target);
            }, index * 200);
        }
    });
}