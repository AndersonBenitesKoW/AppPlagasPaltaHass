import { useQuery } from '@tanstack/react-query';
import { obtenerCatalogo } from '../api/catalogo.api';

export function useCatalogo() {
  return useQuery({
    queryKey: ['catalogo'],
    queryFn: obtenerCatalogo,
    staleTime: 1000 * 60 * 30, // 30 minutos de caché
  });
}
