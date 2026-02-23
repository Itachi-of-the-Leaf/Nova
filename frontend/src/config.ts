/**
 * Central API configuration.
 *
 * Set VITE_API_URL in your .env file to point at the backend:
 *   VITE_API_URL=http://127.0.0.1:8000
 *
 * Falls back to localhost:8000 when the variable is not defined.
 */
export const API_BASE = import.meta.env.VITE_API_URL ?? 'http://127.0.0.1:8000';
