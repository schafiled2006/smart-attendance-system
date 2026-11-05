import React, { useEffect, useRef, useState, useCallback } from 'react';
import { Camera, CameraOff, RefreshCw } from 'lucide-react';
import { Button } from '../../components/ui/Button';

interface CameraFeedProps {
  onFrameCapture: (blob: Blob) => Promise<void>;
  isProcessing: boolean;
  intervalMs?: number;
  children?: React.ReactNode;
}

export const CameraFeed: React.FC<CameraFeedProps> = ({
  onFrameCapture,
  isProcessing,
  intervalMs = 650,
  children,
}) => {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const [devices, setDevices] = useState<MediaDeviceInfo[]>([]);
  const [selectedDeviceId, setSelectedDeviceId] = useState<string>('');
  const [isCameraActive, setIsCameraActive] = useState<boolean>(false);
  const [cameraError, setCameraError] = useState<string | null>(null);

  // List available video input devices
  const enumerateDevices = useCallback(async () => {
    try {
      const allDevices = await navigator.mediaDevices.enumerateDevices();
      const videoInputs = allDevices.filter((d) => d.kind === 'videoinput');
      setDevices(videoInputs);
      if (videoInputs.length > 0 && !selectedDeviceId) {
        setSelectedDeviceId(videoInputs[0].deviceId);
      }
    } catch (err) {
      console.warn('Failed to enumerate media devices:', err);
    }
  }, [selectedDeviceId]);

  // Start video stream
  const startCamera = useCallback(async () => {
    setCameraError(null);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }

    try {
      const constraints: MediaStreamConstraints = {
        video: selectedDeviceId
          ? { deviceId: { exact: selectedDeviceId }, width: { ideal: 640 }, height: { ideal: 480 } }
          : { width: { ideal: 640 }, height: { ideal: 480 } },
        audio: false,
      };

      const stream = await navigator.mediaDevices.getUserMedia(constraints);
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      setIsCameraActive(true);
      enumerateDevices();
    } catch (err) {
      console.error('Camera stream error:', err);
      setCameraError('دسترسی به دوربین وب‌کم با خطا مواجه شد. لطفاً دسترسی مرورگر را بررسی نمایید.');
      setIsCameraActive(false);
    }
  }, [selectedDeviceId, enumerateDevices]);

  // Stop video stream
  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setIsCameraActive(false);
  }, []);

  useEffect(() => {
    startCamera();
    return () => {
      stopCamera();
    };
  }, [startCamera, stopCamera]);

  // Controlled frame capture loop
  useEffect(() => {
    if (!isCameraActive) return;

    let timer: ReturnType<typeof setTimeout>;

    const captureCycle = async () => {
      const video = videoRef.current;
      const canvas = canvasRef.current;

      if (video && canvas && video.readyState === video.HAVE_ENOUGH_DATA && !isProcessing) {
        const width = video.videoWidth || 640;
        const height = video.videoHeight || 480;

        canvas.width = width;
        canvas.height = height;
        const ctx = canvas.getContext('2d');
        if (ctx) {
          ctx.drawImage(video, 0, 0, width, height);

          canvas.toBlob(
            async (blob) => {
              if (blob) {
                await onFrameCapture(blob);
              }
            },
            'image/jpeg',
            0.85
          );
        }
      }

      timer = setTimeout(captureCycle, intervalMs);
    };

    timer = setTimeout(captureCycle, intervalMs);

    return () => {
      clearTimeout(timer);
    };
  }, [isCameraActive, isProcessing, intervalMs, onFrameCapture]);

  return (
    <div className="space-y-3">
      {/* Video Container with Overlays */}
      <div className="relative rounded-2xl overflow-hidden bg-ink border border-bone shadow-lift aspect-[4/3] flex items-center justify-center">
        {cameraError ? (
          <div className="text-center p-6 space-y-3">
            <CameraOff className="w-10 h-10 text-accent-crimson mx-auto" />
            <p className="text-xs text-white/80 max-w-xs">{cameraError}</p>
            <Button variant="secondary" size="sm" onClick={startCamera}>
              تلاش مجدد
            </Button>
          </div>
        ) : (
          <>
            <video
              ref={videoRef}
              playsInline
              muted
              className="w-full h-full object-cover transform scale-x-[-1]" // Mirrored for human natural selfie-preview
            />
            {/* Hidden capture canvas */}
            <canvas ref={canvasRef} className="hidden" />

            {/* Recognition Face Boxes Overlay */}
            {children}

            {/* Subdued live processing indicator */}
            <div className="absolute top-4 right-4 flex items-center gap-2 px-2.5 py-1 rounded-full bg-ink/70 backdrop-blur-md text-[11px] text-white border border-white/10 select-none">
              <span
                className={`w-2 h-2 rounded-full ${
                  isProcessing ? 'bg-accent-amber animate-ping' : 'bg-accent-emerald'
                }`}
              />
              <span>{isProcessing ? 'در حال انکود چهره...' : 'پخش زنده'}</span>
            </div>
          </>
        )}
      </div>

      {/* Camera Device Controls */}
      <div className="flex items-center justify-between gap-3 text-xs text-ink-muted px-1">
        <div className="flex items-center gap-2">
          <Camera className="w-3.5 h-3.5 text-brand" />
          {devices.length > 1 ? (
            <select
              value={selectedDeviceId}
              onChange={(e) => setSelectedDeviceId(e.target.value)}
              className="bg-surface border border-bone rounded-lg px-2 py-1 text-xs text-ink focus:outline-none focus:border-brand"
            >
              {devices.map((d, i) => (
                <option key={d.deviceId} value={d.deviceId}>
                  {d.label || `دوربین شماره ${i + 1}`}
                </option>
              ))}
            </select>
          ) : (
            <span>دوربین فعال پیش‌فرض سیستم</span>
          )}
        </div>

        <button
          onClick={startCamera}
          className="flex items-center gap-1 hover:text-ink transition-colors"
          title="بازنشانی اتصال دوربین"
        >
          <RefreshCw className="w-3 h-3" />
          <span>تنظیم مجدد</span>
        </button>
      </div>
    </div>
  );
};

