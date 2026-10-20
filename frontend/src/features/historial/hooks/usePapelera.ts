import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  eliminarDefinitivo,
  obtenerPapelera,
  restaurarDiagnostico,
  vaciarPapelera,
} from '../api/historial.api';

export function usePapelera() {
  return useQuery({
    queryKey: ['papelera'],
    queryFn: obtenerPapelera,
    staleTime: 1000 * 30,
  });
}

function useInvalidarListas() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ['historial'] });
    queryClient.invalidateQueries({ queryKey: ['papelera'] });
  };
}

export function useRestaurarDiagnostico() {
  const invalidar = useInvalidarListas();
  return useMutation({ mutationFn: restaurarDiagnostico, onSuccess: invalidar });
}

export function useEliminarDefinitivo() {
  const invalidar = useInvalidarListas();
  return useMutation<void, Error, string>({
    mutationFn: eliminarDefinitivo,
    onSuccess: invalidar,
  });
}

export function useVaciarPapelera() {
  const invalidar = useInvalidarListas();
  return useMutation({ mutationFn: vaciarPapelera, onSuccess: invalidar });
}
