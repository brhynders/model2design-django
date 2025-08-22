# Django Refactoring Plan: PHP to Django Migration

This document outlines the complete plan for migrating the vanilla PHP application to Django, structured into Django apps.

## Project Overview

**Source**: `/model2design-php` - Vanilla PHP application with RedBeanPHP ORM  
**Target**: `/m2django` - Django application with proper app structure  
**Goal**: Maintain exact HTML/CSS/JS while converting to Django architecture

---

## Django Apps Structure

### ✅ 1. **accounts** - User Authentication & Management
**Status**: COMPLETED ✅

**Functionality**:
- User registration, login, logout
- Profile management 
- Password reset flow
- Dashboard with user statistics
- Guest data migration

**PHP Files Migrated**:
- `login.php` → `accounts/templates/accounts/login.html`
- `register.php` → `accounts/templates/accounts/register.html`
- `profile.php` → `accounts/templates/accounts/profile.html`
- `dashboard.php` → `accounts/templates/accounts/dashboard.html`
- `forgot-password.php` → `accounts/templates/accounts/forgot_password.html`
- `reset-password.php` → `accounts/templates/accounts/reset_password.html`
- `logout.php` → `accounts/views.logout_view`

**Models**:
- `User` (extends AbstractUser) - Custom user with phone, name, brand owner flag
- `PasswordResetToken` - Password reset tokens

**Key Features**:
- Email-based authentication (no username)
- Phone number formatting (US format)
- Guest session migration placeholder
- Exact HTML preservation with Bootstrap 5

---

### ✅ 2. **products** - Product Catalog & Management
**Status**: COMPLETED ✅

**Functionality**:
- Product listing with categories
- Product detail pages
- Product search and filtering
- Static product data management
- Brand-specific product catalogs

**PHP Files to Migrate**:
- `products.php` → Product listing page
- `product-details.php` → Product detail page
- `includes/data.products.php` → Django fixtures/management commands

**Models Needed**:
- `Product` - Product information (name, description, price, etc.)
- `ProductCategory` - Product categorization
- `ProductImage` - Product images and thumbnails
- `BrandProduct` - Brand-specific product availability

**Key Features**:
- 3D model file management (.glb files)
- Product thumbnails
- Category-based filtering
- Brand-specific pricing

---

### 3. **designer** - 3D Design Interface
**Status**: PENDING

**Functionality**:
- 3D design creation interface
- Design saving & loading
- Template selection
- Real-time 3D preview
- Design sharing

**PHP Files to Migrate**:
- `designer.php` → Main 3D designer interface
- `save-design.php` → Design saving endpoint
- `select-template.php` → Template selection
- `design-share.php` → Design sharing page
- `designs.php` → User's saved designs
- `api/designs.php` → Design API endpoints

**Models Needed**:
- `Design` - User designs with 3D data
- `DesignTemplate` - Pre-made design templates
- `DesignShare` - Shared design links

**Key Features**:
- Three.js integration
- GLTF model loading
- Real-time design updates
- Guest design session handling

---

### 4. **cart** - Shopping Cart Management
**Status**: COMPLETED ✅

**Functionality**:
- Add/remove items from cart
- Cart persistence (session + database)
- Cart sidebar component
- Guest cart migration

**PHP Files to Migrate**:
- `cart.php` → Cart page
- `add-to-cart.php` → Add to cart functionality
- `api/cart-sidebar.php` → Cart sidebar API

**Models Needed**:
- `Cart` - User shopping carts
- `CartItem` - Individual cart items with design references

**Key Features**:
- Session-based guest carts
- User cart persistence
- Real-time cart updates

---

### 5. **orders** - Order Processing & Management
**Status**: PENDING

**Functionality**:
- Checkout process
- Order creation & tracking
- Order history
- Order status updates
- Order notes management

**PHP Files to Migrate**:
- `checkout.php` → Checkout process
- `order-details.php` → Order detail page
- `orders.php` → Order history
- `order-success.php` → Order confirmation
- `api/update-order-notes.php` → Order notes API
- `api/generate-order-form.php` → Order form generation

**Models Needed**:
- `Order` - Order information
- `OrderItem` - Individual order items
- `OrderNote` - Order notes and updates
- `OrderStatus` - Order status tracking

**Key Features**:
- Multi-step checkout
- Order status workflow
- PDF generation for order forms

---

### 6. **payments** - Payment Processing
**Status**: PENDING

**Functionality**:
- Stripe payment integration
- Payment intent creation
- Webhook handling
- Coupon validation
- Payment confirmation

**PHP Files to Migrate**:
- `api/create-payment-intent.php` → Payment intent creation
- `api/confirm-payment.php` → Payment confirmation
- `api/stripe-webhook.php` → Stripe webhook handler
- `api/validate-coupon.php` → Coupon validation

**Models Needed**:
- `PaymentIntent` - Stripe payment intents
- `Coupon` - Discount coupons
- `Payment` - Payment records

**Key Features**:
- Stripe Elements integration
- Webhook event processing
- Coupon system

---

### 7. **brands** - Brand Management Portal
**Status**: COMPLETED ✅

**Functionality**:
- Brand owner dashboard
- Brand template management
- Brand background/styling
- Brand earnings tracking
- Brand image management

**PHP Files to Migrate**:
- `brand-dashboard.php` → Brand dashboard
- `brand-templates.php` → Template management
- `brand-backgrounds.php` → Background management
- `brand-images.php` → Image management
- `brand-settings.php` → Brand settings
- `brand-orders.php` → Brand order management
- `brand-earnings.php` → Earnings tracking
- `brand-panel.php` → Brand control panel
- `api/brand-backgrounds.php` → Brand backgrounds API
- `api/templates.php` → Templates API
- `api/public-templates.php` → Public templates API

**Models Needed**:
- `Brand` - Brand information
- `BrandTemplate` - Brand-specific templates
- `BrandImage` - Brand images and assets
- `BrandImageCategory` - Image categorization
- `BrandOwner` - Brand ownership relationships
- `BrandEarnings` - Revenue tracking

**Key Features**:
- Multi-brand support
- Brand-specific styling
- Template marketplace
- Revenue analytics

---

### 8. **admin_panel** - Administrative Interface
**Status**: PENDING

**Functionality**:
- Admin dashboard
- User management
- Order management
- Brand management
- System analytics

**PHP Files to Migrate**:
- `admin-dashboard.php` → Admin dashboard
- `admin-users.php` → User management
- `admin-orders.php` → Order management
- `admin-brands.php` → Brand management
- `admin-coupons.php` → Coupon management
- `admin-payments.php` → Payment tracking

**Models Needed**:
- Custom admin views and forms
- Analytics models

**Key Features**:
- Django admin integration
- Custom admin interface
- Reporting and analytics

---

### 9. **media** - File & Image Management
**Status**: PENDING

**Functionality**:
- Cloudflare R2 integration
- Image upload & processing
- Image bank management
- CORS proxy for Three.js
- Thumbnail generation

**PHP Files to Migrate**:
- `api/images.php` → Image management API
- `api/image-proxy.php` → CORS proxy
- `includes/class.cloudflare-r2.php` → R2 integration
- `includes/class.image-processor.php` → Image processing

**Models Needed**:
- `UserImage` - User uploaded images
- `ImageCategory` - Image categorization

**Key Features**:
- Cloudflare R2 storage
- Image processing pipeline
- CORS handling for 3D textures

---

### 10. **support** - Support & Static Pages
**Status**: PENDING

**Functionality**:
- Support ticket system
- FAQ management
- Static pages (privacy, terms, etc.)
- Tutorials and help content

**PHP Files to Migrate**:
- `support.php` → Support center
- `support-submit.php` → Ticket submission
- `privacy-policy.php` → Privacy policy
- `terms.php` → Terms of service
- `return-policy.php` → Return policy
- `shipping-info.php` → Shipping information

**Models Needed**:
- `SupportSubmission` - Support tickets
- `FAQ` - Frequently asked questions
- `Tutorial` - Help tutorials

**Key Features**:
- Ticket system
- Static content management
- Help documentation

---

### 11. **partners** - Partner Portal
**Status**: PENDING

**Functionality**:
- Partner registration
- Partner dashboard
- Partnership management

**PHP Files to Migrate**:
- `partner.php` → Partner portal

**Models Needed**:
- `Partner` - Partner information
- `Partnership` - Partnership relationships

---

## Shared Components

### **core** (Utility App)
**Purpose**: Shared utilities and base classes

**Components**:
- Database model base classes
- Common middleware
- Helper functions (from `includes/inc.functions.php`)
- CSRF & security utilities
- Session handling utilities
- Email services (SMTP2GO integration)
- Static data management (bumpmaps, fonts, tutorials, FAQs)

---

## Migration Strategy

### Phase 1: Foundation ✅
- [x] **accounts** app - User authentication and management
- [x] Static files setup (CSS, JS, images)
- [x] Base templates and navigation
- [x] Database configuration

### Phase 2: Core Commerce
- [x] **products** app - Product catalog
- [ ] **cart** app - Shopping functionality  
- [ ] **orders** app - Order processing
- [ ] **payments** app - Payment integration

### Phase 3: Design Features
- [ ] **designer** app - 3D design interface
- [ ] **media** app - File management

### Phase 4: Brand & Admin
- [ ] **brands** app - Brand management
- [ ] **admin_panel** app - Administrative interface

### Phase 5: Support & Partners
- [ ] **support** app - Support system
- [ ] **partners** app - Partner portal

---

## Technical Considerations

### Database Migration
- Custom User model (already implemented)
- RedBeanPHP → Django ORM conversion
- Session data migration utilities
- Brand-specific data isolation

### Frontend Preservation
- Exact HTML structure maintenance
- Bootstrap 5 styling preservation
- JavaScript functionality migration
- Three.js integration for 3D designer

### API Endpoints
- Convert PHP API files to Django REST views
- Maintain existing JavaScript API calls
- CSRF token handling
- JSON response formatting

### File Storage
- Cloudflare R2 integration with django-storages
- Static file serving configuration
- Media file handling
- 3D model (.glb) file management

### Security
- Django's built-in security features
- CSRF protection
- SQL injection prevention
- XSS protection
- User input sanitization

---

## Dependencies & Integrations

### External Services
- **Stripe**: Payment processing
- **Cloudflare R2**: File storage
- **SMTP2GO**: Email delivery
- **Three.js**: 3D rendering

### Django Packages
- `django-storages`: Cloudflare R2 integration
- `stripe`: Payment processing
- `pillow`: Image processing
- `django-cors-headers`: CORS handling
- `celery`: Background tasks (optional)

---

## Current Status

### Completed ✅
1. **accounts** app - Full authentication system with exact PHP HTML
2. **products** app - Product catalog foundation for other apps

### Next Priority
3. **cart** app - Shopping functionality

### Success Metrics
- [ ] All PHP functionality preserved
- [ ] Exact HTML/CSS maintained
- [ ] JavaScript compatibility preserved
- [ ] User experience unchanged
- [ ] Performance maintained or improved
- [ ] Security enhanced with Django features