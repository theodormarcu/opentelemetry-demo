import { SpanStatusCode, trace } from '@opentelemetry/api';
import type { NextApiRequest, NextApiResponse } from 'next';

// Error types we can simulate
const errorTypes = {
  INTERNAL_ERROR: 'INTERNAL_ERROR',
  VALIDATION_ERROR: 'VALIDATION_ERROR',
  TIMEOUT_ERROR: 'TIMEOUT_ERROR',
  DEPENDENCY_ERROR: 'DEPENDENCY_ERROR'
};

type ErrorResponse = {
  message: string;
  errorType: string;
  timestamp: string;
};

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse<ErrorResponse>
) {
  const { 
    errorType = errorTypes.INTERNAL_ERROR,
    errorRate = '1.0', // Default to 100% error rate
    latencyMs = '0'    // Default to no added latency
  } = req.query;

  // Get the current active span - this will be created by Next.js instrumentation
  const activeSpan = trace.getActiveSpan();
  
  try {
    // Convert and validate error rate (0.0 to 1.0)
    const rate = Math.min(Math.max(parseFloat(errorRate as string), 0.0), 1.0);
    const latency = parseInt(latencyMs as string) || 0;

    // Add attributes to the active span
    if (activeSpan) {
      activeSpan.setAttribute('error.type', errorType);
      activeSpan.setAttribute('error.rate', rate);
      activeSpan.setAttribute('error.latency_ms', latency);
    }

    // Simulate latency if specified
    if (latency > 0) {
      await new Promise(resolve => setTimeout(resolve, latency));
    }

    // Determine if we should generate an error based on error rate
    if (Math.random() < rate) {
      // Generate the error
      switch (errorType) {
        case errorTypes.VALIDATION_ERROR:
          if (activeSpan) {
            activeSpan.setAttribute('error.message', 'Invalid input parameters');
          }
          throw new Error('Validation failed: Invalid input parameters');

        case errorTypes.TIMEOUT_ERROR:
          if (activeSpan) {
            activeSpan.setAttribute('error.message', 'Request timed out');
          }
          throw new Error('Operation timed out');

        case errorTypes.DEPENDENCY_ERROR:
          if (activeSpan) {
            activeSpan.setAttribute('error.message', 'Downstream service unavailable');
          }
          throw new Error('Failed to reach dependent service');

        case errorTypes.INTERNAL_ERROR:
        default:
          if (activeSpan) {
            activeSpan.setAttribute('error.message', 'Internal server error');
          }
          throw new Error('Internal server error occurred');
      }
    }

    // If we get here, it means we're in the success path based on error rate
    res.status(200).json({
      message: 'Request processed successfully',
      errorType: errorType as string,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    // Record the error in the span
    if (activeSpan) {
      activeSpan.recordException(error as Error);
      activeSpan.setStatus({ code: SpanStatusCode.ERROR });
    }

    // Send error response
    res.status(500).json({
      message: (error as Error).message,
      errorType: errorType as string,
      timestamp: new Date().toISOString()
    });
  }
}
