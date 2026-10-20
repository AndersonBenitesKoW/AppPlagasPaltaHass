import { useMutation, useQueryClient } from '@tanstack/react-query';
import { eliminarDiagnostico } from '../api/historial.api';

/** Mueve un diagnóstico a la papelera. */
export function useEliminarDiagnostico() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: eliminarDiagnostico,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['historial'] });
      queryClient.invalidateQueries({ queryKey: ['papelera'] });
    },
  });
}
