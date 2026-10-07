import { useQuery } from '@tanstack/react-query';
import { obtenerHistorial } from '../api/historial.api';

export function useHistorial() {
  return useQuery({
    queryKey: ['historial'],
    queryFn: obtenerHistorial,
    staleTime: 1000 * 30, // 30 segundos
  });
}
