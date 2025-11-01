/**
 * Upload Utilities
 * Helper functions for file upload operations
 */

/**
 * Divide file into chunks
 */
export function chunkFile(file: File, chunkSize: number): Blob[] {
  const chunks: Blob[] = [];
  let offset = 0;

  while (offset < file.size) {
    const chunk = file.slice(offset, offset + chunkSize);
    chunks.push(chunk);
    offset += chunkSize;
  }

  return chunks;
}

/**
 * Retry function with exponential backoff
 */
export async function retryWithBackoff<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  initialDelay: number = 1000
): Promise<T> {
  let lastError: Error;

  for (let i = 0; i < maxRetries; i++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error as Error;
      
      if (i < maxRetries - 1) {
        const delay = initialDelay * Math.pow(2, i);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
  }

  throw lastError!;
}

/**
 * Create abort controller for upload cancellation
 */
export function createUploadAbortController() {
  return new AbortController();
}

/**
 * Validate file before upload
 */
export interface FileValidationOptions {
  maxSize?: number; // bytes
  allowedTypes?: string[];
  maxFiles?: number;
}

export interface FileValidationResult {
  valid: boolean;
  errors: string[];
}

export function validateFile(
  file: File,
  options: FileValidationOptions = {}
): FileValidationResult {
  const errors: string[] = [];

  // Size validation
  if (options.maxSize && file.size > options.maxSize) {
    const maxMB = options.maxSize / (1024 * 1024);
    errors.push(`File too large. Maximum size is ${maxMB.toFixed(1)}MB`);
  }

  // Type validation
  if (options.allowedTypes && !options.allowedTypes.includes(file.type)) {
    errors.push(`File type ${file.type} is not allowed`);
  }

  return {
    valid: errors.length === 0,
    errors,
  };
}

/**
 * Validate multiple files
 */
export function validateFiles(
  files: File[],
  options: FileValidationOptions = {}
): FileValidationResult {
  const errors: string[] = [];

  // Number of files validation
  if (options.maxFiles && files.length > options.maxFiles) {
    errors.push(`Too many files. Maximum is ${options.maxFiles}`);
  }

  // Validate each file
  files.forEach((file, index) => {
    const result = validateFile(file, options);
    if (!result.valid) {
      errors.push(`File ${index + 1} (${file.name}): ${result.errors.join(', ')}`);
    }
  });

  return {
    valid: errors.length === 0,
    errors,
  };
}

