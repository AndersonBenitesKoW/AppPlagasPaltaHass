import { useMutation, useQueryClient } from '@tanstack/react-query';
import { enviarDiagnostico, enviarDiagnosticoLote } from '../api/diagnostico.api';
import type { Diagnostico, DiagnosticosBatchResponse } from '../model/types';

export function useDiagnosticar() {
  const queryClient = useQueryClient();

  const mutationIndividual = useMutation<Diagnostico, Error, File>({
    mutationFn: enviarDiagnostico,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['historial'] });
    },
  });

  const mutationLote = useMutation<DiagnosticosBatchResponse, Error, File[]>({
    mutationFn: enviarDiagnosticoLote,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['historial'] });
    },
  });

  return {
    analizarUno: mutationIndividual.mutateAsync,
    analizarLote: mutationLote.mutateAsync,
    isLoading: mutationIndividual.isPending || mutationLote.isPending,
    error: mutationIndividual.error || mutationLote.error,
  };
}
