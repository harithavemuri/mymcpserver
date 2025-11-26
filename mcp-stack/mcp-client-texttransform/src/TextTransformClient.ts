import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import { logger } from './logger';

export interface TextTransformOptions {
  baseURL?: string;
  timeout?: number;
  headers?: Record<string, string>;
}

export interface TransformRequest {
  text: string;
  operation: 'uppercase' | 'lowercase' | 'capitalize' | 'reverse' | 'trim' | string;
  options?: Record<string, unknown>;
}

export interface TransformResponse {
  original: string;
  transformed: string;
  operation: string;
  timestamp: string;
}

export class TextTransformClient {
  private client: AxiosInstance;
  private baseURL: string;

  constructor(options: TextTransformOptions = {}) {
    this.baseURL = options.baseURL || 'http://localhost:8002';

    this.client = axios.create({
      baseURL: this.baseURL,
      timeout: options.timeout || 5000,
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...(options.headers || {})
      }
    });

    // Add request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        logger.info(`Sending ${config.method?.toUpperCase()} request to ${config.url}`, {
          method: config.method,
          url: config.url,
          data: config.data
        });
        return config;
      },
      (error) => {
        logger.error('Request error:', error);
        return Promise.reject(error);
      }
    );

    // Add response interceptor for logging and error handling
    this.client.interceptors.response.use(
      (response) => {
        logger.info(`Received response from ${response.config.url}`, {
          status: response.status,
          statusText: response.statusText,
          data: response.data
        });
        return response;
      },
      (error) => {
        const errorData = {
          message: error.message,
          config: {
            url: error.config?.url,
            method: error.config?.method,
            data: error.config?.data
          },
          response: {
            status: error.response?.status,
            statusText: error.response?.statusText,
            data: error.response?.data
          }
        };

        logger.error('Response error:', errorData);
        return Promise.reject(error);
      }
    );
  }

  /**
   * Transforms the input text using the specified operation
   * @param text The text to transform
   * @param operation The transformation operation to apply
   * @param options Additional options for the transformation
   * @returns A promise that resolves to the transformed text
   */
  public async transform(
    text: string,
    operation: string = 'uppercase',
    options: Record<string, unknown> = {}
  ): Promise<TransformResponse> {
    try {
      const request: TransformRequest = {
        text,
        operation,
        options
      };

      const response: AxiosResponse<TransformResponse> = await this.client.post(
        '/transform',
        request
      );

      return response.data;
    } catch (error) {
      logger.error('Transform request failed:', { error, text, operation, options });
      throw new Error(`Failed to transform text: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  /**
   * Checks if the MCP server is healthy
   * @returns A promise that resolves to true if the server is healthy
   */
  public async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/health');
      return response.status === 200;
    } catch (error) {
      logger.error('Health check failed:', { error });
      return false;
    }
  }

  /**
   * Gets information about available transformations
   * @returns A promise that resolves to the list of available transformations
   */
  public async getAvailableTransformations(): Promise<string[]> {
    try {
      const response = await this.client.get('/transformations');
      return response.data as string[];
    } catch (error) {
      logger.error('Failed to get available transformations:', { error });
      throw new Error('Failed to retrieve available transformations');
    }
  }
}

export default TextTransformClient;
