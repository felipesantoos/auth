import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  
  // Path resolution for cleaner imports
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  
  // Build optimization
  build: {
    // Target modern browsers for better performance
    target: 'es2015',
    
    // Chunk size warning limit (500kb)
    chunkSizeWarningLimit: 500,
    
    // Rollup options for bundle optimization
    rollupOptions: {
      output: {
        // ⚡ PERFORMANCE: Manual chunks for vendor code splitting
        // Separates vendor code into individual chunks for better caching
        // When React updates, only react-vendor.js changes (not entire bundle)
        manualChunks: {
          // Core React libraries (changes rarely)
          'react-vendor': ['react', 'react-dom', 'react-router-dom'],
          
          // UI component libraries (changes rarely)
          'ui-vendor': [
            '@radix-ui/react-dialog',
            '@radix-ui/react-dropdown-menu',
            '@radix-ui/react-label',
            '@radix-ui/react-select',
            '@radix-ui/react-slot',
            '@radix-ui/react-toast',
          ],
          
          // Data fetching & state management (changes rarely)
          'data-vendor': ['@tanstack/react-query', '@tanstack/react-table'],
          
          // Form & validation libraries (changes rarely)
          'form-vendor': ['react-hook-form', '@hookform/resolvers', 'zod'],
          
          // Utilities (changes rarely)
          'utils-vendor': ['axios', 'date-fns', 'clsx', 'tailwind-merge'],
        },
        
        // Asset file names with hash for cache busting
        assetFileNames: (assetInfo) => {
          const info = assetInfo.name.split('.');
          const ext = info[info.length - 1];
          if (/png|jpe?g|svg|gif|tiff|bmp|ico/i.test(ext)) {
            return `assets/images/[name]-[hash][extname]`;
          } else if (/woff|woff2|eot|ttf|otf/i.test(ext)) {
            return `assets/fonts/[name]-[hash][extname]`;
          }
          return `assets/[name]-[hash][extname]`;
        },
        
        // Chunk file names with hash for cache busting
        chunkFileNames: 'assets/js/[name]-[hash].js',
        entryFileNames: 'assets/js/[name]-[hash].js',
      },
    },
    
    // Minification options
    minify: 'terser',
    terserOptions: {
      compress: {
        // Remove console.log in production
        drop_console: true,
        drop_debugger: true,
        // Remove dead code
        dead_code: true,
        // Evaluate constant expressions
        evaluate: true,
      },
      format: {
        // Remove comments
        comments: false,
      },
    },
    
    // Source maps for production debugging (disable for faster builds)
    sourcemap: false,
    
    // Report compressed size (slower build, but useful for monitoring)
    reportCompressedSize: true,
  },
  
  // Development server optimization
  server: {
    port: 5173,
    // Faster HMR
    hmr: {
      overlay: true,
    },
  },
  
  // Preview server (for testing production build locally)
  preview: {
    port: 4173,
  },
})
