/**
 * Alpine.js Designer - Modern reactive 3D designer application
 * Replaces jQuery-based designer.js with Alpine.js reactivity
 */

// Debug logging
const DEBUG = true;
const debugLog = DEBUG ? console.log : () => {};
const debugWarn = DEBUG ? console.warn : () => {};
const debugError = DEBUG ? console.error : () => {};

// Three.js variables (global for integration)
let scene, camera, renderer, controls, model, mixer;
let gltfLoader, textureLoader, rgbeLoader, pmremGenerator;
let raycaster, mouse;

// State management with Alpine stores
document.addEventListener("alpine:init", () => {
  // Main designer store - central state management
  Alpine.store("designer", {
    // Loading states
    isLoading: true,
    loadingStates: {
      model: false,
      design: false,
      fonts: false,
    },

    // 3D Scene state
    currentLayer: "Front",
    layers: {},
    decals: [],
    selectedDecal: null,

    // Product data
    product: null,

    // UI state

    // Design data
    designName: "Untitled Design",
    designId: null,

    // Initialization guard
    _initialized: false,

    // Methods
    init() {
      // Prevent multiple initialization
      if (this._initialized) {
        debugLog("Alpine Designer Store already initialized, skipping...");
        return;
      }

      debugLog("Alpine Designer Store initialized");
      debugLog("window.phpData:", window.phpData);
      debugLog("window.phpData.product:", window.phpData?.product);
      this.product = window.phpData?.product;
      this.designName = window.phpData?.designData?.name || "Untitled Design";
      this.designId = window.phpData?.designData?.id;

      // Initialize with default layer if no product yet
      if (!this.product) {
        this.layers["Front"] = {
          name: "Front",
          color: "ffffff",
          material: "none",
          decals: [],
        };
        this.currentLayer = "Front";
      }

      // Set design loading state immediately (no design to load or already loaded)
      if (!window.phpData?.designData) {
        this.setLoadingState("design", true);
        debugLog("No design data to load, marking design as loaded");
      }

      this.initThreeJS();
      this._initialized = true;

      // Quick test fallback: Hide loading after 5 seconds for testing
      setTimeout(() => {
        if (this.isLoading) {
          debugWarn(
            "5 second timeout reached, forcing loading overlay to hide"
          );
          this.hideLoading();
        }
      }, 5000);

      // Ultimate fallback: Hide loading after 10 seconds maximum
      setTimeout(() => {
        if (this.isLoading) {
          debugWarn("Loading timeout reached, forcing loading overlay to hide");
          this.hideLoading();
        }
      }, 10000);
    },

    // Loading management
    setLoadingState(type, loaded) {
      debugLog(`Setting loading state: ${type} = ${loaded}`);
      this.loadingStates[type] = loaded;
      debugLog("Current loading states:", this.loadingStates);

      if (
        this.loadingStates.model &&
        this.loadingStates.design &&
        this.loadingStates.fonts
      ) {
        this.isLoading = false;
        debugLog("✅ All components loaded - hiding loading overlay");
      }
    },

    // Force hide loading overlay (fallback method)
    hideLoading() {
      this.isLoading = false;
      debugLog("Loading overlay force hidden");
    },

    // Layer management
    setCurrentLayer(layerId) {
      if (this.layers[layerId]) {
        this.currentLayer = layerId;
        this.selectedDecal = null;
        this.renderLayer();
        debugLog(`Switched to layer: ${layerId}`);
      }
    },

    getCurrentLayerData() {
      const layer = this.layers[this.currentLayer] || {};
      return {
        color: "ffffff",
        material: "none",
        decals: [],
        ...layer,
      };
    },

    // Color management
    setLayerColor(color) {
      if (this.layers[this.currentLayer]) {
        this.layers[this.currentLayer].color = color.replace("#", "");
        this.renderLayer();
      }
    },

    copyColorToLayer(targetLayerId) {
      const currentLayer = this.layers[this.currentLayer];
      const targetLayer = this.layers[targetLayerId];
      
      // Check if target layer can change color (default to true if not specified)
      if (currentLayer && targetLayer && targetLayer.settings?.canChangeColor !== false) {
        targetLayer.color = currentLayer.color;
        
        // Update the mesh material color if layer is loaded
        if (targetLayer.mesh && targetLayer.mesh.material) {
          const color = new THREE.Color("#" + targetLayer.color);
          targetLayer.mesh.material.color = color;
          targetLayer.mesh.material.needsUpdate = true;
        }
        
        debugLog(`Copied color #${currentLayer.color} to layer ${targetLayerId}`);
        
        // If we switch to the target layer, trigger a re-render
        if (this.currentLayer === targetLayerId) {
          this.renderLayer();
        }
      }
    },

    copyColorToAllLayers() {
      const currentLayer = this.layers[this.currentLayer];
      if (!currentLayer) return;
      
      const currentColor = currentLayer.color;
      let copiedCount = 0;
      
      Object.keys(this.layers).forEach(layerId => {
        if (layerId !== this.currentLayer) {
          const layer = this.layers[layerId];
          // Check if layer can change color (default to true if not specified)
          if (layer.settings?.canChangeColor !== false) {
            layer.color = currentColor;
            copiedCount++;
            
            // Update the mesh material color if layer is loaded
            if (layer.mesh && layer.mesh.material) {
              const color = new THREE.Color("#" + currentColor);
              layer.mesh.material.color = color;
              layer.mesh.material.needsUpdate = true;
            }
          }
        }
      });
      
      debugLog(`Copied color #${currentColor} to ${copiedCount} layers`);
    },

    // Material management
    setLayerMaterial(materialKey) {
      const currentLayer = this.layers[this.currentLayer];
      if (!currentLayer) return;

      // Apply to current layer
      currentLayer.material = materialKey;
      this.applyBumpmapToLayer(currentLayer, materialKey);

      // Apply to linked meshes if they exist
      const meshSettings = currentLayer.settings;
      if (meshSettings?.linkedBumpmaps) {
        meshSettings.linkedBumpmaps.forEach((linkedMeshName) => {
          const linkedLayer = this.layers[linkedMeshName];
          if (linkedLayer) {
            linkedLayer.material = materialKey;
            this.applyBumpmapToLayer(linkedLayer, materialKey);
            debugLog(`Applied linked bumpmap to layer ${linkedMeshName}`);
          }
        });
      }

      this.renderLayer();
    },

    // Apply bumpmap texture to a layer
    applyBumpmapToLayer(layer, materialKey) {
      if (!layer || !layer.mesh) return;

      const bumpmaps = window.phpData?.bumpmaps || {};
      const bumpmap = bumpmaps[materialKey];

      // Handle "none" material (remove texture)
      if (materialKey === "none" || !bumpmap?.link) {
        layer.mesh.material.bumpMap = null;
        layer.mesh.material.bumpScale = 1;
        layer.mesh.material.roughness = 1;
        layer.mesh.material.metalness = 0;
        layer.mesh.material.needsUpdate = true;

        layer.material = materialKey;
        layer.roughness = 1;
        layer.metalness = 0;

        debugLog(`Removed bumpmap from layer: ${layer.name}`);
        return;
      }

      // Load and apply the bumpmap texture
      debugLog(`Loading bumpmap for layer ${layer.name}:`, bumpmap.link);

      textureLoader.load(
        bumpmap.link,
        (texture) => {
          // Configure texture
          texture.wrapS = THREE.RepeatWrapping;
          texture.wrapT = THREE.RepeatWrapping;

          // Apply texture and material properties (matching PHP version)
          layer.mesh.material.bumpMap = texture;
          // Use scale for bumpScale (not bumpmap.bumpScale)
          layer.mesh.material.bumpScale = bumpmap.scale || 1;
          layer.mesh.material.metalness = bumpmap.metalness || 0;
          layer.mesh.material.roughness = bumpmap.roughness || 1;

          // Set repeat after assigning bumpMap (matching PHP version)
          const size = bumpmap.size || 1;
          layer.mesh.material.bumpMap.repeat.set(size, size);

          layer.mesh.material.needsUpdate = true;

          // Update layer properties
          layer.material = materialKey;
          layer.roughness =
            bumpmap.roughness !== undefined ? bumpmap.roughness : 1;
          layer.metalness =
            bumpmap.metalness !== undefined ? bumpmap.metalness : 0;

          debugLog(`Applied bumpmap to layer ${layer.name}:`, {
            key: materialKey,
            scale: bumpmap.scale,
            size: size,
            roughness: layer.roughness,
            metalness: layer.metalness,
          });
        },
        undefined,
        (error) => {
          debugError("Error loading bumpmap texture:", bumpmap.link, error);
        }
      );
    },

    // Decal management
    addDecal(type, data) {
      const decal = {
        id: Date.now() + Math.random(),
        type: type,
        layer: this.currentLayer,
        x: 0.5,
        y: 0.5,
        width: 0.2,
        height: 0.2,
        rotation: 0,
        ...data,
      };

      if (!this.layers[this.currentLayer].decals) {
        this.layers[this.currentLayer].decals = [];
      }

      this.layers[this.currentLayer].decals.push(decal);
      this.selectedDecal = decal.id;
      this.renderLayer();
      debugLog("Added decal:", decal);
    },

    selectDecal(decalId) {
      this.selectedDecal = decalId;
    },

    deleteDecal(decalId) {
      const layer = this.layers[this.currentLayer];
      if (layer && layer.decals) {
        layer.decals = layer.decals.filter((d) => d.id !== decalId);
        if (this.selectedDecal === decalId) {
          this.selectedDecal = null;
        }
        this.renderLayer();
      }
    },

    // Design management
    saveDesign() {
      // Open the Bootstrap save design modal
      debugLog("Opening save design modal");
      const modal = new bootstrap.Modal(document.getElementById('saveDesignModal'));
      modal.show();
    },

    clearDesign() {
      Object.keys(this.layers).forEach((layerId) => {
        this.layers[layerId].decals = [];
        this.layers[layerId].color = "ffffff";
        this.layers[layerId].material = "none";
      });
      this.selectedDecal = null;
      this.renderLayer();
      debugLog("Design cleared");
    },

    // Three.js integration
    async initThreeJS() {
      debugLog("Initializing Three.js...");
      await this.waitForThreeJS();
      this.setupThreeJS();
      await this.loadModel();
      this.loadFonts();
    },

    waitForThreeJS() {
      return new Promise((resolve) => {
        const checkReady = () => {
          if (
            typeof THREE !== "undefined" &&
            THREE.GLTFLoader &&
            THREE.OrbitControls &&
            THREE.RGBELoader
          ) {
            resolve();
          } else {
            setTimeout(checkReady, 100);
          }
        };
        checkReady();
      });
    },

    setupThreeJS() {
      // Clear any existing canvases first
      const container = document.getElementById("canvas-container");
      while (container.firstChild) {
        container.removeChild(container.firstChild);
      }

      // Scene setup
      scene = new THREE.Scene();
      scene.background = null; // Keep transparent for CSS backgrounds (matching vanilla designer.js)
      camera = new THREE.PerspectiveCamera(
        75,
        container.clientWidth / container.clientHeight,
        0.1,
        1000
      );
      renderer = new THREE.WebGLRenderer({
        antialias: true,
        preserveDrawingBuffer: true,
        powerPreference: "high-performance",
        alpha: true,
      });

      renderer.setSize(container.clientWidth, container.clientHeight);
      // Ensure canvas fills container
      renderer.domElement.style.display = "block";
      renderer.domElement.style.width = "100%";
      renderer.domElement.style.height = "100%";

      // Set transparent background (matching vanilla designer.js)
      renderer.setClearColor(0x000000, 0); // Black with 0 alpha (transparent)
      renderer.setClearAlpha(0); // Ensure alpha is 0

      // Force canvas to be transparent
      renderer.domElement.style.background = "transparent";
      renderer.domElement.style.backgroundColor = "transparent";

      // Enhanced antialiasing and quality settings
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2)); // Cap at 2x for performance

      // Shadow mapping disabled since we're using environment lighting only (matching vanilla designer.js)
      renderer.shadowMap.enabled = false;

      // Match vanilla designer.js encoding and tone mapping exactly
      renderer.outputEncoding = THREE.LinearEncoding;
      renderer.toneMapping = THREE.ACESFilmicToneMapping;
      renderer.toneMappingExposure = 1;
      container.appendChild(renderer.domElement);

      // Controls (matching vanilla designer.js configuration)
      controls = new THREE.OrbitControls(camera, renderer.domElement);
      controls.enableDamping = true;
      controls.dampingFactor = 0.05;
      controls.enablePan = false;

      // Loaders
      gltfLoader = new THREE.GLTFLoader();
      textureLoader = new THREE.TextureLoader();
      rgbeLoader = new THREE.RGBELoader();

      // Create PMREM generator for environment maps
      pmremGenerator = new THREE.PMREMGenerator(renderer);
      pmremGenerator.compileEquirectangularShader();

      // No scene lighting - using only environment map from neutral.hdr for illumination (matching vanilla designer.js)

      // Load environment map
      this.loadEnvironmentMap();

      // Raycaster for mouse interactions
      raycaster = new THREE.Raycaster();
      mouse = new THREE.Vector2();

      // Mouse events - use right-click for layer selection
      renderer.domElement.addEventListener("contextmenu", (event) => {
        event.preventDefault(); // Prevent context menu from appearing
        this.onCanvasClick(event);
      });

      // Handle window resize
      window.addEventListener("resize", () => this.onWindowResize());

      // Call resize once to set initial size properly
      this.onWindowResize();

      // Render loop
      this.animate();

      debugLog("Three.js setup complete");
    },

    loadEnvironmentMap() {
      debugLog("Starting environment map load from /static/neutral.hdr");
      rgbeLoader.load(
        "/static/neutral.hdr",
        (texture) => {
          debugLog("Environment map texture loaded, processing...", texture);
          texture.mapping = THREE.EquirectangularReflectionMapping;

          // Generate environment map
          const envMap = pmremGenerator.fromEquirectangular(texture).texture;
          debugLog("Environment map generated:", envMap);

          // Set as scene environment for reflections
          scene.environment = envMap;
          debugLog("Scene environment set");

          texture.dispose();
          pmremGenerator.dispose();
          debugLog("Environment map loaded and applied successfully");
        },
        (progress) => {
          debugLog("Loading environment map progress:", progress);
        },
        (error) => {
          debugError("Error loading environment map:", error);
          debugError("Environment map path: /static/neutral.hdr");
          // Continue without environment map
        }
      );
    },

    async loadModel() {
      if (!this.product?.modelLink) {
        debugWarn("No model link found, keeping default layers");

        // If no model, ensure we have at least one default layer
        if (Object.keys(this.layers).length === 0) {
          this.layers["Front"] = {
            name: "Front",
            mesh: null,
            color: "ffffff",
            material: "none",
            decals: [],
            settings: {},
            minX: 0,
            maxX: 1,
            minY: 0,
            maxY: 1,
          };
          this.currentLayer = "Front";
          debugLog("Created default Front layer since no model available");
        }

        debugLog("Current layers:", Object.keys(this.layers));
        this.setLoadingState("model", true);
        return;
      }

      debugLog("Starting model load from:", this.product.modelLink);

      try {
        const gltf = await new Promise((resolve, reject) => {
          gltfLoader.load(
            this.product.modelLink,
            (loadedGltf) => {
              debugLog("GLTF loaded successfully:", loadedGltf);
              resolve(loadedGltf);
            },
            (progress) => {
              debugLog("Model loading progress:", progress);
            },
            (error) => {
              debugError("Error loading GLTF:", error);
              reject(error);
            }
          );
        });

        model = gltf.scene;
        debugLog("Model scene extracted:", model);
        scene.add(model);
        debugLog("Model added to scene");

        // Initialize layers from model
        this.initializeLayers(model);

        // Position camera using the shared fitCameraToModel function
        this.fitCameraToModel();

        this.setLoadingState("model", true);
        debugLog("Model loaded successfully");
      } catch (error) {
        debugError("Error loading model:", error);
        this.setLoadingState("model", true); // Continue anyway
      }
    },

    initializeLayers(model) {
      debugLog("initializeLayers called with model:", model);

      if (!model) {
        debugError("No model provided to initializeLayers!");
        return;
      }

      const meshSettings = this.product?.meshSettings || {};
      const hasProduct = this.product && Object.keys(meshSettings).length > 0;

      // Clear existing layers only if we have product data
      if (hasProduct) {
        this.layers = {};
      }

      let layersCreated = false;
      let childCount = 0;
      let meshCount = 0;

      console.log(model);

      model.traverse((child) => {
        childCount++;
        if (child.isMesh) {
          meshCount++;
          debugLog(
            `Found mesh #${meshCount}:`,
            child.name,
            "Type:",
            child.type
          );

          if (!child.name.includes("polySurface")) {
            debugLog("Processing mesh:", child.name);

            // Clone material to avoid sharing
            child.material = child.material.clone();
            child.material.metalness = 0;
            child.material.roughness = 1;

            if (hasProduct && meshSettings[child.name]) {
              // Use product-specific settings
              const settings = meshSettings[child.name];

              this.layers[child.name] = {
                name: child.name,
                mesh: child,
                color: settings.initialColor || "ffffff",
                material: this.product?.initialBumpmap || "none",
                decals: [],
                settings: settings,
                minX: settings.minX || 0,
                maxX: settings.maxX || 1,
                minY: settings.minY || 0,
                maxY: settings.maxY || 1,
              };

              // Set initial color
              if (settings.initialColor) {
                child.material.color.setHex(
                  parseInt(settings.initialColor, 16)
                );
              }

              // Apply initial bumpmap if specified and allowed
              if (
                settings.canChangeBumpmap &&
                this.product?.initialBumpmap &&
                this.product.initialBumpmap !== "none"
              ) {
                this.applyBumpmapToLayer(
                  this.layers[child.name],
                  this.product.initialBumpmap
                );
                debugLog(
                  `Applied initial bumpmap '${this.product.initialBumpmap}' to layer ${child.name}`
                );
              }

              layersCreated = true;
            } else if (!hasProduct) {
              // Create generic layers for all meshes when no product data
              debugLog(`No mesh settings found for layer`);
            }
          }
        }
      });

      debugLog(
        `Traverse complete. Examined ${childCount} children, found ${meshCount} meshes`
      );

      // Set initial layer
      const initialLayer =
        this.product?.initialLayer || Object.keys(this.layers)[0];
      if (initialLayer && this.layers[initialLayer]) {
        this.currentLayer = initialLayer;
      }

      debugLog("Layers initialized:", Object.keys(this.layers));
    },

    renderLayer() {
      const layer = this.layers[this.currentLayer];
      if (!layer || !layer.mesh) return;

      // Update color
      const colorHex = parseInt(layer.color, 16);
      layer.mesh.material.color.setHex(colorHex);

      // Update material/texture
      // TODO: Implement material switching

      // Render decals
      // TODO: Implement decal rendering

      debugLog(`Rendered layer: ${this.currentLayer}`);
    },

    async loadFonts() {
      try {
        if (window.phpData?.fonts) {
          // Font loading logic here
          debugLog("Fonts loaded");
        }
        this.setLoadingState("fonts", true);
      } catch (error) {
        debugError("Font loading failed:", error);
        this.setLoadingState("fonts", true); // Continue anyway
      }
    },

    animate() {
      requestAnimationFrame(() => this.animate());

      if (controls) controls.update();
      if (renderer && scene && camera) {
        renderer.render(scene, camera);
      }
    },

    onCanvasClick(event) {
      const rect = renderer.domElement.getBoundingClientRect();
      mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      raycaster.setFromCamera(mouse, camera);

      // Check for layer intersections
      const meshes = Object.values(this.layers)
        .map((layer) => layer.mesh)
        .filter(Boolean);
      const intersects = raycaster.intersectObjects(meshes);

      if (intersects.length > 0) {
        const clickedLayer = Object.keys(this.layers).find(
          (layerId) => this.layers[layerId].mesh === intersects[0].object
        );

        if (clickedLayer && clickedLayer !== this.currentLayer) {
          this.setCurrentLayer(clickedLayer);
        }
      }
    },

    // Handle window resize
    onWindowResize() {
      const container = document.getElementById("canvas-container");
      if (!container || !camera || !renderer) return;

      const width = container.clientWidth;
      const height = container.clientHeight;

      // Update camera aspect ratio
      camera.aspect = width / height;
      camera.updateProjectionMatrix();

      // Update renderer size
      renderer.setSize(width, height);
      renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

      // Re-fit camera if model is loaded
      if (model && scene) {
        this.fitCameraToModel();
      }

      debugLog(`Canvas resized to ${width}x${height}`);
    },

    // Fit camera to model (extracted for reuse)
    fitCameraToModel() {
      if (!model || !camera || !controls) return;

      const box = new THREE.Box3().setFromObject(model);
      const size = box.getSize(new THREE.Vector3());
      const center = box.getCenter(new THREE.Vector3());

      // Get the max dimension considering aspect ratio
      const container = document.getElementById("canvas-container");
      const aspect = container.clientWidth / container.clientHeight;

      // Calculate the dimension that matters based on aspect ratio
      const horizontalFOV =
        2 * Math.atan(Math.tan((camera.fov * Math.PI) / 360) * aspect);
      const verticalFOV = (camera.fov * Math.PI) / 180;

      // Determine limiting dimension
      const horizontalDistance = size.x / (2 * Math.tan(horizontalFOV / 2));
      const verticalDistance = size.y / (2 * Math.tan(verticalFOV / 2));
      const depthDistance = size.z * 0.5;

      // Use the largest required distance with a small margin
      const distance =
        Math.max(horizontalDistance, verticalDistance, depthDistance) * 1.5;

      // Position camera at the front
      camera.position.set(center.x, center.y, center.z + distance);

      // Set controls target to center
      controls.target.copy(center);
      controls.update();

      // Set zoom limits based on model size
      controls.minDistance = distance * 0.5;
      controls.maxDistance = distance * 3;

      debugLog("Camera fitted to model");
    },

    // Camera controls
    rotateView(direction) {
      if (!controls || !model) return;

      const box = new THREE.Box3().setFromObject(model);
      const center = box.getCenter(new THREE.Vector3());
      const size = box.getSize(new THREE.Vector3());
      
      // Get the max dimension considering aspect ratio (same as fitCameraToModel)
      const container = document.getElementById("canvas-container");
      const aspect = container.clientWidth / container.clientHeight;
      
      // Calculate the dimension that matters based on aspect ratio
      const horizontalFOV =
        2 * Math.atan(Math.tan((camera.fov * Math.PI) / 360) * aspect);
      const verticalFOV = (camera.fov * Math.PI) / 180;
      
      // Determine limiting dimension
      const horizontalDistance = size.x / (2 * Math.tan(horizontalFOV / 2));
      const verticalDistance = size.y / (2 * Math.tan(verticalFOV / 2));
      const depthDistance = size.z * 0.5;
      
      // Use the largest required distance with a small margin
      const distance =
        Math.max(horizontalDistance, verticalDistance, depthDistance) * 1.5;

      switch (direction) {
        case "front":
          camera.position.set(center.x, center.y, center.z + distance);
          break;
        case "back":
          camera.position.set(center.x, center.y, center.z - distance);
          break;
        case "left":
          camera.position.set(center.x - distance, center.y, center.z);
          break;
        case "right":
          camera.position.set(center.x + distance, center.y, center.z);
          break;
      }

      controls.target.copy(center);
      controls.update();
      
      // Set zoom limits based on model size (same as fitCameraToModel)
      controls.minDistance = distance * 0.5;
      controls.maxDistance = distance * 3;
    },

    rotateCamera(direction) {
      if (!controls) return;

      const rotationAmount = Math.PI / 6; // 30 degrees (matching vanilla designer.js)
      const currentPosition = camera.position.clone();
      const target = controls.target.clone();

      // Rotate around target
      currentPosition.sub(target);

      if (direction === "left") {
        currentPosition.applyAxisAngle(
          new THREE.Vector3(0, 1, 0),
          rotationAmount
        );
      } else {
        currentPosition.applyAxisAngle(
          new THREE.Vector3(0, 1, 0),
          -rotationAmount
        );
      }

      currentPosition.add(target);
      camera.position.copy(currentPosition);
      controls.update();
    },

    zoomCamera(direction) {
      if (!controls || !camera) return;

      const zoomFactor = 0.1;
      const offset = new THREE.Vector3();

      offset.copy(camera.position).sub(controls.target);

      if (direction === "in") {
        offset.multiplyScalar(1 - zoomFactor);
      } else if (direction === "out") {
        offset.multiplyScalar(1 + zoomFactor);
      }

      // Respect distance limits (matching vanilla designer.js)
      const distance = offset.length();
      if (
        distance >= controls.minDistance &&
        distance <= controls.maxDistance
      ) {
        camera.position.copy(controls.target).add(offset);
        controls.update();
      }
    },

    // Background management
    setBackground(backgroundId) {
      debugLog('setBackground called with:', backgroundId);
      const container = document.getElementById('canvas-container');
      
      if (!container) {
        debugError('Canvas container not found!');
        return;
      }
      
      if (backgroundId === null) {
        debugLog('Removing background');
        // Remove background
        container.style.backgroundImage = '';
        container.style.backgroundColor = '';
        return;
      }
      
      // Find the background
      const backgrounds = window.phpData?.brandBackgrounds || [];
      const background = backgrounds.find(bg => bg.id === backgroundId);
      
      if (!background) {
        debugError('Background not found for ID:', backgroundId);
        return;
      }
      
      // Set background image
      const imageUrl = background.image_url;
      debugLog('Setting background image:', imageUrl);
      container.style.backgroundImage = `url('${imageUrl}')`;
      container.style.backgroundSize = 'cover';
      container.style.backgroundPosition = 'center';
      container.style.backgroundRepeat = 'no-repeat';
      debugLog('Background applied successfully');
    },

    // Design name management
    saveDesignName() {
      debugLog('Saving design name:', this.designName);
      // TODO: Implement actual saving to backend if needed
      debugLog('Design name updated successfully');
    },
  });

});

// Initialize when Alpine is ready
document.addEventListener("alpine:initialized", () => {
  debugLog("Alpine Designer initialized");
  Alpine.store("designer").init();
});

// Global functions for compatibility with onclick handlers
window.rotateView = (direction) =>
  Alpine.store("designer").rotateView(direction);
window.rotateCamera = (direction) =>
  Alpine.store("designer").rotateCamera(direction);
window.zoomCamera = (direction) =>
  Alpine.store("designer").zoomCamera(direction);
window.openTutorials = () => window.open("/tutorials", "_blank");
window.saveDesign = () => Alpine.store("designer").saveDesign();
window.confirmClearDesign = () => {
  if (confirm("Are you sure you want to clear the design?")) {
    Alpine.store("designer").clearDesign();
  }
};
window.confirmExitDesigner = () => {
  if (confirm("Are you sure you want to exit the designer?")) {
    window.location.href = "/products/";
  }
};
window.editDesignName = () => {
  const modal = new bootstrap.Modal(document.getElementById('editDesignNameModal'));
  modal.show();
  // Focus the input after the modal opens
  setTimeout(() => {
    const input = document.getElementById('design-name-input');
    if (input) {
      input.focus();
      input.select();
    }
  }, 100);
};

window.setCurrentLayerColor = (color) =>
  Alpine.store("designer").setLayerColor(color);
window.setCurrentLayerColorFromHex = (hex) =>
  Alpine.store("designer").setLayerColor("#" + hex);
window.addImageDecal = () => {
  const modal = new bootstrap.Modal(document.getElementById('imageBankModal'));
  modal.show();
};
window.closeDropdownAndAddText = () =>
  Alpine.store("designer").addDecal("text", {
    text: "Sample Text",
    font: "Roboto",
    color: "000000",
  });
window.closeDropdownAndAddFade = () =>
  Alpine.store("designer").addDecal("fade", {});
window.openCartModal = () => {
  const modal = new bootstrap.Modal(document.getElementById('cartModalNew'));
  modal.show();
};
window.openTemplates = () => {
  const modal = new bootstrap.Modal(document.getElementById('templatesModal'));
  modal.show();
};

// Debug functions for console access
window.debugDesigner = () => {
  console.log("Designer Store:", Alpine.store("designer"));
  console.log("Loading States:", Alpine.store("designer").loadingStates);
  console.log("Is Loading:", Alpine.store("designer").isLoading);
  console.log("Current Layer:", Alpine.store("designer").currentLayer);
  console.log("Layers:", Alpine.store("designer").layers);
};
window.hideLoading = () => Alpine.store("designer").hideLoading();
window.testLoading = () => {
  const store = Alpine.store("designer");
  console.log("Testing loading states...");
  store.setLoadingState("model", true);
  store.setLoadingState("design", true);
  store.setLoadingState("fonts", true);
};
