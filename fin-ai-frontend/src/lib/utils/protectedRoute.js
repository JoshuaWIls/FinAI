//Users/jwils/Developer/code/7th sem project Finance AI/financialai/fin-ai-frontend/src/lib/utils/protectedRoute.js
import { NextResponse } from 'next/server';
import { getAuthToken, verifyToken } from './auth';

/**
 * A utility to check for a valid JWT in the request cookies.
 * This pattern is used to protect Next.js Route Handlers.
 * @param {Request} request The incoming Next.js Request object.
 * @returns {object|NextResponse} Returns the verified payload or an error Response.
 */
export const protectApiRoute = (request) => {
  const token = getAuthToken(request);

  if (!token) {
    return NextResponse.json({ message: 'Not authenticated' }, { status: 401 });
  }

  const verified = verifyToken(token);

  if (!verified) {
    return NextResponse.json({ message: 'Token expired or invalid' }, { status: 403 });
  }

  // Returns the payload if successful
  return { userId: verified.id }; 
};