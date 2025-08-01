const { createCanvas } = require('canvas');
const fs = require('fs');
const path = require('path');

// Create directories if they don't exist
['public', 'public/images2'].forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
});

// Function to create a gradient logo
function createLogo(width, height, text, filename) {
    const canvas = createCanvas(width, height);
    const ctx = canvas.getContext('2d');

    // Create gradient background
    const gradient = ctx.createLinearGradient(0, 0, width, height);
    gradient.addColorStop(0, '#1E40AF');  // Primary blue
    gradient.addColorStop(1, '#F97316');  // Secondary orange
    
    // Fill background
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, width, height);

    // Add text
    ctx.fillStyle = 'white';
    ctx.font = `bold ${height/4}px Inter, sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(text, width/2, height/2);

    // Save to file
    const buffer = canvas.toBuffer('image/png');
    fs.writeFileSync(filename, buffer);
    console.log(`Created ${filename}`);
}

// Create different versions of the logo
createLogo(200, 200, 'AF', 'public/ASTRAFRABRIC-LOGO.png');
createLogo(400, 200, 'AstraFabric', 'public/ASTRAFRABRIC-BRAND.png');
createLogo(200, 200, 'AF', 'public/images2/logo.png');

// Create favicon
createLogo(32, 32, 'A', 'public/favicon.ico');
