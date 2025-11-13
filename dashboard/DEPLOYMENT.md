# Dashboard Deployment Guide

## Prerequisites

1. **Vercel Account**: Sign up at https://vercel.com
2. **Vercel CLI** (optional, for CLI deployment):
   ```bash
   npm install -g vercel
   ```

## Deployment Methods

### Method 1: Deploy via Vercel CLI (Recommended)

1. **Install Vercel CLI** (if not already installed):
   ```bash
   npm install -g vercel
   ```

2. **Navigate to dashboard directory**:
   ```bash
   cd dashboard
   ```

3. **Login to Vercel**:
   ```bash
   vercel login
   ```

4. **Deploy**:
   ```bash
   vercel
   ```
   
   Follow the prompts:
   - Link to existing project? (No for first deployment)
   - Project name: `vocabulator-dashboard` (or your preferred name)
   - Directory: `./` (current directory)
   - Override settings? (No)

5. **Set Environment Variable**:
   ```bash
   vercel env add VITE_API_BASE
   ```
   
   When prompted, enter your production API URL:
   ```
   https://plugilp509.execute-api.us-east-1.amazonaws.com/development/api/v1
   ```

6. **Redeploy** (to apply environment variable):
   ```bash
   vercel --prod
   ```

### Method 2: Deploy via Vercel Dashboard (GitHub Integration)

1. **Push code to GitHub** (if not already):
   ```bash
   git add dashboard/
   git commit -m "Add dashboard for deployment"
   git push
   ```

2. **Import Project in Vercel**:
   - Go to https://vercel.com/new
   - Import your GitHub repository
   - Select the `dashboard` directory as the root directory
   - Framework Preset: SvelteKit (auto-detected)

3. **Configure Environment Variables**:
   - Go to Project Settings → Environment Variables
   - Add: `VITE_API_BASE` = `https://plugilp509.execute-api.us-east-1.amazonaws.com/development/api/v1`
   - Apply to: Production, Preview, Development

4. **Deploy**:
   - Click "Deploy"
   - Vercel will automatically build and deploy

### Method 3: Deploy to AWS S3 + CloudFront (Alternative)

If you prefer to deploy to AWS instead of Vercel:

1. **Build the dashboard**:
   ```bash
   cd dashboard
   npm run build
   ```

2. **Upload to S3**:
   ```bash
   aws s3 sync build/ s3://your-bucket-name/dashboard/ --delete
   ```

3. **Configure CloudFront** to serve the S3 bucket

4. **Set environment variable** at build time:
   ```bash
   VITE_API_BASE=https://plugilp509.execute-api.us-east-1.amazonaws.com/development/api/v1 npm run build
   ```

## Post-Deployment Steps

### 1. Update Backend CORS Configuration

After deployment, update your API Gateway CORS configuration to include the Vercel domain:

1. **Get your Vercel deployment URL** (e.g., `https://vocabulator-dashboard.vercel.app`)

2. **Update Lambda environment variable**:
   ```bash
   aws lambda update-function-configuration \
     --function-name vocabulator-development-api \
     --environment Variables="{CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173,http://localhost:8000,https://vocabulator-dashboard.vercel.app}" \
     --region us-east-1
   ```

3. **Update API Gateway CORS** (if needed):
   - The CORS configuration in `infrastructure/cloudformation/api-gateway-lambda.yaml` should already handle this
   - Redeploy CloudFormation if you need to add the new origin

### 2. Verify Deployment

1. Visit your Vercel deployment URL
2. Check browser console for errors
3. Test API connectivity
4. Verify student data loads

## Environment Variables

### Required
- `VITE_API_BASE`: Your production API URL
  - Development: `https://plugilp509.execute-api.us-east-1.amazonaws.com/development/api/v1`
  - Production: Update when you have a production API URL

### Optional
- None currently required

## Troubleshooting

### Build Fails
- Ensure Node.js 18+ is installed
- Run `npm install` in the dashboard directory
- Check for TypeScript errors: `npm run check`

### API Connection Errors
- Verify `VITE_API_BASE` is set correctly in Vercel
- Check backend CORS configuration includes Vercel domain
- Verify API Gateway is accessible

### CORS Errors
- Add Vercel domain to backend CORS allowed origins
- Redeploy backend after CORS changes

## Continuous Deployment

If using GitHub integration, Vercel will automatically deploy on every push to:
- `main` branch → Production
- Other branches → Preview deployments

Each preview deployment gets its own URL for testing.

