import { Request, Response } from "express";

export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  timestamp: string;
}

export interface ErrorResponse {
  success: false;
  error: string;
  message: string;
  statusCode: number;
  timestamp: string;
  path?: string;
  stack?: string;
}

export interface CustomRequest extends Request {
  requestId?: string;
  startTime?: number;
}

export interface CustomResponse extends Response {
  locals: {
    requestId?: string;
  };
}

export interface ValidationError {
  field: string;
  message: string;
  value?: any;
}

export interface RouteHandler {
  (req: CustomRequest, res: CustomResponse): Promise<void> | void;
}
