import React, { useEffect, useRef, useState } from 'react';
import {
  UploadCloud,
  Image as ImageIcon,
  X,
  Sparkles,
  Camera,
  RotateCcw,
} from 'lucide-react';
import { Button } from '../../../shared/ui/Button';

interface DropzoneProps {
  onAnalizar: (archivos: File[]) => void;
  isLoading: boolean;
}

export const Dropzone: React.FC<DropzoneProps> = ({
  onAnalizar,
  isLoading,
}) => {
  const [archivos, setArchivos] = useState<File[]>([]);
  const [previews, setPreviews] = useState<string[]>([]);
  const [isDragOver, setIsDragOver] = useState(false);

  // Cámara
  const [mostrarCamara, setMostrarCamara] = useState(false);
  const [camaraActiva, setCamaraActiva] = useState<'environment' | 'user'>(
    'environment',
  );
  const [errorCamara, setErrorCamara] = useState<string | null>(null);

  const inputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

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

  /*
   * ============================================================
   * CÁMARA
   * ============================================================
   */

  const detenerCamara = () => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => {
        track.stop();
      });

      streamRef.current = null;
    }

    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  const abrirCamara = async () => {
    setErrorCamara(null);
    setMostrarCamara(true);
  };

  const iniciarCamara = async () => {
    try {
      setErrorCamara(null);

      detenerCamara();

      if (!navigator.mediaDevices?.getUserMedia) {
        setErrorCamara(
          'Tu navegador no permite acceder a la cámara desde esta página.',
        );
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: camaraActiva,
          width: {
            ideal: 1920,
          },
          height: {
            ideal: 1080,
          },
        },
        audio: false,
      });

      streamRef.current = stream;

      if (videoRef.current) {
        videoRef.current.srcObject = stream;

        try {
          await videoRef.current.play();
        } catch {
          // Algunos navegadores manejan el play automáticamente.
        }
      }
    } catch (error) {
      console.error('Error al acceder a la cámara:', error);

      setErrorCamara(
        'No se pudo acceder a la cámara. Verifica que hayas permitido el acceso a la cámara.',
      );
    }
  };

  const cerrarCamara = () => {
    detenerCamara();
    setMostrarCamara(false);
    setErrorCamara(null);
  };

  const cambiarCamara = async () => {
    const nuevaCamara =
      camaraActiva === 'environment' ? 'user' : 'environment';

    setCamaraActiva(nuevaCamara);
  };

  const capturarFoto = () => {
    const video = videoRef.current;

    if (!video) return;

    if (video.readyState < 2) {
      setErrorCamara('La cámara todavía no está lista.');
      return;
    }

    const canvas = document.createElement('canvas');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;

    const context = canvas.getContext('2d');

    if (!context) {
      setErrorCamara('No se pudo capturar la imagen.');
      return;
    }

    context.drawImage(
      video,
      0,
      0,
      canvas.width,
      canvas.height,
    );

    canvas.toBlob(
      (blob) => {
        if (!blob) {
          setErrorCamara('No se pudo generar la fotografía.');
          return;
        }

        const nombreArchivo = `foto-camara-${Date.now()}.jpg`;

        const archivo = new File(
          [blob],
          nombreArchivo,
          {
            type: 'image/jpeg',
          },
        );

        agregarArchivos([archivo]);

        cerrarCamara();
      },
      'image/jpeg',
      0.92,
    );
  };

  /*
   * ============================================================
   * EFECTOS DE CÁMARA
   * ============================================================
   */

  useEffect(() => {
    if (mostrarCamara) {
      iniciarCamara();
    }

    return () => {
      detenerCamara();
    };
  }, [mostrarCamara, camaraActiva]);

  useEffect(() => {
    return () => {
      detenerCamara();

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
          BOTÓN DE CÁMARA
          ====================================================== */}

      <div className="flex justify-center">
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            abrirCamara();
          }}
          className="inline-flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 active:bg-emerald-600 text-slate-950 font-semibold transition-colors cursor-pointer"
        >
          <Camera className="w-5 h-5" />
          Tomar foto
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

      {/* ======================================================
          MODAL DE CÁMARA
          ====================================================== */}

      {mostrarCamara && (
        <div
          className="fixed inset-0 z-[100] bg-black flex flex-col"
          onClick={(e) => e.stopPropagation()}
        >

          {/* Cabecera */}
          <div className="flex items-center justify-between px-4 py-4 bg-black/80 text-white">

            <h2 className="text-lg font-semibold">
              Tomar foto
            </h2>

            <button
              type="button"
              onClick={cerrarCamara}
              className="w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center transition-colors"
            >
              <X className="w-6 h-6" />
            </button>

          </div>

          {/* Vista de cámara */}
          <div className="relative flex-1 flex items-center justify-center bg-black overflow-hidden">

            {errorCamara ? (
              <div className="px-6 text-center">

                <Camera className="w-16 h-16 text-red-400 mx-auto mb-4" />

                <p className="text-white text-lg font-semibold mb-2">
                  No se pudo abrir la cámara
                </p>

                <p className="text-slate-400 text-sm max-w-sm">
                  {errorCamara}
                </p>

              </div>
            ) : (
              <video
                ref={videoRef}
                autoPlay
                playsInline
                muted
                className="w-full h-full object-contain"
              />
            )}

            {/* Guía para colocar la planta/palta */}
            {!errorCamara && (
              <div className="absolute inset-0 pointer-events-none flex items-center justify-center">

                <div className="w-[75%] h-[60%] border-2 border-emerald-400/70 rounded-3xl shadow-[0_0_30px_rgba(52,211,153,0.15)]" />

              </div>
            )}

          </div>

          {/* Controles */}
          <div className="bg-black/90 px-6 py-6">

            <div className="flex items-center justify-center gap-8">

              {/* Cambiar cámara */}
              <button
                type="button"
                onClick={cambiarCamara}
                disabled={!!errorCamara}
                className="w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 disabled:opacity-40 text-white flex items-center justify-center transition-colors"
                title="Cambiar cámara"
              >
                <RotateCcw className="w-6 h-6" />
              </button>

              {/* Capturar */}
              <button
                type="button"
                onClick={capturarFoto}
                disabled={!!errorCamara}
                className="w-20 h-20 rounded-full bg-white border-4 border-emerald-400 hover:scale-105 active:scale-95 disabled:opacity-40 transition-transform flex items-center justify-center"
                title="Capturar foto"
              >
                <div className="w-14 h-14 rounded-full bg-emerald-500" />
              </button>

              {/* Espacio para mantener centrado */}
              <div className="w-12 h-12" />

            </div>

            <p className="text-center text-slate-400 text-xs mt-4">
              Coloca la hoja o fruto dentro del recuadro y toma la foto
            </p>

          </div>

        </div>
      )}

    </div>
  );
};