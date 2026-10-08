import React, { useEffect, useRef, useState } from 'react';
import { UploadCloud, Image as ImageIcon, X, Sparkles, ScanSearch } from 'lucide-react';
import { Button } from '../../../shared/ui/Button';

interface DropzoneProps {
  onAnalizar: (archivos: File[]) => void;
  onAbrirCamara: () => void;
  isLoading: boolean;
}

export const Dropzone: React.FC<DropzoneProps> = ({
  onAnalizar,
  onAbrirCamara,
  isLoading,
}) => {
  const [archivos, setArchivos] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);

  const inputRef = useRef<HTMLInputElement>(null);

  /*
   * ============================================================
   * ARCHIVOS
   * ============================================================
   */

  const agregarArchivos = (nuevos: FileList | File[]) => {
    const permitidos = Array.from(nuevos).filter((f) =>
      ['image/jpeg', 'image/png', 'image/webp'].includes(f.type),
    );

    if (permitidos.length === 0) return;

    setArchivos((prev) => [...prev, ...permitidos]);

    const nuevosPreviews = permitidos.map((f) =>
      URL.createObjectURL(f),
    );

    setPreviews((prev) => [...prev, ...nuevosPreviews]);
  };

  const eliminarArchivo = (index: number) => {
    setPreviews((prev) => {
      if (prev[index]) {
        URL.revokeObjectURL(prev[index]);
      }

      return prev.filter((_, i) => i !== index);
    });

    setArchivos((prev) => prev.filter((_, i) => i !== index));
  };

  const limpiarTodo = () => {
    previews.forEach((preview) => {
      URL.revokeObjectURL(preview);
    });

    setArchivos([]);
    setPreviews([]);
  };

  /*
   * ============================================================
   * DRAG & DROP
   * ============================================================
   */

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);

    if (e.dataTransfer.files) {
      agregarArchivos(e.dataTransfer.files);
    }
  };

  useEffect(() => {
    return () => {
      previews.forEach((preview) => {
        URL.revokeObjectURL(preview);
      });
    };
  }, []);

  /*
   * ============================================================
   * ANALIZAR
   * ============================================================
   */

  const handleAnalizarClick = () => {
    if (archivos.length > 0) {
      onAnalizar(archivos);
    }
  };

  /*
   * ============================================================
   * RENDER
   * ============================================================
   */

  return (
    <div className="space-y-4">

      {/* ======================================================
          ÁREA PRINCIPAL DE SUBIDA
          ====================================================== */}

      <div
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`relative cursor-pointer rounded-3xl border-2 border-dashed p-8 sm:p-12 text-center transition-all duration-300 ${
          isDragOver
            ? 'border-emerald-400 bg-emerald-500/10 scale-[1.01]'
            : 'border-emerald-500/25 bg-[#121915]/60 hover:border-emerald-500/50 hover:bg-[#121915]'
        }`}
      >

        {/* Input normal de archivos */}
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          className="hidden"
          onChange={(e) => {
            if (e.target.files) {
              agregarArchivos(e.target.files);
            }

            e.target.value = '';
          }}
        />

        <div className="flex flex-col items-center">

          {/* Icono */}
          <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 flex items-center justify-center mb-5">
            <UploadCloud className="w-8 h-8 text-emerald-400" />
          </div>

          {/* Título */}
          <h3 className="text-lg sm:text-xl font-semibold text-white mb-2">
            Arrastra tus imágenes aquí
          </h3>

          {/* Descripción */}
          <p className="text-sm text-slate-400 mb-2">
            o haz clic para seleccionar imágenes
          </p>

          {/* Formatos */}
          <p className="text-xs text-slate-500">
            JPG, PNG o WEBP
          </p>

        </div>
      </div>

      {/* ======================================================
          BOTÓN DE DIAGNÓSTICO EN TIEMPO REAL
          ====================================================== */}

      <div className="flex justify-center">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onAbrirCamara();
          }}
          className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-600 text-slate-950 font-semibold transition-colors cursor-pointer"
        >
          <ScanSearch className="w-5 h-5" />
          Diagnóstico en tiempo real
        </button>
      </div>

      {/* ======================================================
          PREVISUALIZACIONES
          ====================================================== */}

      {archivos.length > 0 && (
        <div className="space-y-4">

          {/* Cabecera */}
          <div className="flex items-center justify-between">

            <div className="flex items-center gap-2">
              <ImageIcon className="w-5 h-5 text-emerald-400" />

              <span className="text-sm font-medium text-white">
                {archivos.length}{' '}
                {archivos.length === 1
                  ? 'imagen seleccionada'
                  : 'imágenes seleccionadas'}
              </span>
            </div>

            <button
              type="button"
              onClick={limpiarTodo}
              className="text-xs text-slate-400 hover:text-red-400 transition-colors"
            >
              Limpiar todo
            </button>

          </div>

          {/* Imágenes */}
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-4">

            {previews.map((preview, index) => (
              <div
                key={preview}
                className="relative aspect-square rounded-2xl overflow-hidden border border-emerald-500/20 bg-[#121915]"
              >

                <img
                  src={preview}
                  alt={`Vista previa ${index + 1}`}
                  className="w-full h-full object-cover"
                />

                {/* Eliminar */}
                <button
                  type="button"
                  onClick={() => eliminarArchivo(index)}
                  className="absolute top-2 right-2 w-8 h-8 rounded-full bg-black/70 hover:bg-red-500 text-white flex items-center justify-center transition-colors"
                >
                  <X className="w-4 h-4" />
                </button>

                {/* Nombre */}
                <div className="absolute bottom-0 left-0 right-0 bg-black/60 px-2 py-1">
                  <p className="text-xs text-white truncate">
                    {archivos[index].name}
                  </p>
                </div>

              </div>
            ))}

          </div>

          {/* Analizar */}
          <div className="flex justify-center pt-2">

            <Button
              onClick={handleAnalizarClick}
              disabled={isLoading || archivos.length === 0}
              className="min-w-[200px]"
            >
              {isLoading ? (
                <>
                  <Sparkles className="w-5 h-5 mr-2 animate-pulse" />
                  Analizando...
                </>
              ) : (
                <>
                  <Sparkles className="w-5 h-5 mr-2" />
                  Analizar imágenes
                </>
              )}
            </Button>

          </div>

        </div>
      )}

    </div>
  );
};