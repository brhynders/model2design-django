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

// Reusable canvas elements for performance optimization
let textCanvas = null;
let fadeCanvas = null;

// State management with Alpine stores
document.addEventListener("alpine:init", () => {
  // Main designer store - central state management
  Alpine.store("designer", {
    // Loading states
    isLoading: true,
    isAddingImage: false,
    isSavingDesign: false,
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
    replacingDecalId: null,
    isDecalEditMode: false,

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
        // Exit decal edit mode when switching layers
        if (this.isDecalEditMode) {
          this.isDecalEditMode = false;
        }
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
      const layer = this.layers[this.currentLayer];
      if (layer) {
        layer.color = color.replace("#", "");

        // Directly update the mesh material color
        if (layer.mesh && layer.mesh.material) {
          const colorHex = parseInt(layer.color, 16);
          layer.mesh.material.color.setHex(colorHex);
          layer.mesh.material.needsUpdate = true;
        }
      }
    },

    copyColorToLayer(targetLayerId) {
      const currentLayer = this.layers[this.currentLayer];
      const targetLayer = this.layers[targetLayerId];

      // Check if target layer can change color (default to true if not specified)
      if (
        currentLayer &&
        targetLayer &&
        targetLayer.settings?.canChangeColor !== false
      ) {
        targetLayer.color = currentLayer.color;

        // Update the mesh material color if layer is loaded
        if (targetLayer.mesh && targetLayer.mesh.material) {
          const color = new THREE.Color("#" + targetLayer.color);
          targetLayer.mesh.material.color = color;
          targetLayer.mesh.material.needsUpdate = true;
        }

        debugLog(
          `Copied color #${currentLayer.color} to layer ${targetLayerId}`
        );
      }
    },

    copyColorToAllLayers() {
      const currentLayer = this.layers[this.currentLayer];
      if (!currentLayer) return;

      const currentColor = currentLayer.color;
      let copiedCount = 0;

      Object.keys(this.layers).forEach((layerId) => {
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

    // Generate unique ID for decals
    generateId() {
      return (
        "decal_" + Date.now() + "_" + Math.random().toString(36).slice(2, 11)
      );
    },

    // Check if max decals limit reached (14 decals per layer)
    isMaxDecalsReached() {
      const layer = this.layers[this.currentLayer];
      return layer && layer.decals && layer.decals.length >= 14;
    },

    // Check if current layer can add decals
    canAddDecals() {
      const layer = this.layers[this.currentLayer];
      return layer && layer.settings && layer.settings.canAddImages;
    },

    // Add image decal - opens image bank modal
    addImageDecal() {
      if (!this.currentLayer) {
        alert("Please select a layer first");
        return;
      }

      // Check if current layer can add images
      if (!this.canAddDecals()) {
        alert("This layer does not support adding designs");
        return;
      }

      // Check if max decals limit reached
      if (this.isMaxDecalsReached()) {
        alert(
          `Maximum elements reached for ${this.currentLayer}. You can have up to 14 elements per layer.`
        );
        return;
      }

      // Open image bank modal
      const imageModal = new bootstrap.Modal(
        document.getElementById("imageBankModal")
      );
      imageModal.show();
      debugLog("Image bank modal opened for adding decal");
    },

    // Add text decal with default settings
    addTextDecal() {
      if (!this.currentLayer) {
        alert("Please select a layer first");
        return;
      }

      // Check if current layer can add images
      if (!this.canAddDecals()) {
        alert("This layer does not support adding designs");
        return;
      }

      // Check if max decals limit reached
      if (this.isMaxDecalsReached()) {
        alert(
          `Maximum elements reached for ${this.currentLayer}. You can have up to 14 elements per layer.`
        );
        return;
      }

      // Default text values
      const text = "Sample Text";
      const font = "Roboto";
      const color = "#000000";
      const letterSpacing = 0;
      const borderWidth = 0;
      const borderColor = "#000000";

      // Create text texture
      const texture = this.createTextTexture(
        text,
        font,
        color,
        letterSpacing,
        borderWidth,
        borderColor
      );

      // Create text decal with default values
      const decal = {
        id: this.generateId(),
        name: text,
        type: "text",
        text: text,
        font: font,
        color: color,
        letterSpacing: letterSpacing,
        borderWidth: borderWidth,
        borderColor: borderColor,
        texture: texture,
        position: { x: 0.5, y: 0.5 },
        size: { x: 0.4, y: 0.2 },
        rotation: 0,
        opacity: 1,
        flipX: false,
        flipY: false,
        aspectLocked: true,
        isLoadingFont: true, // Flag to indicate font is still loading
        textData: {
          text: text,
          font: font,
          color: color,
          letterSpacing: letterSpacing,
          borderWidth: borderWidth,
          borderColor: borderColor,
        },
      };

      // Add to current layer
      if (!this.layers[this.currentLayer].decals) {
        this.layers[this.currentLayer].decals = [];
      }

      this.layers[this.currentLayer].decals.push(decal);
      this.selectedDecal = decal.id;
      this.renderLayer();
      debugLog("Text decal added:", decal);
    },

    // Add fade decal with default settings
    addFadeDecal() {
      if (!this.currentLayer) {
        alert("Please select a layer first");
        return;
      }

      // Check if current layer can add images
      if (!this.canAddDecals()) {
        alert("This layer does not support adding designs");
        return;
      }

      // Check if max decals limit reached
      if (this.isMaxDecalsReached()) {
        alert(
          `Maximum elements reached for ${this.currentLayer}. You can have up to 14 elements per layer.`
        );
        return;
      }

      // Default fade settings
      const fadeData = {
        baseColor: "#000000",
        blendColor: "#ffffff",
        fadeStart: 0.4,
        mixRatio: 0.5,
        direction: "Vertical",
      };

      // Create fade texture
      const texture = this.createFadeTexture(fadeData);

      const decal = {
        id: this.generateId(),
        name: "Fade Effect",
        type: "fade",
        texture: texture,
        position: { x: 0.5, y: 0.5 },
        size: { x: 1.2, y: 1.2 },
        rotation: 0,
        opacity: 0.7,
        flipX: false,
        flipY: false,
        aspectLocked: true,
        fadeData: fadeData,
      };

      // Add to current layer (insert at beginning for fade effects)
      if (!this.layers[this.currentLayer].decals) {
        this.layers[this.currentLayer].decals = [];
      }

      this.layers[this.currentLayer].decals.unshift(decal);
      this.selectedDecal = decal.id;
      this.renderLayer();
      debugLog("Fade decal added:", decal);
    },

    // Create image decal from selected image (called from image bank)
    createImageDecalFromUrl(imageUrl, imageName, isPattern = false) {
      // Check if max decals limit reached
      if (this.isMaxDecalsReached()) {
        alert(
          `Maximum elements reached for ${this.currentLayer}. You can have up to 14 elements per layer.`
        );
        return;
      }

      // Use Three.js TextureLoader
      if (!textureLoader) {
        debugError("TextureLoader not initialized");
        return;
      }

      // Show loading state
      this.isAddingImage = true;
      debugLog("Loading texture from:", imageUrl);

      textureLoader.load(
        imageUrl,
        (texture) => {
          // Success - texture loaded
          // Apply optimal texture settings
          this.applyTextureSettings(texture);

          // Determine size based on pattern category
          const size = isPattern ? { x: 1, y: 1 } : { x: 0.3, y: 0.3 };

          const decal = {
            id: this.generateId(),
            name: imageName || "Image",
            type: "image",
            texture: texture,
            imageUrl: imageUrl,
            position: { x: 0.5, y: 0.5 },
            size: size,
            rotation: 0,
            opacity: 1,
            flipX: false,
            flipY: false,
            aspectLocked: true,
          };

          // Add to current layer
          if (!this.layers[this.currentLayer].decals) {
            this.layers[this.currentLayer].decals = [];
          }

          this.layers[this.currentLayer].decals.push(decal);
          this.selectedDecal = decal.id;
          this.renderLayer();

          // Hide loading state
          this.isAddingImage = false;
          debugLog("Image decal added with texture:", decal);
        },
        (progress) => {
          // Progress callback (optional)
          debugLog("Loading texture progress:", progress);
        },
        (error) => {
          // Error callback
          debugError("Failed to load texture:", imageUrl, error);

          // Hide loading state
          this.isAddingImage = false;
          alert("Failed to load image. Please try again.");
        }
      );
    },

    // Apply optimal texture settings for decals
    applyTextureSettings(texture, isBumpMap = false) {
      texture.generateMipmaps = true;
      texture.anisotropy = Math.min(
        16,
        renderer ? renderer.capabilities.getMaxAnisotropy() : 16
      );
      texture.wrapS = texture.wrapT = THREE.RepeatWrapping;

      // Set flipY to false for all textures (decals and bumpmaps)
      texture.flipY = false;

      // Better filtering
      if (isBumpMap) {
        texture.minFilter = THREE.LinearMipMapLinearFilter;
        texture.magFilter = THREE.LinearFilter;
      } else {
        texture.minFilter = THREE.LinearMipMapLinearFilter;
        texture.magFilter = THREE.LinearFilter;
      }

      texture.needsUpdate = true;
    },

    // Create fade texture
    createFadeTexture({
      baseColor = "#000000",
      blendColor = "#ffffff",
      fadeStart = 0.4,
      mixRatio = 0.5,
      direction = "Vertical",
    }) {
      debugLog("Creating fade texture with options:", {
        baseColor,
        blendColor,
        fadeStart,
        mixRatio,
        direction,
      });

      // Create or reuse global fade canvas for performance
      if (!fadeCanvas) {
        fadeCanvas = document.createElement("canvas");
      }
      
      const canvas = fadeCanvas;
      canvas.width = 2048;
      canvas.height = 2048;
      const ctx = canvas.getContext("2d");

      // Clear canvas
      ctx.clearRect(0, 0, 2048, 2048);

      // Create the gradient
      let gradient;
      if (direction === "Vertical") {
        gradient = ctx.createLinearGradient(0, 0, 0, 2048);
      } else {
        gradient = ctx.createLinearGradient(0, 0, 2048, 0);
      }

      // Calculate blended color based on mixRatio
      const blendedColor = this.blendColors(baseColor, blendColor, mixRatio);

      // Add color stops
      gradient.addColorStop(fadeStart, baseColor);
      gradient.addColorStop(1, blendedColor);

      // Fill with gradient
      ctx.fillStyle = gradient;
      ctx.fillRect(0, 0, 2048, 2048);

      // Create texture from canvas
      const texture = new THREE.CanvasTexture(canvas);

      // Apply the same texture settings as image textures
      this.applyTextureSettings(texture, false);

      return texture;
    },

    // Blend two colors
    blendColors(baseColor, blendColor, mixRatio) {
      // Convert hex to RGB
      const hexToRgb = (hex) => {
        const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
        return result
          ? {
              r: parseInt(result[1], 16),
              g: parseInt(result[2], 16),
              b: parseInt(result[3], 16),
            }
          : null;
      };

      // Convert RGB to hex
      const rgbToHex = (r, g, b) => {
        return (
          "#" + ((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)
        );
      };

      const base = hexToRgb(baseColor);
      const blend = hexToRgb(blendColor);

      if (!base || !blend) {
        console.warn("Invalid color format in blendColors");
        return baseColor;
      }

      // Mix colors based on ratio
      const r = Math.round(base.r * (1 - mixRatio) + blend.r * mixRatio);
      const g = Math.round(base.g * (1 - mixRatio) + blend.g * mixRatio);
      const b = Math.round(base.b * (1 - mixRatio) + blend.b * mixRatio);

      return rgbToHex(r, g, b);
    },

    // Create text texture
    createTextTexture(
      text,
      font,
      color,
      letterSpacing = 0,
      borderWidth = 0,
      borderColor = "#000000"
    ) {
      // Create or reuse global text canvas for performance
      if (!textCanvas) {
        textCanvas = document.createElement("canvas");
      }
      
      const canvas = textCanvas;
      const canvasSize = 2048;
      canvas.width = canvasSize;
      canvas.height = canvasSize;

      const ctx = canvas.getContext("2d");
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Use placeholder font for now (will be updated when fonts are loaded)
      const fontSize = 200;
      ctx.font = `${fontSize}px ${font}, Arial, sans-serif`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";

      const centerX = canvas.width / 2;
      const centerY = canvas.height / 2;

      // Apply letter spacing if needed
      if (letterSpacing !== 0) {
        // Draw text with letter spacing character by character
        const chars = text.split('');
        const totalExtraSpacing = letterSpacing * (chars.length - 1);
        
        // Measure the text without letter spacing
        const metrics = ctx.measureText(text);
        const textWidth = metrics.width;
        
        // Calculate starting position to keep text centered
        let currentX = centerX - (textWidth + totalExtraSpacing) / 2;
        
        // Draw each character with spacing
        chars.forEach((char, index) => {
          const charMetrics = ctx.measureText(char);
          const charWidth = charMetrics.width;
          
          // Draw border if specified
          if (borderWidth > 0) {
            ctx.strokeStyle = borderColor;
            ctx.lineWidth = borderWidth * 2;
            ctx.strokeText(char, currentX + charWidth / 2, centerY);
          }
          
          // Draw character
          ctx.fillStyle = color;
          ctx.fillText(char, currentX + charWidth / 2, centerY);
          
          // Move to next character position
          currentX += charWidth + letterSpacing;
        });
      } else {
        // Draw text normally without letter spacing
        // Draw border if specified
        if (borderWidth > 0) {
          ctx.strokeStyle = borderColor;
          ctx.lineWidth = borderWidth * 2;
          ctx.strokeText(text, centerX, centerY);
        }

        // Draw text
        ctx.fillStyle = color;
        ctx.fillText(text, centerX, centerY);
      }

      const texture = new THREE.CanvasTexture(canvas);

      // Apply the same texture settings as image textures
      this.applyTextureSettings(texture, false);

      return texture;
    },

    selectDecal(decalId) {
      this.selectedDecal = decalId;
    },

    enterDecalEditMode(decalId) {
      this.selectedDecal = decalId;
      this.isDecalEditMode = true;
      debugLog("Entered decal edit mode for decal:", decalId);
    },

    exitDecalEditMode() {
      this.isDecalEditMode = false;
      this.selectedDecal = null;
      debugLog("Exited decal edit mode");
    },

    getSelectedDecal() {
      if (!this.selectedDecal || !this.currentLayer) return null;
      const layer = this.layers[this.currentLayer];
      if (!layer || !layer.decals) return null;
      return layer.decals.find(d => d.id === this.selectedDecal);
    },

    updateDecalPosition(axis, value) {
      const decal = this.getSelectedDecal();
      if (!decal) return;
      
      decal.position[axis] = value;
      this.renderLayer();
    },

    updateDecalSize(value) {
      const decal = this.getSelectedDecal();
      if (!decal) return;
      
      // Maintain aspect ratio if needed
      const oldSize = decal.size.x;
      decal.size.x = value;
      
      if (decal.aspectLocked) {
        // Adjust Y size proportionally
        const ratio = decal.size.y / oldSize;
        decal.size.y = value * ratio;
      } else {
        decal.size.y = value;
      }
      
      this.renderLayer();
    },

    updateDecalRotation(value) {
      const decal = this.getSelectedDecal();
      if (!decal) return;
      
      decal.rotation = value;
      this.renderLayer();
    },

    updateDecalOpacity(value) {
      const decal = this.getSelectedDecal();
      if (!decal) return;
      
      decal.opacity = value;
      this.renderLayer();
    },

    toggleDecalFlip(axis) {
      const decal = this.getSelectedDecal();
      if (!decal) return;
      
      if (axis === 'x') {
        decal.flipX = !decal.flipX;
      } else if (axis === 'y') {
        decal.flipY = !decal.flipY;
      }
      
      this.renderLayer();
    },

    duplicateDecal(decalId) {
      if (!this.currentLayer) return;
      
      const layer = this.layers[this.currentLayer];
      const originalDecal = layer.decals.find(d => d.id === decalId);
      if (!originalDecal) return;

      // Check if max decals limit reached
      if (this.isMaxDecalsReached()) {
        alert(`Maximum elements reached for ${this.currentLayer}. You can have up to 14 elements per layer.`);
        return;
      }

      // Create a deep copy of the decal
      const newDecal = {
        ...originalDecal,
        id: this.generateId(),
        name: originalDecal.name + ' Copy',
        position: { ...originalDecal.position },
        size: { ...originalDecal.size }
      };

      layer.decals.push(newDecal);
      this.selectedDecal = newDecal.id;
      this.renderLayer();
      
      debugLog("Decal duplicated:", newDecal);
    },

    updateTextProperty(property, value) {
      const decal = this.getSelectedDecal();
      if (!decal || decal.type !== 'text') return;
      
      // Update the property
      decal[property] = value;
      
      // Update decal name when text changes
      if (property === 'text') {
        decal.name = value || 'Text Decal';
      }
      
      // Also update textData if it exists
      if (decal.textData) {
        decal.textData[property] = value;
      }
      
      // Recreate the text texture with new properties
      const newTexture = this.createTextTexture(
        decal.text,
        decal.font,
        decal.color,
        decal.letterSpacing || 0,
        decal.borderWidth || 0,
        decal.borderColor || '#000000'
      );
      
      // Dispose old texture
      if (decal.texture) {
        decal.texture.dispose();
      }
      
      decal.texture = newTexture;
      this.renderLayer();
      
      debugLog(`Updated text decal ${property}:`, value);
    },

    updateFadeProperty(property, value) {
      const decal = this.getSelectedDecal();
      if (!decal || decal.type !== 'fade') return;
      
      // Update the fade data
      if (!decal.fadeData) {
        decal.fadeData = {};
      }
      decal.fadeData[property] = value;
      
      // Recreate the fade texture with new properties
      const newTexture = this.createFadeTexture(decal.fadeData);
      
      // Dispose old texture
      if (decal.texture) {
        decal.texture.dispose();
      }
      
      decal.texture = newTexture;
      this.renderLayer();
      
      debugLog(`Updated fade decal ${property}:`, value);
    },

    replaceImageDecal() {
      const decal = this.getSelectedDecal();
      if (!decal || decal.type !== 'image') return;
      
      // Open image bank modal for replacement
      const imageModal = new bootstrap.Modal(document.getElementById('imageBankModal'));
      imageModal.show();
      
      // Store that we're replacing a decal
      this.replacingDecalId = decal.id;
      
      debugLog("Opening image bank to replace decal:", decal.id);
    },

    getAvailableLayers() {
      // Get all layers that can accept images (excluding current layer)
      const availableLayers = {};
      Object.keys(this.layers).forEach(layerName => {
        const layer = this.layers[layerName];
        if (layer.settings?.canAddImages && layerName !== this.currentLayer) {
          availableLayers[layerName] = layer;
        }
      });
      return availableLayers;
    },

    formatLayerName(layerName) {
      // Format layer name for display (e.g., "front_message" -> "Front Message")
      return layerName
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    },

    moveDecalToLayer(decalId, targetLayerName) {
      const currentLayerObj = this.layers[this.currentLayer];
      const targetLayer = this.layers[targetLayerName];
      
      if (!currentLayerObj || !targetLayer) {
        debugError("Invalid layers for move operation");
        return;
      }
      
      const decal = currentLayerObj.decals?.find(d => d.id === decalId);
      if (!decal) {
        debugError("Decal not found:", decalId);
        return;
      }
      
      // Check if target layer has reached max decals limit
      if (targetLayer.decals && targetLayer.decals.length >= 14) {
        alert(`Maximum elements reached for ${this.formatLayerName(targetLayerName)}. You can have up to 14 elements per layer.`);
        return;
      }
      
      // Remove from current layer
      currentLayerObj.decals = currentLayerObj.decals.filter(d => d.id !== decalId);
      
      // Add to target layer
      if (!targetLayer.decals) {
        targetLayer.decals = [];
      }
      targetLayer.decals.push(decal);
      
      // Exit decal edit mode and clear selection since decal is moved
      if (this.selectedDecal === decalId) {
        this.selectedDecal = null;
        this.isDecalEditMode = false;
      }
      
      // Re-render both layers
      this.renderLayer();
      const prevLayer = this.currentLayer;
      this.currentLayer = targetLayerName;
      this.renderLayer();
      this.currentLayer = prevLayer;
      
      debugLog(`Moved decal ${decalId} to ${targetLayerName}`);
    },

    copyDecalToLayer(decalId, targetLayerName) {
      const currentLayerObj = this.layers[this.currentLayer];
      const targetLayer = this.layers[targetLayerName];
      
      if (!currentLayerObj || !targetLayer) {
        debugError("Invalid layers for copy operation");
        return;
      }
      
      const decal = currentLayerObj.decals?.find(d => d.id === decalId);
      if (!decal) {
        debugError("Decal not found:", decalId);
        return;
      }
      
      // Check if target layer has reached max decals limit
      if (targetLayer.decals && targetLayer.decals.length >= 14) {
        alert(`Maximum elements reached for ${this.formatLayerName(targetLayerName)}. You can have up to 14 elements per layer.`);
        return;
      }
      
      // Create a copy of the decal with new ID
      const newDecal = {
        ...JSON.parse(JSON.stringify(decal)), // Deep clone
        id: this.generateId()
      };
      
      // If it's a texture-based decal, we need to copy the texture reference
      if (decal.texture) {
        newDecal.texture = decal.texture; // Share the same texture object
      }
      
      // Add to target layer
      if (!targetLayer.decals) {
        targetLayer.decals = [];
      }
      targetLayer.decals.push(newDecal);
      
      // Exit decal edit mode after copying for cleaner UX
      if (this.selectedDecal === decalId) {
        this.selectedDecal = null;
        this.isDecalEditMode = false;
      }
      
      // Re-render target layer
      const prevLayer = this.currentLayer;
      this.currentLayer = targetLayerName;
      this.renderLayer();
      this.currentLayer = prevLayer;
      
      debugLog(`Copied decal ${decalId} to ${targetLayerName}`);
    },

    copyDecalToAllLayers(decalId) {
      const currentLayerObj = this.layers[this.currentLayer];
      
      if (!currentLayerObj) {
        debugError("Current layer not found");
        return;
      }
      
      const decal = currentLayerObj.decals?.find(d => d.id === decalId);
      if (!decal) {
        debugError("Decal not found:", decalId);
        return;
      }
      
      const availableLayers = this.getAvailableLayers();
      const layerNames = Object.keys(availableLayers);
      
      if (layerNames.length === 0) {
        debugLog("No available layers to copy to");
        return;
      }
      
      let copiedCount = 0;
      let skippedLayers = [];
      
      // Copy to each available layer
      layerNames.forEach(layerName => {
        const targetLayer = availableLayers[layerName];
        
        // Check if target layer has reached max decals limit
        if (targetLayer.decals && targetLayer.decals.length >= 14) {
          skippedLayers.push(this.formatLayerName(layerName));
          return;
        }
        
        // Create a copy of the decal with new ID
        const newDecal = {
          ...JSON.parse(JSON.stringify(decal)), // Deep clone
          id: this.generateId()
        };
        
        // If it's a texture-based decal, we need to copy the texture reference
        if (decal.texture) {
          newDecal.texture = decal.texture; // Share the same texture object
        }
        
        // Add to target layer
        if (!targetLayer.decals) {
          targetLayer.decals = [];
        }
        targetLayer.decals.push(newDecal);
        copiedCount++;
      });
      
      // Always exit decal edit mode after copying to all layers for cleaner UX
      this.selectedDecal = null;
      this.isDecalEditMode = false;
      
      // Re-render all affected layers
      const prevLayer = this.currentLayer;
      layerNames.forEach(layerName => {
        this.currentLayer = layerName;
        this.renderLayer();
      });
      this.currentLayer = prevLayer;
      
      // Show feedback to user
      let message = `Copied to ${copiedCount} layer${copiedCount !== 1 ? 's' : ''}`;
      if (skippedLayers.length > 0) {
        message += `\n\nSkipped layers (14 element limit reached): ${skippedLayers.join(', ')}`;
      }
      
      if (copiedCount > 0) {
        // Use a brief toast-style message instead of alert for better UX
        console.log(message);
        debugLog(`Copied decal ${decalId} to ${copiedCount} layers`);
      }
      
      if (skippedLayers.length > 0 && copiedCount === 0) {
        alert(`Cannot copy to any layers. All available layers have reached the 14 element limit.`);
      }
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
      const modal = new bootstrap.Modal(
        document.getElementById("saveDesignModal")
      );
      modal.show();
    },

    clearDesign() {
      Object.keys(this.layers).forEach((layerId) => {
        const layer = this.layers[layerId];

        // Clear decals
        layer.decals = [];

        // Reset to initial color (or white as fallback)
        const initialColor = layer.settings?.initialColor || "ffffff";
        layer.color = initialColor;

        // Reset material to none
        layer.material = "none";

        // Directly update mesh material if it exists
        if (layer.mesh && layer.mesh.material) {
          // Update color
          const colorHex = parseInt(initialColor, 16);
          layer.mesh.material.color.setHex(colorHex);

          // Remove bumpmap material
          layer.mesh.material.bumpMap = null;
          layer.mesh.material.bumpScale = 1;
          layer.mesh.material.roughness = 1;
          layer.mesh.material.metalness = 0;
          layer.mesh.material.needsUpdate = true;
        }
      });

      this.selectedDecal = null;
      this.renderLayer(); // Only for decals
      debugLog("Design cleared");
    },

    updateDesignName(newName) {
      const trimmedName = newName ? newName.trim() : "";
      if (trimmedName) {
        this.designName = trimmedName;
        debugLog("Design name updated to:", trimmedName);

        // Update the design name display in the header
        const designNameSpan = document.querySelector(".design-header h5");
        if (designNameSpan) {
          designNameSpan.textContent = trimmedName;
        }
      }
    },

    async saveDesign() {
      try {
        // Show saving overlay
        this.isSavingDesign = true;
        
        // Get session ID for guest users
        const sessionId = this.getSessionId();
        
        // Prepare design data using Alpine.raw to avoid proxy issues
        const designData = {
          name: this.designName || 'Untitled Design',
          product: this.productId,
          data: Alpine.raw({
            layers: this.layers,
            currentLayer: this.currentLayer,
            productId: this.productId,
            designName: this.designName
          }),
          session_id: sessionId,
          public: false
        };

        // Get CSRF token
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value || 
                         document.querySelector('[name="csrfmiddlewaretoken"]')?.value ||
                         document.querySelector('meta[name="csrf-token"]')?.content ||
                         this.getCookie('csrftoken');
        
        debugLog("Saving design data:", designData);
        debugLog("CSRF token:", csrfToken);

        // Make POST request to save design
        const response = await fetch('/designer/save/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
          },
          body: JSON.stringify(designData)
        });

        const result = await response.json();
        
        if (!response.ok) {
          throw new Error(result.error || `HTTP error! status: ${response.status}`);
        }
        
        if (result.success) {
          debugLog("Design saved successfully:", result);
          alert(result.message || "Design saved successfully!");
        } else {
          throw new Error(result.error || 'Failed to save design');
        }

      } catch (error) {
        debugError("Failed to save design:", error);
        alert(`Failed to save design: ${error.message}`);
      } finally {
        // Hide saving overlay
        this.isSavingDesign = false;
      }
    },

    getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    },

    getSessionId() {
      // Get Django session ID from cookies
      const cookies = document.cookie.split(';');
      for (let cookie of cookies) {
        const [name, value] = cookie.trim().split('=');
        if (name === 'sessionid') {
          return value;
        }
      }
      // Fallback to a generated session ID if none exists
      return 'guest_' + Math.random().toString(36).substr(2, 9);
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
      textureLoader.crossOrigin = "anonymous"; // Fix CORS issues
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

    renderAllLayers() {
      Object.keys(this.layers).forEach((layerId) => {
        const layer = this.layers[layerId];
        // Only render layers that can have images/decals
        if (layer.settings?.canAddImages) {
          this.renderLayer(layerId);
        }
      });
      debugLog("Rendered all layers with canAddImages");
    },

    async loadFonts() {
      try {
        if (!window.phpData?.fonts) {
          debugLog("No fonts to load");
          this.setLoadingState("fonts", true);
          return;
        }

        debugLog("🔤 Loading fonts:", window.phpData.fonts);

        // Wait for document fonts to be ready first
        await document.fonts.ready;
        debugLog("✅ Document fonts ready");

        // Load each font family with multiple weights and sizes for caching
        const fontPromises = [];
        for (const font of window.phpData.fonts) {
          const sizes = [16, 24, 48, 72, 96, 144, 200];
          const weights = [400, 700];
          
          for (const size of sizes) {
            for (const weight of weights) {
              fontPromises.push(
                document.fonts.load(`${weight} ${size}px "${font}"`).catch(() => {
                  debugWarn(`Failed to load ${font} ${weight} ${size}px`);
                })
              );
            }
          }
        }

        // Wait for all font variants to load
        await Promise.all(fontPromises);
        debugLog(`✅ All fonts loaded successfully: ${window.phpData.fonts.length} families`);
        
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
      debugLog("setBackground called with:", backgroundId);
      const container = document.getElementById("canvas-container");

      if (!container) {
        debugError("Canvas container not found!");
        return;
      }

      if (backgroundId === null) {
        debugLog("Removing background");
        // Remove background
        container.style.backgroundImage = "";
        container.style.backgroundColor = "";
        return;
      }

      // Find the background
      const backgrounds = window.phpData?.brandBackgrounds || [];
      const background = backgrounds.find((bg) => bg.id === backgroundId);

      if (!background) {
        debugError("Background not found for ID:", backgroundId);
        return;
      }

      // Set background image
      const imageUrl = background.image_url;
      debugLog("Setting background image:", imageUrl);
      container.style.backgroundImage = `url('${imageUrl}')`;
      container.style.backgroundSize = "cover";
      container.style.backgroundPosition = "center";
      container.style.backgroundRepeat = "no-repeat";
      debugLog("Background applied successfully");
    },

    // Design name management
    saveDesignName() {
      debugLog("Saving design name:", this.designName);
      // TODO: Implement actual saving to backend if needed
      debugLog("Design name updated successfully");
    },

    generateSwitchCases(numDecals) {
      let switchCases = "";
      for (let i = 0; i < numDecals; i++) {
        switchCases += `
            case ${i}:
                texColor = texture2D(decalImages[${i}], uv);
                break;
        `;
      }
      return switchCases;
    },

    renderLayer(targetLayerId = null) {
      let selectedLayer = this.layers[this.currentLayer];
      if (targetLayerId) selectedLayer = this.layers[targetLayerId];
      const currentLayer = Alpine.raw(selectedLayer);
      console.log(currentLayer);

      const mesh = currentLayer.mesh;
      const allDecals = currentLayer.decals;

      // Filter out decals without textures
      const decals = allDecals.filter((d) => d.texture);

      debugLog(
        "Rendering layer with",
        decals.length,
        "decals using shader (filtered from",
        allDecals.length,
        "total)"
      );

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
        // Set Uniforms
        shader.uniforms.decalImages = { value: decals.map((d) => d.texture) };
        shader.uniforms.decalPositions = {
          value: decals.map(
            (d) => new THREE.Vector2(d.position.x, d.position.y)
          ),
        };
        shader.uniforms.decalRotations = {
          value: decals.map((d) => (d.rotation * Math.PI) / 180),
        };
        shader.uniforms.decalFlipXs = { value: decals.map((d) => d.flipX) };
        shader.uniforms.decalFlipYs = { value: decals.map((d) => d.flipY) };
        shader.uniforms.decalOpacities = {
          value: decals.map((d) => d.opacity),
        };
        shader.uniforms.decalSizes = {
          value: decals.map((d) => {
            if (
              d.aspectLocked &&
              d.texture &&
              d.texture.image &&
              d.texture.image.width &&
              d.texture.image.height
            ) {
              return new THREE.Vector2(
                d.size.x,
                d.size.x * (d.texture.image.height / d.texture.image.width) // Maintain aspect ratio of image
              );
            } else {
              return new THREE.Vector2(d.size.x, d.size.y);
            }
          }),
        };
        shader.uniforms.minX = { value: parseFloat(currentLayer.minX) };
        shader.uniforms.maxX = { value: parseFloat(currentLayer.maxX) };
        shader.uniforms.minY = { value: parseFloat(currentLayer.minY) };
        shader.uniforms.maxY = { value: parseFloat(currentLayer.maxY) };

        // Adjust Vertex Shader
        shader.vertexShader = `
        ${shader.vertexShader.replace("void main", "void originalMain")}
        varying vec2 vDecalUv;
        void main() {
            vDecalUv = uv;
            originalMain();
        }
        `;

        // Define uniforms/vars in global scope
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

                  vec2 rotatedUV = vDecalUv - decalPositions[i]; // Translate to origin
                  float c = cos(decalRotations[i]);
                  float s = sin(decalRotations[i]);
                  rotatedUV = vec2(
                      rotatedUV.x * c - rotatedUV.y * s,
                      rotatedUV.x * s + rotatedUV.y * c
                  );
                  rotatedUV += decalPositions[i]; // Translate back to original position

                  vec2 uv = (rotatedUV - decalPositions[i]) / decalSizes[i] + 0.5;
                  
                  if (decalFlipXs[i]) {
                    uv.x = 1.0 - uv.x;
                  }
                  if (decalFlipYs[i]) {
                    uv.y = 1.0 - uv.y;
                  }

                  vec4 texColor = vec4(0.0);
                  switch(i) {
                    ${this.generateSwitchCases(decals.length)}
                  }
                  if (uv.x >= 0.0 && uv.x <= 1.0 && uv.y >= 0.0 && uv.y <= 1.0 && originalUV.x >= minX && originalUV.x <= maxX && originalUV.y >= minY && originalUV.y <= maxY && gl_FrontFacing) {
                    float existingAlpha = diffuseColor.a;
                    float finalAlpha = existingAlpha * (1.0 - texColor.a * decalOpacities[i]) + texColor.a * decalOpacities[i];

                      // Check if the final alpha is less than a very small threshold, treat it as fully transparent
                      if (finalAlpha < 0.001) {
                          diffuseColor.a = 0.0;
                      } else {
                          // Blend the colors using the calculated alpha value
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
    },
  });

  // Image Bank Store - manages image selection modal
  Alpine.store("imageBank", {
    images: [],
    selectedImage: null,
    isLoading: false,
    isUploading: false,
    uploadProgress: 0,
    uploadedCount: 0,
    totalToUpload: 0,
    searchQuery: "",
    currentCategory: "all",
    categories: [],

    init() {
      // Load categories from template data
      this.categories = window.phpData?.imageBank?.categories || [];
    },

    showToast(message, type = "info", duration = 5000) {
      // Dispatch custom event to show toast
      window.dispatchEvent(
        new CustomEvent("show-toast", {
          detail: { message, type, duration },
        })
      );
    },

    get filteredImages() {
      let filtered = this.images;

      // When searching, show all images regardless of category
      if (this.searchQuery && this.searchQuery.trim()) {
        const query = this.searchQuery.toLowerCase().trim();
        // Search across ALL images
        filtered = this.images.filter((img) =>
          img.name.toLowerCase().includes(query)
        );
      } else {
        // When not searching, apply category filter
        if (this.currentCategory === "all") {
          // Show all images
        } else if (this.currentCategory === "my-images") {
          // Show only user uploaded images (DesignImage)
          filtered = filtered.filter((img) => img.source === "user");
        } else {
          // Show images from specific brand category
          filtered = filtered.filter(
            (img) => img.category_id == this.currentCategory
          );
        }
      }

      return filtered;
    },

    get categoryTitle() {
      // When searching, always show "Search Results"
      if (this.searchQuery && this.searchQuery.trim()) {
        return `Search Results for "${this.searchQuery}"`;
      }

      if (this.currentCategory === "all") return "All Images";
      if (this.currentCategory === "my-images") return "My Images";

      const category = this.categories.find(
        (cat) => cat.id == this.currentCategory
      );
      return category ? category.name : "All Images";
    },

    async loadImages() {
      this.isLoading = true;
      try {
        const response = await fetch("/designer/images/");
        const data = await response.json();
        this.images = data.images || [];
      } catch (error) {
        console.error("Error loading images:", error);
      } finally {
        this.isLoading = false;
      }
    },

    async uploadImage(event) {
      const files = event.target.files;
      if (!files || files.length === 0) return;

      const formData = new FormData();

      // Add all selected files
      for (let i = 0; i < files.length; i++) {
        formData.append("images", files[i]);
      }

      // Set upload state
      this.isUploading = true;
      this.isLoading = true;
      this.uploadProgress = 0;
      this.uploadedCount = 0;
      this.totalToUpload = files.length;

      // Simulate progress during upload
      const progressInterval = setInterval(() => {
        if (this.uploadProgress < 90) {
          this.uploadProgress += Math.random() * 10;
        }
      }, 200);

      try {
        const response = await fetch("/designer/images/upload/", {
          method: "POST",
          body: formData,
          headers: {
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")
              .value,
          },
        });

        // Clear progress interval
        clearInterval(progressInterval);
        this.uploadProgress = 100;

        const result = await response.json();

        if (response.ok && result.success) {
          // Add all successfully uploaded images to the beginning of the list
          if (result.images && result.images.length > 0) {
            this.images.unshift(...result.images);
            this.uploadedCount = result.images.length;

            // Switch to 'My Images' category to show the uploaded images
            this.currentCategory = "my-images";
          }

          // Show success message
          if (result.uploaded_count > 0) {
            this.showToast(
              `Successfully uploaded ${result.uploaded_count} image(s)`,
              "success"
            );
          }

          // Show any errors that occurred
          if (result.errors && result.errors.length > 0) {
            result.errors.forEach((error) => {
              this.showToast(error, "error", 8000); // Longer duration for errors
            });

            // If some succeeded and some failed
            if (result.uploaded_count > 0) {
              this.showToast(
                `${result.errors.length} image(s) failed to upload`,
                "warning"
              );
            }
          }

          event.target.value = "";
        } else {
          this.showToast(result.error || "Upload failed", "error");
          if (result.errors && result.errors.length > 0) {
            result.errors.forEach((error) => {
              this.showToast(error, "error", 8000);
            });
          }
        }
      } catch (error) {
        console.error("Error uploading images:", error);
        this.showToast(
          "Network error during upload. Please try again.",
          "error"
        );
        clearInterval(progressInterval);
      } finally {
        // Small delay to show completed state
        setTimeout(() => {
          this.isUploading = false;
          this.isLoading = false;
          this.uploadProgress = 0;
        }, 1000);
      }
    },

    selectImage(image) {
      this.selectedImage = image;
    },

    selectCategory(categoryId) {
      this.currentCategory = categoryId;
      this.selectedImage = null;
      // Clear search when selecting a category
      this.searchQuery = "";
    },

    addToDesign() {
      if (this.selectedImage) {
        const designer = Alpine.store("designer");
        
        // Check if we're replacing an existing decal
        if (designer.replacingDecalId) {
          const layer = designer.layers[designer.currentLayer];
          const decal = layer.decals.find(d => d.id === designer.replacingDecalId);
          
          if (decal && decal.type === 'image') {
            // Replace the image
            debugLog("Replacing image for decal:", decal.id);
            
            // Load new texture
            textureLoader.load(
              this.selectedImage.image_url,
              (texture) => {
                // Dispose old texture
                if (decal.texture) {
                  decal.texture.dispose();
                }
                
                // Apply texture settings
                designer.applyTextureSettings(texture);
                
                // Update decal
                decal.texture = texture;
                decal.imageUrl = this.selectedImage.image_url;
                decal.name = this.selectedImage.name;
                
                designer.renderLayer();
                debugLog("Image replaced successfully");
              },
              undefined,
              (error) => {
                debugError("Failed to load replacement image:", error);
                alert("Failed to load image. Please try again.");
              }
            );
          }
          
          // Clear the replacing flag
          designer.replacingDecalId = null;
        } else {
          // Normal add to design
          designer.createImageDecalFromUrl(
            this.selectedImage.image_url,
            this.selectedImage.name
          );
        }

        bootstrap.Modal.getInstance(
          document.getElementById("imageBankModal")
        ).hide();
        this.selectedImage = null;
      }
    },

    formatFileSize(bytes) {
      if (!bytes) return "";
      const sizes = ["B", "KB", "MB", "GB"];
      const i = Math.floor(Math.log(bytes) / Math.log(1024));
      return Math.round((bytes / Math.pow(1024, i)) * 10) / 10 + " " + sizes[i];
    },

    async deleteImage(image) {
      if (!image || image.source !== "user") {
        console.error("Cannot delete this image");
        return;
      }

      try {
        const response = await fetch(`/designer/images/delete/${image.id}/`, {
          method: "DELETE",
          headers: {
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]")
              .value,
            "Content-Type": "application/json",
          },
        });

        const result = await response.json();

        if (response.ok && result.success) {
          // Remove the image from the local array
          const index = this.images.findIndex((img) => img.id === image.id);
          if (index > -1) {
            this.images.splice(index, 1);
          }

          // Clear selection if the deleted image was selected
          if (this.selectedImage && this.selectedImage.id === image.id) {
            this.selectedImage = null;
          }

          console.log("Image deleted successfully:", result.message);
        } else {
          console.error("Delete failed:", result.error || "Unknown error");
        }
      } catch (error) {
        console.error("Error deleting image:", error);
      }
    },
  });
});

// Initialize when Alpine is ready
document.addEventListener("alpine:initialized", () => {
  debugLog("Alpine Designer initialized");
  Alpine.store("designer").init();
  Alpine.store("imageBank").init();
});
