const fs = require('fs');
const path = require('path');

// Create directories if they don't exist
['public', 'public/images2'].forEach(dir => {
    if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
    }
});

// Function to create an SVG logo
function createSVGLogo(width, height, text, filename) {
    const svg = `<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="${width}" height="${height}" xmlns="http://www.w3.org/2000/svg">
    <defs>
        <linearGradient id="gradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" style="stop-color:#1E40AF;stop-opacity:1" />
            <stop offset="100%" style="stop-color:#F97316;stop-opacity:1" />
        </linearGradient>
    </defs>
    <rect width="100%" height="100%" fill="url(#gradient)"/>
    <text x="50%" y="50%" 
          font-family="Arial, sans-serif" 
          font-size="${height/4}px" 
          fill="white" 
          text-anchor="middle" 
          dominant-baseline="middle"
          font-weight="bold">${text}</text>
</svg>`;

    fs.writeFileSync(filename, svg);
    console.log(`Created ${filename}`);
}

// Create different versions of the logo
createSVGLogo(200, 200, 'AF', 'public/ASTRAFRABRIC-LOGO.svg');
createSVGLogo(400, 200, 'AstraFabric', 'public/ASTRAFRABRIC-BRAND.svg');
createSVGLogo(200, 200, 'AF', 'public/images2/logo.svg');
createSVGLogo(32, 32, 'A', 'public/favicon.svg');
