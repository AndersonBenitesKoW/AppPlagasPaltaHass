import { useMutation, useQueryClient } from '@tanstack/react-query';

import {
  enviarDiagnostico,
  enviarDiagnosticoLote,
  type Organo,
} from '../api/diagnostico.api';

import type { Diagnostico, DiagnosticosBatchResponse } from '../model/types';

export function useDiagnosticar() {
  const queryClient = useQueryClient();

  const mutationIndividual = useMutation<
    Diagnostico,
    Error,
    { file: File; organo: Organo }
  >({
    mutationFn: ({ file, organo }) => enviarDiagnostico(file, organo),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['historial'] });
    },
  });

  const mutationLote = useMutation<
    DiagnosticosBatchResponse,
    Error,
    { files: File[]; organo: Organo }
  >({
    mutationFn: ({ files, organo }) => enviarDiagnosticoLote(files, organo),
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

