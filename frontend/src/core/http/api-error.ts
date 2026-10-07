import { z } from 'zod';

const ProblemSchema = z.object({
  title: z.string().optional(),
  status: z.number().optional(),
  detail: z.string().optional(),
  request_id: z.string().optional(),
});

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly codigo: string,
    public readonly detalle: string,
    public readonly requestId?: string,
  ) {
    super(detalle);
    this.name = 'ApiError';
  }

  static desde(body: unknown, status: number): ApiError {
    const parseado = ProblemSchema.safeParse(body);
    if (parseado.success && parseado.data) {
      return new ApiError(
        parseado.data.status || status,
        parseado.data.title || 'error',
        parseado.data.detail || 'Ocurrió un error en el servidor',
        parseado.data.request_id,
      );
    }
    return new ApiError(status, 'desconocido', 'Error de comunicación con el servidor');
  }
}
