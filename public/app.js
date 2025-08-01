// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded, initializing AstraFabric...');
    
    // Initialize 3D background
    init3DBackground();
    
    // Initialize payment modal
    initPaymentModal();
    
    // Initialize pricing
    initPricing();
});

// 3D Background Implementation
function init3DBackground() {
    console.log('Initializing 3D background...');
    
    // Check if Three.js is loaded
    if (typeof THREE === 'undefined') {
        console.error('Three.js not loaded!');
        return;
    }
    
    // Get container
    const container = document.getElementById('web3-background');
    if (!container) {
        console.error('Web3 background container not found!');
        return;
    }
    
    // Scene setup
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ 
        alpha: true, 
        antialias: true 
    });
    
    renderer.setSize(window.innerWidth, window.innerHeight);
    renderer.setPixelRatio(window.devicePixelRatio);
    container.appendChild(renderer.domElement);
    
    // Create particles (nodes)
    const particles = [];
    const particleGeometry = new THREE.SphereGeometry(0.1, 8, 8);
    const particleMaterial = new THREE.MeshBasicMaterial({ 
        color: 0x1E40AF, // AstraFabric blue
        transparent: true,
        opacity: 0.8
    });
    
    // Create particle system
    for (let i = 0; i < 50; i++) {
        const particle = new THREE.Mesh(particleGeometry, particleMaterial);
        particle.position.x = (Math.random() - 0.5) * 20;
        particle.position.y = (Math.random() - 0.5) * 20;
        particle.position.z = (Math.random() - 0.5) * 20;
        particle.userData.velocity = new THREE.Vector3(
            (Math.random() - 0.5) * 0.01,
            (Math.random() - 0.5) * 0.01,
            (Math.random() - 0.5) * 0.01
        );
        scene.add(particle);
        particles.push(particle);
    }
    
    // Create connections between particles
    const connections = [];
    const connectionMaterial = new THREE.LineBasicMaterial({ 
        color: 0xF97316, // AstraFabric orange
        transparent: true,
        opacity: 0.2
    });
    
    for (let i = 0; i < particles.length; i++) {
        for (let j = i + 1; j < particles.length; j++) {
            const distance = particles[i].position.distanceTo(particles[j].position);
            if (distance < 5) {
                const geometry = new THREE.BufferGeometry().setFromPoints([
                    particles[i].position,
                    particles[j].position
                ]);
                const connection = new THREE.Line(geometry, connectionMaterial);
                scene.add(connection);
                connections.push({
                    line: connection,
                    particleA: particles[i],
                    particleB: particles[j]
                });
            }
        }
    }
    
    // Create central shield
    const shieldGeometry = new THREE.ConeGeometry(1, 2, 4);
    const shieldMaterial = new THREE.MeshBasicMaterial({ 
        color: 0x1E40AF,
        wireframe: true
    });
    const shield = new THREE.Mesh(shieldGeometry, shieldMaterial);
    scene.add(shield);
    
    // Position camera
    camera.position.z = 10;
    
    // Animation loop
    function animate() {
        requestAnimationFrame(animate);
        
        // Animate particles
        particles.forEach(particle => {
            particle.position.add(particle.userData.velocity);
            
            // Bounce off boundaries
            if (Math.abs(particle.position.x) > 10) particle.userData.velocity.x *= -1;
            if (Math.abs(particle.position.y) > 10) particle.userData.velocity.y *= -1;
            if (Math.abs(particle.position.z) > 10) particle.userData.velocity.z *= -1;
        });
        
        // Update connections
        connections.forEach(conn => {
            const positions = conn.line.geometry.attributes.position.array;
            positions[0] = conn.particleA.position.x;
            positions[1] = conn.particleA.position.y;
            positions[2] = conn.particleA.position.z;
            positions[3] = conn.particleB.position.x;
            positions[4] = conn.particleB.position.y;
            positions[5] = conn.particleB.position.z;
            conn.line.geometry.attributes.position.needsUpdate = true;
        });
        
        // Rotate shield
        shield.rotation.x += 0.005;
        shield.rotation.y += 0.005;
        
        renderer.render(scene, camera);
    }
    
    animate();
    
    // Handle window resize
    window.addEventListener('resize', () => {
        camera.aspect = window.innerWidth / window.innerHeight;
        camera.updateProjectionMatrix();
        renderer.setSize(window.innerWidth, window.innerHeight);
    });
    
    console.log('3D background initialized successfully');
}

// Payment Modal Implementation
function initPaymentModal() {
    console.log('Initializing payment modal...');
    
    // Get modal elements
    const modal = document.getElementById('payment-modal');
    const closeBtn = document.querySelector('.close-modal');
    
    // Close modal when clicking the close button
    if (closeBtn) {
        closeBtn.addEventListener('click', () => {
            modal.style.display = 'none';
        });
    }
    
    // Close modal when clicking outside
    window.addEventListener('click', (event) => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
    
    console.log('Payment modal initialized');
}

// Pricing Implementation
function initPricing() {
    console.log('Initializing pricing...');
    
    // Get plan selection buttons
    const planButtons = document.querySelectorAll('.select-plan');
    planButtons.forEach(button => {
        button.addEventListener('click', function() {
            const plan = this.getAttribute('data-plan');
            showPaymentModal();
            // Pre-select the plan
            setTimeout(() => {
                const planCards = document.querySelectorAll('#step-1 .plan-card');
                planCards.forEach(card => {
                    card.classList.remove('selected');
                    if (card.getAttribute('data-plan') === plan) {
                        card.classList.add('selected');
                    }
                });
            }, 100);
        });
    });
    
    console.log('Pricing initialized');
}

// Global variables for payment modal
let currentStep = 1;
let selectedPlan = null;
let selectedCurrency = 'USD';
let selectedPaymentMethod = null;
let selectedCryptoCurrency = 'USDT';

// Show payment modal
function showPaymentModal() {
    console.log('Showing payment modal...');
    const modal = document.getElementById('payment-modal');
    if (modal) {
        modal.style.display = 'block';
        currentStep = 1;
        showStep(currentStep);
    }
}

// Show specific step
function showStep(step) {
    console.log('Showing step:', step);
    
    // Hide all steps
    document.querySelectorAll('.payment-step').forEach(el => {
        el.classList.remove('active');
    });
    
    // Show current step
    const currentStepEl = document.getElementById(`step-${step}`);
    if (currentStepEl) {
        currentStepEl.classList.add('active');
    }
    
    // Update step indicators
    document.querySelectorAll('.step').forEach(el => {
        el.classList.remove('active');
    });
    
    const stepIndicator = document.querySelector(`.step[data-step="${step}"]`);
    if (stepIndicator) {
        stepIndicator.classList.add('active');
    }
    
    // Update navigation buttons
    const prevBtn = document.getElementById('prev-step');
    const nextBtn = document.getElementById('next-step');
    
    if (prevBtn) {
        prevBtn.style.display = step === 1 ? 'none' : 'block';
    }
    
    if (nextBtn) {
        nextBtn.style.display = step === 3 ? 'none' : 'block';
    }
    
    // Update summary on step 3
    if (step === 3) {
        updatePaymentSummary();
    }
}

// Change step
function changeStep(direction) {
    const newStep = currentStep + direction;
    if (newStep >= 1 && newStep <= 3) {
        currentStep = newStep;
        showStep(currentStep);
    }
}

// Plan selection in modal
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('select-plan-btn')) {
        document.querySelectorAll('#step-1 .plan-card').forEach(card => {
            card.classList.remove('selected');
        });
        e.target.closest('.plan-card').classList.add('selected');
        selectedPlan = e.target.closest('.plan-card').getAttribute('data-plan');
    }
    
    if (e.target.classList.contains('select-method-btn')) {
        document.querySelectorAll('.method-card').forEach(card => {
            card.classList.remove('selected');
        });
        e.target.closest('.method-card').classList.add('selected');
        selectedPaymentMethod = e.target.closest('.method-card').getAttribute('data-method');
        
        if (selectedPaymentMethod === 'crypto') {
            showCryptoOptions();
        }
    }
});

// Currency selection
document.getElementById('currency-select')?.addEventListener('change', function() {
    selectedCurrency = this.value;
    updatePrices();
});

document.getElementById('modal-currency-select')?.addEventListener('change', function() {
    selectedCurrency = this.value;
    updateModalPrices();
});

// Update prices
function updatePrices() {
    console.log('Updating prices...');
    const selectedCurrency = document.getElementById('currency-select').value;
    
    const currencySymbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'NGN': '₦',
        'CAD': 'C$',
        'AUD': 'A$'
    };
    
    document.querySelectorAll('.amount').forEach(el => {
        const usdAmount = parseFloat(el.getAttribute('data-usd'));
        el.textContent = usdAmount.toFixed(2);
    });
    
    document.querySelectorAll('.currency-symbol').forEach(el => {
        el.textContent = currencySymbols[selectedCurrency] || '$';
    });
}

// Update modal prices
function updateModalPrices() {
    console.log('Updating modal prices...');
    const selectedCurrency = document.getElementById('modal-currency-select').value;
    
    const currencySymbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'NGN': '₦',
        'CAD': 'C$',
        'AUD': 'A$'
    };
    
    document.querySelectorAll('#step-1 .amount').forEach(el => {
        const usdAmount = parseFloat(el.getAttribute('data-usd'));
        el.textContent = usdAmount.toFixed(2);
    });
    
    document.querySelectorAll('#step-1 .currency-symbol').forEach(el => {
        el.textContent = currencySymbols[selectedCurrency] || '$';
    });
}

// Show crypto options
function showCryptoOptions() {
    console.log('Showing crypto options...');
    const cryptoOptionsHtml = `
        <div class="form-group">
            <label for="crypto-select">Select Cryptocurrency</label>
            <select id="crypto-select">
                <option value="BTC">Bitcoin (BTC)</option>
                <option value="ETH">Ethereum (ETH)</option>
                <option value="USDT">Tether (USDT)</option>
                <option value="BNB">Binance Coin (BNB)</option>
                <option value="LTC">Litecoin (LTC)</option>
            </select>
        </div>
    `;
    
    const paymentMethodDetails = document.getElementById('payment-method-details');
    if (paymentMethodDetails) {
        paymentMethodDetails.innerHTML = cryptoOptionsHtml;
        
        document.getElementById('crypto-select')?.addEventListener('change', function() {
            selectedCryptoCurrency = this.value;
        });
    }
}

// Update payment summary
function updatePaymentSummary() {
    console.log('Updating payment summary...');
    
    const planNames = {
        'starter': 'Starter',
        'professional': 'Professional',
        'enterprise': 'Enterprise'
    };
    
    const methodNames = {
        'flutterwave': 'Flutterwave',
        'crypto': 'Cryptocurrency'
    };
    
    const planAmounts = {
        'starter': 29,
        'professional': 79,
        'enterprise': 199
    };
    
    const currencySymbols = {
        'USD': '$',
        'EUR': '€',
        'GBP': '£',
        'NGN': '₦',
        'CAD': 'C$',
        'AUD': 'A$'
    };
    
    // Update summary elements
    const summaryPlan = document.getElementById('summary-plan');
    const summaryCurrency = document.getElementById('summary-currency');
    const summaryMethod = document.getElementById('summary-method');
    const summaryTotal = document.getElementById('summary-total');
    
    if (summaryPlan) summaryPlan.textContent = planNames[selectedPlan] || '-';
    if (summaryCurrency) summaryCurrency.textContent = selectedCurrency;
    if (summaryMethod) summaryMethod.textContent = methodNames[selectedPaymentMethod] || '-';
    
    if (summaryTotal && selectedPlan) {
        const usdAmount = planAmounts[selectedPlan];
        summaryTotal.textContent = `${currencySymbols[selectedCurrency] || '$'}${usdAmount}`;
    }
    
    // Show payment method details
    const paymentMethodDetails = document.getElementById('payment-method-details');
    if (paymentMethodDetails) {
        if (selectedPaymentMethod === 'crypto') {
            showCryptoOptions();
        } else {
            paymentMethodDetails.innerHTML = '';
        }
    }
}

// Form submission
document.getElementById('payment-form')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    console.log('Submitting payment form...');
    
    const email = document.getElementById('email')?.value;
    const planAmounts = {
        'starter': 29,
        'professional': 79,
        'enterprise': 199
    };
    
    const amount = planAmounts[selectedPlan];
    
    if (!email || !amount) {
        alert('Please fill in all required fields');
        return;
    }
    
    try {
        const response = await fetch('/api/initialize-payment', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email,
                amount,
                currency: selectedCurrency,
                paymentMethod: selectedPaymentMethod,
                cryptoCurrency: selectedCryptoCurrency
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Redirect to payment gateway
            if (data.gateway === 'flutterwave') {
                window.location.href = data.data.link;
            } else if (data.gateway === 'nowpayments') {
                window.location.href = data.data.pay_url;
            }
        } else {
            alert('Payment initialization failed: ' + data.error);
        }
    } catch (error) {
        console.error('Payment initialization failed:', error);
        alert('Payment initialization failed. Please try again.');
    }
});

// Demo function
function showDemo() {
    alert('Demo video coming soon!');
}

// Initialize everything when page loads
window.addEventListener('load', function() {
    console.log('Page fully loaded');
});
