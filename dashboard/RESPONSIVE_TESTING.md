# Responsive Design Testing Guide

## Test Devices and Viewports

Test the dashboard at the following breakpoints:

### Mobile Devices
- **Small Mobile**: 320px × 568px (iPhone SE)
- **Medium Mobile**: 375px × 667px (iPhone 8)
- **Large Mobile**: 414px × 896px (iPhone 11 Pro Max)

### Tablets
- **Small Tablet**: 768px × 1024px (iPad)
- **Large Tablet**: 1024px × 1366px (iPad Pro)

### Desktop
- **Small Desktop**: 1280px × 720px
- **Medium Desktop**: 1920px × 1080px
- **Large Desktop**: 2560px × 1440px

## Test Cases

### 1. Teacher Dashboard View

#### Mobile (< 768px)
- [ ] Header navbar stacks vertically or uses hamburger menu
- [ ] "Sync with Google Classroom" button is full-width or appropriately sized
- [ ] Class filter dropdown is full-width
- [ ] Student table is horizontally scrollable
- [ ] Table columns are readable (no text truncation issues)
- [ ] "View Details" buttons are appropriately sized for touch
- [ ] All text is readable without zooming

#### Tablet (768px - 1024px)
- [ ] Header layout is optimized for tablet
- [ ] Student table uses available space efficiently
- [ ] Buttons and form elements are appropriately sized
- [ ] No horizontal scrolling required

#### Desktop (> 1024px)
- [ ] Layout uses full width efficiently
- [ ] Student table displays all columns without scrolling
- [ ] Spacing is appropriate (not too cramped or too spread out)

### 2. Student Detail View

#### Mobile (< 768px)
- [ ] StudentStats card stacks vertically (4 columns → 2x2 or 1x4)
- [ ] Vocabulary chart is readable (not too small)
- [ ] Chart labels are readable
- [ ] Recommendations list items are full-width
- [ ] "Show Details" buttons are easily tappable
- [ ] Assignment selector checkboxes are easily tappable
- [ ] "Submit Selected Assignments" button is full-width

#### Tablet (768px - 1024px)
- [ ] StudentStats uses 2x2 grid layout
- [ ] Chart is appropriately sized
- [ ] Recommendations list uses available space
- [ ] Assignment selector is readable

#### Desktop (> 1024px)
- [ ] StudentStats uses 4-column layout
- [ ] Chart uses full width appropriately
- [ ] All components are well-spaced

### 3. Header Component

#### All Viewports
- [ ] Header is always visible (sticky/fixed if implemented)
- [ ] Dropdown is accessible and usable
- [ ] Dropdown options are readable
- [ ] Brand name "Vocabulator Dashboard" is visible

#### Mobile
- [ ] Dropdown doesn't overflow viewport
- [ ] Dropdown is easily accessible with touch

### 4. Vocabulary Chart Component

#### All Viewports
- [ ] Chart is responsive (adjusts to container width)
- [ ] Chart labels are readable
- [ ] Chart tooltips are accessible
- [ ] Chart maintains aspect ratio appropriately
- [ ] Chart doesn't overflow container

#### Mobile
- [ ] Chart is readable when zoomed
- [ ] Touch interactions work (if implemented)

### 5. Recommendations List Component

#### All Viewports
- [ ] List items are readable
- [ ] Expandable sections work correctly
- [ ] Difficulty badges are visible
- [ ] Text doesn't overflow containers

#### Mobile
- [ ] List items stack properly
- [ ] "Show Details" buttons are easily tappable
- [ ] Expanded content is readable

### 6. Assignment Selector Component

#### All Viewports
- [ ] Checkboxes are easily clickable/tappable
- [ ] Assignment preview text is readable
- [ ] Submit button is accessible
- [ ] Success/error messages are visible

#### Mobile
- [ ] Checkboxes are large enough for touch
- [ ] Assignment text preview doesn't overflow
- [ ] Submit button is full-width or appropriately sized

## Bootstrap Breakpoints Used

The dashboard uses Bootstrap 5 breakpoints:
- **xs**: < 576px (extra small)
- **sm**: ≥ 576px (small)
- **md**: ≥ 768px (medium)
- **lg**: ≥ 992px (large)
- **xl**: ≥ 1200px (extra large)
- **xxl**: ≥ 1400px (extra extra large)

## Testing Tools

### Browser DevTools
1. Open Chrome/Edge DevTools (F12)
2. Click device toolbar icon (Ctrl+Shift+M)
3. Select device or enter custom dimensions
4. Test interactions and layout

### Online Tools
- [Responsive Design Checker](https://responsivedesignchecker.com/)
- [BrowserStack](https://www.browserstack.com/) (for real device testing)

## Common Issues to Check

1. **Text Overflow**: Ensure long text doesn't break layout
2. **Touch Targets**: Buttons/links should be at least 44×44px on mobile
3. **Horizontal Scrolling**: Should not occur except for intentional scrollable tables
4. **Fixed Width Elements**: Avoid fixed widths that break on small screens
5. **Image Scaling**: Charts and images should scale appropriately
6. **Form Elements**: Inputs and selects should be appropriately sized
7. **Modal/Dropdown Overflow**: Ensure dropdowns don't get cut off

## Responsive Utilities Used

The dashboard uses Bootstrap responsive utilities:
- `container-fluid`: Full-width container
- `row`: Flexbox row
- `col-md-*`: Responsive columns
- `table-responsive`: Scrollable table wrapper
- `d-flex`, `d-md-block`: Display utilities
- `text-center`, `text-md-start`: Text alignment utilities

## Test Checklist

Before marking responsive design as complete:

- [ ] All test cases pass on mobile devices
- [ ] All test cases pass on tablets
- [ ] All test cases pass on desktop
- [ ] No horizontal scrolling (except intentional)
- [ ] All interactive elements are accessible
- [ ] Text is readable at all sizes
- [ ] Charts and visualizations are readable
- [ ] Forms are usable on all devices
- [ ] Navigation works on all devices

