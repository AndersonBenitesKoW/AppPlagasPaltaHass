import React, { useRef, useState } from 'react';
import { UploadCloud, Image as ImageIcon, X, Sparkles, FolderUp } from 'lucide-react';
import { Button } from '../../../shared/ui/Button';

interface DropzoneProps {
  onAnalizar: (archivos: File[]) => void;
  isLoading: boolean;
}

export const Dropzone: React.FC<DropzoneProps> = ({ onAnalizar, isLoading }) => {
  const [archivos, setArchivos] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const agregarArchivos = (nuevos: FileList | File[]) => {
    const permitidos = Array.from(nuevos).filter((f) =>
      ['image/jpeg', 'image/png', 'image/webp'].includes(f.type),
    );

    if (permitidos.length === 0) return;

    const actualizados = [...archivos, ...permitidos];
    setArchivos(actualizados);

    // Generar previews
    const nuevosPreviews = permitidos.map((f) => URL.createObjectURL(f));
    setPreviews((prev) => [...prev, ...nuevosPreviews]);
  };

  const eliminarArchivo = (index: number) => {
    URL.revokeObjectURL(previews[index]);
    setArchivos((prev) => prev.filter((_, i) => i !== index));
    setPreviews((prev) => prev.filter((_, i) => i !== index));
  };

  const limpiarTodo = () => {
    previews.forEach((p) => URL.revokeObjectURL(p));
    setArchivos([]);
    setPreviews([]);
  };

  const handleDrop = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
    if (e.dataTransfer.files) {
      agregarArchivos(e.dataTransfer.files);
    }
  };

  const handleAnalizarClick = () => {
    if (archivos.length > 0) {
      onAnalizar(archivos);
    }
  };

  return (
    <div className="space-y-4">
      {/* Zona de arrastrar y soltar */}
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
        <input
          ref={inputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple
          className="hidden"
          onChange={(e) => e.target.files && agregarArchivos(e.target.files)}
        />

        <div className="flex flex-col items-center justify-center space-y-4">
          <div className="relative">
            <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400 shadow-inner group-hover:scale-110 transition-transform">
              <UploadCloud className="w-8 h-8 animate-bounce-subtle" />
            </div>
            <Sparkles className="w-5 h-5 text-emerald-300 absolute -top-1 -right-1 animate-pulse" />
          </div>

          <div className="space-y-1">
            <p className="text-lg font-semibold text-slate-100">
              Arrastra una o varias fotos de hojas de palta Hass
            </p>
            <p className="text-sm text-slate-400">
              o haz clic para explorar en tu dispositivo (JPEG, PNG o WEBP hasta 10 MB)
            </p>
          </div>

          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-medium text-emerald-400">
            <FolderUp className="w-3.5 h-3.5" />
            Soporta análisis individual o en lote
          </div>
        </div>
      </div>

      {/* Miniaturas de imágenes seleccionadas */}
      {archivos.length > 0 && (
        <div className="p-4 rounded-2xl bg-[#111915] border border-dark-border space-y-4 animate-fade-in">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-slate-200 flex items-center gap-2">
              <ImageIcon className="w-4 h-4 text-emerald-400" />
              {archivos.length} {archivos.length === 1 ? 'imagen lista' : 'imágenes listas'} para
              diagnóstico
            </span>
            <button
              onClick={limpiarTodo}
              className="text-xs text-rose-400 hover:text-rose-300 hover:underline cursor-pointer"
            >
              Quitar todas
            </button>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
            {previews.map((preview, index) => (
              <div
                key={index}
                className="relative group rounded-xl overflow-hidden aspect-square border border-dark-border bg-black/40"
              >
                <img
                  src={preview}
                  alt={`Previsualización ${index + 1}`}
                  className="w-full h-full object-cover"
                />
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation();
                    eliminarArchivo(index);
                  }}
                  className="absolute top-1.5 right-1.5 p-1 rounded-full bg-black/75 hover:bg-rose-600 text-white transition-colors cursor-pointer"
                  title="Eliminar foto"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
                <div className="absolute bottom-0 inset-x-0 p-1 bg-black/70 text-[10px] text-slate-300 truncate text-center">
                  {archivos[index]?.name}
                </div>
              </div>
            ))}
          </div>

          <div className="pt-2 flex justify-end">
            <Button
              onClick={handleAnalizarClick}
              isLoading={isLoading}
              size="lg"
              className="w-full sm:w-auto shadow-xl"
            >
              <Sparkles className="w-5 h-5 mr-1" />
              {archivos.length === 1
                ? 'Analizar Hoja con IA'
                : `Analizar ${archivos.length} Hojas en Lote`}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
};
