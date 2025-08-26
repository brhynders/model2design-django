// Design Share Page JavaScript
// This file contains the 3D viewer and interactive functionality for the design share page

// Copy share URL to clipboard
function copyShareUrl() {
    const input = document.getElementById('shareUrl');
    input.select();
    document.execCommand('copy');
    
    // Show feedback
    const btn = event.target.closest('button');
    const originalHtml = btn.innerHTML;
    btn.innerHTML = '<i class="bi bi-check"></i>';
    btn.classList.add('btn-success');
    btn.classList.remove('btn-outline-secondary');
    
    setTimeout(() => {
        btn.innerHTML = originalHtml;
        btn.classList.remove('btn-success');
        btn.classList.add('btn-outline-secondary');
    }, 2000);
}

// Social sharing functions
function shareOnFacebook() {
    const url = encodeURIComponent(window.location.href);
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank', 'width=600,height=400');
}

function shareOnTwitter() {
    const url = encodeURIComponent(window.location.href);
    const text = encodeURIComponent('Check out this amazing design: ' + window.designShareData.designName);
    window.open(`https://twitter.com/intent/tweet?url=${url}&text=${text}`, '_blank', 'width=600,height=400');
}

function shareOnPinterest() {
    const url = encodeURIComponent(window.location.href);
    const image = encodeURIComponent(window.designShareData.thumbnailImage);
    const description = encodeURIComponent(window.designShareData.designName);
    window.open(`https://www.pinterest.com/pin/create/button/?url=${url}&media=${image}&description=${description}`, '_blank', 'width=600,height=400');
}

function shareViaEmail() {
    const subject = encodeURIComponent('Check out this design: ' + window.designShareData.designName);
    const body = encodeURIComponent('I thought you might like this design:\n\n' + window.designShareData.designName + '\n\n' + window.location.href);
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
}

// Copy design and redirect to editor
async function copyAndEditDesign() {
    const btn = document.getElementById('copy-design-btn');
    const originalHtml = btn.innerHTML;
    
    // Show loading state
    btn.disabled = true;
    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Copying design...';
    
    console.log('=== COPY DESIGN DEBUG START ===');
    console.log('Design ID:', window.designShareData.designId);
    console.log('Design Name:', window.designShareData.designName);
    
    try {
        const requestData = {
            design_id: window.designShareData.designId,
            new_name: window.designShareData.designName + ' (Copy)'
        };
        
        console.log('Request data:', requestData);
        
        // Create a copy of the design
        const response = await fetch('/api/designs.php?action=duplicate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        console.log('Response status:', response.status);
        console.log('Response headers:', Object.fromEntries(response.headers.entries()));
        
        const result = await response.json();
        
        console.log('Response result:', result);
        console.log('=== COPY DESIGN DEBUG END ===');
        
        if (result.success) {
            // Redirect to designer with the new design ID
            const productId = window.designShareData.productId;
            const designId = result.design_id;
            console.log('Success! Redirecting to designer with new design ID:', designId);
            window.location.href = `/designer?product=${productId}&design=${designId}`;
        } else {
            console.error('Error copying design:', result);
            console.error('Response status:', response.status);
            
            // Check if it's an authentication error
            if (result.error && (result.error.includes('login') || result.error.includes('not logged in'))) {
                // Redirect to login with return URL
                const productId = window.designShareData.productId;
                const returnUrl = `/designer?product=${productId}&copy=${window.designShareData.designId}`;
                window.location.href = `/login?return=${encodeURIComponent(returnUrl)}`;
            } else {
                // Show detailed error message
                const errorMsg = result.error || 'Unknown error occurred';
                alert(`Failed to copy design: ${errorMsg}`);
                
                // Restore button state
                btn.disabled = false;
                btn.innerHTML = originalHtml;
            }
        }
    } catch (error) {
        console.error('Error copying design:', error);
        
        // Check if it's a fetch error with response
        if (error.response) {
            // Check if it's a 401 Unauthorized (not logged in)
            if (error.response.status === 401) {
                // Redirect to login with return URL
                const productId = window.designShareData.productId;
                const returnUrl = `/designer?product=${productId}&copy=${window.designShareData.designId}`;
                window.location.href = `/login?return=${encodeURIComponent(returnUrl)}`;
                return;
            }
        }
        
        // For other errors, check response status from the response object
        try {
            const response = error.response || await fetch('/api/designs.php?action=duplicate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    design_id: window.designShareData.designId,
                    new_name: window.designShareData.designName + ' (Copy)'
                })
            });
            
            if (response.status === 401) {
                // Redirect to login with return URL
                const productId = window.designShareData.productId;
                const returnUrl = `/designer?product=${productId}&copy=${window.designShareData.designId}`;
                window.location.href = `/login?return=${encodeURIComponent(returnUrl)}`;
                return;
            }
        } catch (e) {
            // Ignore retry errors
        }
        
        alert(`Network error: ${error.message || 'Please check your connection and try again.'}`);
        
        // Restore button state
        btn.disabled = false;
        btn.innerHTML = originalHtml;
    }
}

// 3D Viewer for Design Share Page
let scene, camera, renderer, controls, pmremGenerator, rgbeLoader;
let currentProduct = null;
let layers = {};
let currentLayer = null;

// Initialize 3D viewer
function initDesignViewer() {
    const canvas = document.getElementById('share-three-canvas');
    const container = document.getElementById('three-container');
    const loading = document.getElementById('viewer-loading');
    
    if (!canvas || !container) {
        console.error('Canvas or container not found');
        return;
    }
    
    // Scene setup
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0xf8f9fa);
    
    // Camera setup
    camera = new THREE.PerspectiveCamera(75, container.clientWidth / container.clientHeight, 0.1, 1000);
    camera.position.set(0, 0, 5);
    
    // Renderer setup with same settings as designer
    renderer = new THREE.WebGLRenderer({
        canvas: canvas,
        antialias: true,
        alpha: false
    });
    renderer.setSize(container.clientWidth, container.clientHeight);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Cap at 2x for performance
    
    // Shadow mapping disabled since we're using environment lighting only
    renderer.shadowMap.enabled = false;
    renderer.outputEncoding = THREE.LinearEncoding;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1;
    
    // Create PMREM generator for environment maps
    pmremGenerator = new THREE.PMREMGenerator(renderer);
    pmremGenerator.compileEquirectangularShader();
    
    // Create RGBE loader
    rgbeLoader = new THREE.RGBELoader();
    
    // Controls setup
    controls = new THREE.OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.enablePan = false;
    controls.screenSpacePanning = false;
    controls.minDistance = 0.5;
    controls.maxDistance = 50;
    controls.maxPolarAngle = Math.PI;
    
    // Load environment map first, then product and design
    loadEnvironmentMap(() => {
        loadProductAndDesign();
    });
    
    console.log('🎯 Using HDR environment lighting only - no artificial lights');
    
    // Setup view controls
    setupViewControls();
    
    // Handle resize
    window.addEventListener('resize', onWindowResize);
    
    // Start render loop
    animate();
}

// Load environment map for proper lighting and reflections
function loadEnvironmentMap(callback) {
    console.log('🌅 Loading HDR environment map: /static/neutral.hdr');
    
    rgbeLoader.load(
        '/static/neutral.hdr',
        function(texture) {
            texture.mapping = THREE.EquirectangularReflectionMapping;
            
            // Generate environment map
            const envMap = pmremGenerator.fromEquirectangular(texture).texture;
            
            // Set as scene environment for reflections and lighting
            scene.environment = envMap;
            
            texture.dispose();
            pmremGenerator.dispose();
            
            console.log('✅ HDR environment map loaded and applied to scene');
            console.log('🎭 Using Linear tone mapping for accurate color reproduction');
            if (callback) callback();
        },
        function(progress) {
            console.log('📦 Loading HDR environment map progress...', progress);
        },
        function(error) {
            console.error('❌ Error loading HDR environment map:', error);
            console.warn('⚠️ Continuing without environment map - lighting may not be optimal');
            // Continue without environment map
            if (callback) callback();
        }
    );
}

// Load product model and apply design
async function loadProductAndDesign() {
    try {
        // Get product data from global variable
        const product = window.designShareData.products.find(p => p.id == window.designShareData.productId);
        
        if (!product) {
            throw new Error('Product not found');
        }
        
        console.log('Loading product:', product);
        
        // Load the actual GLTF model
        await loadProductModel(product);
        
        // Apply design data to the product
        if (window.designShareData.designData) {
            applyDesignToProduct(window.designShareData.designData);
        }
        
        // Hide loading
        const loading = document.getElementById('viewer-loading');
        if (loading) loading.style.display = 'none';
        
    } catch (error) {
        console.error('Error loading product and design:', error);
        
        // Show error message
        const loading = document.getElementById('viewer-loading');
        if (loading) {
            loading.innerHTML = `
                <div class="text-danger">
                    <i class="bi bi-exclamation-triangle mb-2" style="font-size: 2rem;"></i>
                    <div>Unable to load 3D design</div>
                    <small class="text-muted">Please try refreshing the page</small>
                </div>
            `;
        }
    }
}

// Load actual GLTF product model
async function loadProductModel(product) {
    console.log(`Loading 3D model: ${product.modelLink}`);
    
    // Clear existing objects
    const objectsToRemove = [];
    scene.traverse((child) => {
        if (child.type === 'Mesh' || child.type === 'Group') {
            objectsToRemove.push(child);
        }
    });
    objectsToRemove.forEach(obj => scene.remove(obj));
    
    // Adjust model path (same logic as designer)
    const modelPath = product.modelLink.startsWith('/models/') ? 
        product.modelLink.replace('/models/', '/static/models/') : 
        product.modelLink;
    
    // Load GLTF model
    const loader = new THREE.GLTFLoader();
    const gltf = await new Promise((resolve, reject) => {
        loader.load(
            modelPath,
            resolve,
            (progress) => {
                if (progress.total > 0) {
                    console.log('Loading progress:', Math.round(progress.loaded / progress.total * 100) + '%');
                }
            },
            (error) => {
                console.error('GLTF loading error for:', modelPath);
                console.error('Error details:', error);
                
                let errorMessage = 'Failed to load 3D model';
                if (error.message && error.message.includes('404')) {
                    errorMessage = `3D model file not found: ${modelPath}`;
                } else if (error.message && error.message.includes('JSON')) {
                    errorMessage = `3D model file is corrupted: ${modelPath}`;
                } else if (error.message) {
                    errorMessage = `3D model loading error: ${error.message}`;
                }
                
                reject(new Error(errorMessage));
            }
        );
    });
    
    console.log('✅ GLTF loaded successfully:', gltf);
    
    // Add model to scene
    scene.add(gltf.scene);
    currentProduct = gltf.scene;
    
    // Initialize layers from product mesh settings
    initializeLayersFromProduct(product);
    
    // Apply initial product color from product data
    if (product.meshSettings) {
        const firstLayer = Object.values(product.meshSettings)[0];
        if (firstLayer && firstLayer.initialColor) {
            updateProductColor('#' + firstLayer.initialColor);
            console.log('🎨 Applied initial product color from meshSettings:', '#' + firstLayer.initialColor);
        }
    }
    
    // Fit model to view (same as designer page)
    const box = new THREE.Box3().setFromObject(gltf.scene);
    const center = box.getCenter(new THREE.Vector3());
    const size = box.getSize(new THREE.Vector3());
    
    console.log('Model bounds:', { center, size });
    
    // Calculate optimal camera distance to fit model
    const maxDim = Math.max(size.x, size.y, size.z);
    const fov = camera.fov * (Math.PI / 180);
    
    // Use smaller padding for better fit
    let cameraZ = (maxDim / 2) / Math.tan(fov / 2);
    cameraZ *= 1.2; // Small padding for breathing room
    
    // Ensure reasonable minimum distance
    cameraZ = Math.max(cameraZ, 1);
    
    console.log('Calculated camera distance:', cameraZ, 'Model max dimension:', maxDim);
    
    // Position camera
    camera.position.set(center.x, center.y, center.z + cameraZ);
    camera.lookAt(center);
    
    // Update controls target
    controls.target.copy(center);
    controls.update();
    
    // Trigger a resize to ensure proper aspect ratio
    onWindowResize();
    
    console.log('✅ 3D model loaded and positioned');
}

// Apply design data to the product using layer system
function applyDesignToProduct(data) {
    if (!currentProduct || !data) return;
    
    console.log('🎨 Applying design data with layer system:', data);
    
    // Handle new layer-based data structure
    if (data.layers && typeof data.layers === 'object') {
        // First, ensure all layers start with empty decals
        Object.values(layers).forEach(layer => {
            layer.decals = [];
        });
        
        // Then apply decals only to layers that have them in the design data
        Object.keys(data.layers).forEach(layerName => {
            const layerData = data.layers[layerName];
            const layer = layers[layerName];
            
            if (!layer) {
                console.warn(`Layer ${layerName} not found in model`);
                return;
            }
            
            console.log(`Processing layer ${layerName}:`, layerData);
            
            // Apply layer color
            if (layerData.color) {
                updateLayerColor(layer, layerData.color);
                console.log(`🎨 Applied color to layer ${layerName}:`, layerData.color);
            }
            
            // Apply decals to layer
            if (layerData.decals && Array.isArray(layerData.decals) && layerData.decals.length > 0) {
                console.log(`Loading ${layerData.decals.length} decals for layer ${layerName}`);
                
                // Load all decals asynchronously
                Promise.all(layerData.decals.map(async (decalData) => {
                    try {
                        const decal = await createDecalFromData(decalData);
                        return decal;
                    } catch (error) {
                        console.error('Error creating decal:', error);
                        return null;
                    }
                })).then(decals => {
                    // Filter out null values and add to layer
                    layer.decals = decals.filter(decal => decal !== null);
                    console.log(`✅ Layer ${layerName} loaded ${layer.decals.length} decals`);
                    
                    // Render layer after all decals are loaded
                    renderLayer(layer);
                });
            } else {
                console.log(`No decals for layer ${layerName}, rendering empty`);
                // Render layer with no decals to clear any previous state
                renderLayer(layer);
            }
        });
        
        // Also render any layers not mentioned in the design data to ensure they're clean
        Object.keys(layers).forEach(layerName => {
            if (!data.layers[layerName]) {
                console.log(`Layer ${layerName} not in design data, rendering empty`);
                renderLayer(layers[layerName]);
            }
        });
    }
    
    // Handle legacy data formats
    else {
        // Apply base product color if specified in design data
        if (data.productColor || data.baseColor || data.color) {
            const color = data.productColor || data.baseColor || data.color;
            updateProductColor(color);
            console.log('🎨 Applied product base color:', color);
        }
        
        // Handle background color (legacy format)
        if (data.background) {
            updateProductColor(data.background);
            console.log('🎨 Applied background color:', data.background);
        }
    }
    
    console.log('✅ Design data application complete');
}

// Initialize layers from product data (like designer.js)
function initializeLayersFromProduct(product) {
    console.log('🔧 Initializing layers for product:', product.name);
    
    // Clear existing layers
    layers = {};
    currentLayer = null;
    
    // Initialize layers from meshes in the GLTF model
    currentProduct.traverse(child => {
        if (child.isMesh && child.material) {
            const meshSettings = product.meshSettings && product.meshSettings[child.name]
                ? product.meshSettings[child.name]
                : { canSelect: true, canAddImages: true, canChangeColor: true };
            
            // Clone material to ensure each mesh has its own material instance
            // This prevents shader modifications from affecting other meshes
            child.material = child.material.clone();
            
            // Set initial color
            if (meshSettings.initialColor) {
                child.material.color.setHex(parseInt(meshSettings.initialColor, 16));
            }
            
            // Create layer object
            layers[child.name] = {
                name: child.name,
                mesh: child,
                decals: [],
                material: product.initialBumpmap || "none",
                meshSettings: meshSettings,
                minX: meshSettings.minX || 0,
                maxX: meshSettings.maxX || 1,
                minY: meshSettings.minY || 0,
                maxY: meshSettings.maxY || 1,
                roughness: 1,
                metalness: 0,
            };
        }
    });
    
    // Set first layer as current (optional for viewing)
    const layerNames = Object.keys(layers);
    if (layerNames.length > 0) {
        currentLayer = layers[layerNames[0]];
    }
    
    console.log('✅ Layers initialized:', Object.keys(layers));
}

// Update color of a specific layer
function updateLayerColor(layer, color) {
    if (!layer || !layer.mesh) return;
    
    try {
        const colorObj = new THREE.Color(color);
        
        if (Array.isArray(layer.mesh.material)) {
            layer.mesh.material.forEach(material => {
                if (material.color) {
                    material.color.copy(colorObj);
                }
            });
        } else {
            if (layer.mesh.material.color) {
                layer.mesh.material.color.copy(colorObj);
            }
        }
        
        console.log(`🎨 Layer ${layer.name} color updated to:`, color);
    } catch (error) {
        console.error('❌ Error updating layer color:', error);
    }
}

// Create decal from design data
async function createDecalFromData(decalData) {
    if (!decalData) return null;
    
    console.log('Creating decal:', decalData.type, decalData);
    
    let texture = null;
    
    try {
        if (decalData.type === 'text' && decalData.textData) {
            // Create text texture
            texture = createTextTexture(decalData.textData);
            console.log('Created text texture');
        } else if (decalData.type === 'image' && decalData.imageUrl) {
            // Load image texture - use proxy for R2 images to avoid CORS
            let imageUrl = decalData.imageUrl;
            
            // Check if it's an R2 URL that needs proxying
            if (imageUrl.includes('filess.model2design.app') || imageUrl.includes('r2.cloudflarestorage.com')) {
                // Extract the path from the URL
                const url = new URL(imageUrl);
                const imagePath = url.pathname.substring(1); // Remove leading slash
                imageUrl = `/api/image-proxy.php?path=${encodeURIComponent(imagePath)}`;
                console.log('Using proxy for R2 image:', imageUrl);
            }
            
            console.log('Loading image from URL:', imageUrl);
            texture = await loadImageTexture(imageUrl);
            console.log('Image texture loaded successfully');
        }
        
        if (!texture) {
            console.warn('No texture created for decal:', decalData);
            return null;
        }
        
        const decal = {
            id: decalData.id || Math.random().toString(36),
            name: decalData.name || 'decal',
            type: decalData.type,
            texture: texture,
            position: decalData.position || { x: 0.5, y: 0.5 },
            size: decalData.size || { x: 0.3, y: 0.3 },
            rotation: decalData.rotation || 0,
            opacity: decalData.opacity !== undefined ? decalData.opacity : 1,
            flipX: decalData.flipX || false,
            flipY: decalData.flipY || false,
            aspectLocked: decalData.aspectLocked !== undefined ? decalData.aspectLocked : true
        };
        
        console.log('Decal created:', decal);
        return decal;
    } catch (error) {
        console.error('Error creating decal from data:', error);
        return null;
    }
}

// Create text texture for decals
function createTextTexture(textData) {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    
    // Set canvas size
    canvas.width = 512;
    canvas.height = 256;
    
    // Set font and style
    const fontSize = 48; // Fixed size for texture generation
    ctx.font = `${fontSize}px ${textData.font || 'Arial'}`;
    ctx.fillStyle = textData.color || '#000000';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    // Add border if specified
    if (textData.borderWidth && textData.borderWidth > 0) {
        ctx.strokeStyle = textData.borderColor || '#000000';
        ctx.lineWidth = textData.borderWidth;
        ctx.strokeText(textData.text, canvas.width / 2, canvas.height / 2);
    }
    
    // Draw text
    ctx.fillText(textData.text, canvas.width / 2, canvas.height / 2);
    
    // Create and return texture
    const texture = new THREE.CanvasTexture(canvas);
    texture.flipY = false;
    texture.needsUpdate = true;
    
    return texture;
}

// Load image texture for decals
function loadImageTexture(imageUrl) {
    return new Promise((resolve, reject) => {
        // First try to load the image to check if it's accessible
        const testImg = new Image();
        testImg.crossOrigin = 'anonymous';
        
        testImg.onload = function() {
            console.log('✅ Image accessible, loading as texture:', imageUrl);
            
            // Now load as Three.js texture
            const loader = new THREE.TextureLoader();
            loader.crossOrigin = 'anonymous';
            
            loader.load(
                imageUrl,
                (texture) => {
                    console.log('✅ Texture loaded successfully from:', imageUrl);
                    texture.encoding = THREE.sRGBEncoding;
                    texture.flipY = false;
                    texture.needsUpdate = true;
                    resolve(texture);
                },
                (progress) => {
                    // Progress callback
                    if (progress.total > 0) {
                        console.log('Loading texture:', Math.round(progress.loaded / progress.total * 100) + '%');
                    }
                },
                (error) => {
                    console.error('❌ Error loading texture from', imageUrl, ':', error);
                    reject(error);
                }
            );
        };
        
        testImg.onerror = function(error) {
            console.error('❌ Image not accessible:', imageUrl, error);
            reject(new Error('Image not accessible: ' + imageUrl));
        };
        
        testImg.src = imageUrl;
    });
}

// Render layer with decals using shader-based approach (from designer.js)
function renderLayer(layer) {
    if (!layer) return;
    
    const mesh = layer.mesh;
    const allDecals = layer.decals;
    
    // Filter out decals without textures
    const decals = allDecals.filter(d => d.texture);
    
    console.log(`Rendering layer ${layer.name} with`, decals.length, "decals (filtered from", allDecals.length, "total)");
    
    // If no decals with textures, reset material to default
    if (decals.length === 0) {
        mesh.material.onBeforeCompile = () => {};
        mesh.material.needsUpdate = true;
        return;
    }
    
    // Ensure Shader is not cached
    mesh.material.customProgramCacheKey = () =>
        Math.random().toString(36).substring(2, 15);
    
    // Hook Shader
    mesh.material.onBeforeCompile = (shader) => {
        // Add varying for UV coordinates
        shader.vertexShader = shader.vertexShader.replace(
            'void main()',
            `
            varying vec2 vDecalUv;
            void main()
            `
        );
        
        shader.vertexShader = shader.vertexShader.replace(
            '#include <uv_vertex>',
            `
            #include <uv_vertex>
            vDecalUv = uv;
            `
        );
        
        // Set Uniforms
        shader.uniforms.decalImages = { value: decals.map((d) => d.texture) };
        shader.uniforms.decalPositions = {
            value: decals.map((d) => new THREE.Vector2(d.position.x, d.position.y)),
        };
        shader.uniforms.decalRotations = {
            value: decals.map((d) => (d.rotation * Math.PI) / 180),
        };
        shader.uniforms.decalFlipXs = { value: decals.map((d) => d.flipX) };
        shader.uniforms.decalFlipYs = { value: decals.map((d) => d.flipY) };
        shader.uniforms.decalOpacities = { value: decals.map((d) => d.opacity) };
        shader.uniforms.decalSizes = {
            value: decals.map((d) => {
                if (d.aspectLocked && d.texture && d.texture.image) {
                    return new THREE.Vector2(
                        d.size.x,
                        d.size.x * (d.texture.image.height / d.texture.image.width)
                    );
                } else {
                    return new THREE.Vector2(d.size.x, d.size.y);
                }
            }),
        };
        shader.uniforms.minX = { value: parseFloat(layer.minX) };
        shader.uniforms.maxX = { value: parseFloat(layer.maxX) };
        shader.uniforms.minY = { value: parseFloat(layer.minY) };
        shader.uniforms.maxY = { value: parseFloat(layer.maxY) };
        
        // Modify fragment shader
        shader.fragmentShader = shader.fragmentShader.replace(
            "void main()",
            `
            varying vec2 vDecalUv;
            #define MAX_DECALS ${decals.length}
            #if MAX_DECALS > 0
                uniform sampler2D decalImages[MAX_DECALS];
                uniform vec2 decalPositions[MAX_DECALS];
                uniform vec2 decalSizes[MAX_DECALS];
                uniform float decalRotations[MAX_DECALS];
                uniform bool decalFlipXs[MAX_DECALS];
                uniform bool decalFlipYs[MAX_DECALS];
                uniform float decalOpacities[MAX_DECALS];
            #endif
            uniform float minX;
            uniform float maxX;
            uniform float minY;
            uniform float maxY;
            void main()
            `
        );
        
        // Replace normal texture mapping with custom one
        shader.fragmentShader = shader.fragmentShader.replace(
            "#include <map_fragment>",
            `
            #if MAX_DECALS > 0
                for (int i = 0; i < MAX_DECALS; i++) {
                    vec2 originalUV = vDecalUv;

                    vec2 rotatedUV = vDecalUv - decalPositions[i];
                    float c = cos(decalRotations[i]);
                    float s = sin(decalRotations[i]);
                    rotatedUV = vec2(
                        rotatedUV.x * c - rotatedUV.y * s,
                        rotatedUV.x * s + rotatedUV.y * c
                    );
                    rotatedUV += decalPositions[i];

                    vec2 uv = (rotatedUV - decalPositions[i]) / decalSizes[i] + 0.5;
                    
                    if (decalFlipXs[i]) {
                      uv.x = 1.0 - uv.x;
                    }
                    if (decalFlipYs[i]) {
                      uv.y = 1.0 - uv.y;
                    }

                    vec4 texColor = vec4(0.0);
                    ${generateSwitchCases(decals.length)}

                    if (uv.x >= 0.0 && uv.x <= 1.0 && uv.y >= 0.0 && uv.y <= 1.0 && originalUV.x >= minX && originalUV.x <= maxX && originalUV.y >= minY && originalUV.y <= maxY && gl_FrontFacing) {
                      float existingAlpha = diffuseColor.a;
                      float finalAlpha = existingAlpha * (1.0 - texColor.a * decalOpacities[i]) + texColor.a * decalOpacities[i];

                        if (finalAlpha < 0.001) {
                            diffuseColor.a = 0.0;
                        } else {
                            diffuseColor.rgb = (texColor.rgb * texColor.a * decalOpacities[i] + diffuseColor.rgb * existingAlpha * (1.0 - texColor.a * decalOpacities[i])) / finalAlpha;
                            diffuseColor.a = finalAlpha;
                        }
                    }
                }
            #endif
            `
        );
    };
    
    // Trigger Rerender of Material
    mesh.material.needsUpdate = true;
}

// Generate switch cases for shader (from designer.js)
function generateSwitchCases(numDecals) {
    let switchCases = "switch(i) {\n";
    for (let i = 0; i < numDecals; i++) {
        switchCases += `
                    case ${i}:
                        texColor = texture2D(decalImages[${i}], uv);
                        break;
                `;
    }
    switchCases += "\n}";
    return switchCases;
}

// Update product color (fallback for legacy data)
function updateProductColor(color) {
    if (!currentProduct) return;
    
    try {
        const colorObj = new THREE.Color(color);
        
        // Apply color to all materials in the GLTF scene
        currentProduct.traverse((child) => {
            if (child.isMesh && child.material) {
                if (Array.isArray(child.material)) {
                    // Handle multiple materials
                    child.material.forEach(material => {
                        if (material.color) {
                            material.color.copy(colorObj);
                        }
                    });
                } else {
                    // Handle single material
                    if (child.material.color) {
                        child.material.color.copy(colorObj);
                    }
                }
            }
        });
        
        console.log('🎨 Product color updated to:', color);
    } catch (error) {
        console.error('❌ Error updating product color:', error);
    }
}

// Setup view control buttons
function setupViewControls() {
    // Get model center and distance for view controls
    const getModelInfo = () => {
        if (!currentProduct) return { center: new THREE.Vector3(0, 0, 0), distance: 5 };
        
        const box = new THREE.Box3().setFromObject(currentProduct);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        const maxDim = Math.max(size.x, size.y, size.z);
        const fov = camera.fov * (Math.PI / 180);
        const distance = Math.max((maxDim / 2) / Math.tan(fov / 2) * 1.2, 1);
        
        return { center, distance };
    };
    
    // View preset buttons
    document.getElementById('view-front')?.addEventListener('click', () => {
        const { center, distance } = getModelInfo();
        camera.position.set(center.x, center.y, center.z + distance);
        camera.lookAt(center);
        controls.target.copy(center);
        controls.update();
    });
    
    document.getElementById('view-back')?.addEventListener('click', () => {
        const { center, distance } = getModelInfo();
        camera.position.set(center.x, center.y, center.z - distance);
        camera.lookAt(center);
        controls.target.copy(center);
        controls.update();
    });
    
    document.getElementById('view-left')?.addEventListener('click', () => {
        const { center, distance } = getModelInfo();
        camera.position.set(center.x - distance, center.y, center.z);
        camera.lookAt(center);
        controls.target.copy(center);
        controls.update();
    });
    
    document.getElementById('view-right')?.addEventListener('click', () => {
        const { center, distance } = getModelInfo();
        camera.position.set(center.x + distance, center.y, center.z);
        camera.lookAt(center);
        controls.target.copy(center);
        controls.update();
    });
    
    document.getElementById('view-reset')?.addEventListener('click', () => {
        const { center, distance } = getModelInfo();
        camera.position.set(center.x, center.y, center.z + distance);
        camera.lookAt(center);
        controls.target.copy(center);
        controls.update();
    });
    
    // Zoom controls
    document.getElementById('zoom-in')?.addEventListener('click', () => {
        const direction = camera.position.clone().sub(controls.target).normalize();
        camera.position.addScaledVector(direction, -0.5);
        controls.update();
    });
    
    document.getElementById('zoom-out')?.addEventListener('click', () => {
        const direction = camera.position.clone().sub(controls.target).normalize();
        camera.position.addScaledVector(direction, 0.5);
        controls.update();
    });
}

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    
    if (controls) {
        controls.update();
    }
    
    if (renderer && scene && camera) {
        renderer.render(scene, camera);
    }
}

// Handle window resize
function onWindowResize() {
    const container = document.getElementById('three-container');
    if (!container || !camera || !renderer) return;
    
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

// Add to Cart Modal functionality
function initAddToCartModal() {
    // Check if add to cart functionality is available
    if (!window.designShareData.pricingTiers) {
        console.log('No pricing data available - cart functionality disabled');
        return;
    }
    
    // Pricing data from PHP
    const pricingTiers = window.designShareData.pricingTiers;
    let sizeQuantities = {}; // Store quantities for each size
    
    // Update size quantity
    window.updateSizeQuantity = function(size, change) {
        if (!sizeQuantities[size]) {
            sizeQuantities[size] = 0;
        }
        
        sizeQuantities[size] = Math.max(0, sizeQuantities[size] + change);
        
        // Update the input field
        const input = document.querySelector(`input[data-size="${size}"]`);
        if (input) {
            input.value = sizeQuantities[size];
        }
        
        // Update card appearance
        const card = input?.closest('.size-card-modal');
        if (card) {
            if (sizeQuantities[size] > 0) {
                card.classList.add('has-quantity');
            } else {
                card.classList.remove('has-quantity');
            }
        }
        
        updateCartTotals();
    };
    
    // Update cart totals
    function updateCartTotals() {
        const totalQuantity = Object.values(sizeQuantities).reduce((sum, qty) => sum + qty, 0);
        
        // Calculate price per unit based on total quantity
        let priceEach = pricingTiers[1] || 50;
        const sortedTiers = Object.keys(pricingTiers).map(Number).sort((a, b) => b - a);
        for (let tierQty of sortedTiers) {
            if (totalQuantity >= tierQty) {
                priceEach = pricingTiers[tierQty];
                break;
            }
        }
        
        const total = totalQuantity * priceEach;
        
        // Update display
        const quantityEl = document.getElementById('cart-quantity-modal');
        const priceEl = document.getElementById('cart-price-each-modal');
        const totalEl = document.getElementById('cart-total-modal');
        
        if (quantityEl) quantityEl.textContent = totalQuantity;
        if (priceEl) priceEl.textContent = '$' + priceEach.toFixed(2);
        if (totalEl) totalEl.textContent = '$' + total.toFixed(2);
        
        // Enable/disable add to cart button
        const addBtn = document.getElementById('confirm-add-cart-btn');
        if (addBtn) {
            addBtn.disabled = totalQuantity === 0;
        }
    }
    
    // Setup pricing popover
    function setupPricingPopover() {
        const pricingBtn = document.getElementById('pricing-info-btn');
        if (!pricingBtn) return;
        
        // Build pricing content
        let content = '<div class="px-1">';
        Object.entries(pricingTiers).forEach(([qty, price]) => {
            content += `<div class="d-flex justify-content-between align-items-center py-1 px-1">`;
            content += `<span class="text-muted me-3">${qty}+ pieces</span>`;
            content += `<span class="fw-bold text-success text-end">$${parseFloat(price).toFixed(2)} <small class="text-muted fw-normal">each</small></span>`;
            content += `</div>`;
        });
        content += '</div>';
        
        new bootstrap.Popover(pricingBtn, {
            placement: 'top',
            html: true,
            title: 'Bulk Pricing',
            content: content,
            trigger: 'hover focus'
        });
    }
    
    // Add to cart button
    document.getElementById('confirm-add-cart-btn')?.addEventListener('click', function() {
        const designId = window.designShareData.designId;
        
        // Check if any quantities are selected
        const totalQuantity = Object.values(sizeQuantities).reduce((sum, qty) => sum + qty, 0);
        if (totalQuantity === 0) {
            alert('Please select at least one size and quantity');
            return;
        }
        
        // Show loading state
        this.disabled = true;
        this.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span>Adding...';
        
        // Add each size+quantity combination to cart
        const promises = [];
        
        Object.entries(sizeQuantities).forEach(([size, quantity]) => {
            if (quantity > 0) {
                const formData = new FormData();
                formData.append('design_id', designId);
                formData.append('size', size);
                formData.append('quantity', quantity);
                
                promises.push(
                    fetch('/add-to-cart.php', {
                        method: 'POST',
                        body: formData
                    }).then(response => response.json())
                );
            }
        });
        
        // Wait for all additions to complete
        Promise.all(promises)
        .then(results => {
            const hasError = results.some(result => !result.success);
            if (hasError) {
                const errorMessages = results.filter(r => !r.success).map(r => r.message).join(', ');
                alert('Error adding to cart: ' + errorMessages);
            } else {
                // Close modal and redirect to cart
                bootstrap.Modal.getInstance(document.getElementById('cartModal')).hide();
                window.location.href = '/cart?added=' + designId;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error adding to cart. Please try again.');
        })
        .finally(() => {
            // Restore button state
            this.disabled = false;
            this.innerHTML = '<i class="bi bi-cart-plus"></i> Add to Cart';
        });
    });
    
    // Setup input listeners for manual quantity entry
    function setupInputListeners() {
        document.querySelectorAll('.qty-input-modal').forEach(input => {
            input.addEventListener('input', function() {
                const size = this.getAttribute('data-size');
                let value = parseInt(this.value) || 0;
                value = Math.max(0, Math.min(999, value)); // Clamp between 0 and 999
                
                sizeQuantities[size] = value;
                this.value = value;
                
                // Update card appearance
                const card = this.closest('.size-card-modal');
                if (card) {
                    if (value > 0) {
                        card.classList.add('has-quantity');
                    } else {
                        card.classList.remove('has-quantity');
                    }
                }
                
                updateCartTotals();
            });
            
            input.addEventListener('blur', function() {
                // Ensure valid value on blur
                const size = this.getAttribute('data-size');
                const value = sizeQuantities[size] || 0;
                this.value = value;
            });
        });
    }
    
    // Initialize
    setupPricingPopover();
    setupInputListeners();
    updateCartTotals();
}

// Initialize when page loads
document.addEventListener('DOMContentLoaded', function() {
    initDesignViewer();
    initAddToCartModal();
});