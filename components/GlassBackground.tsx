"use client";

import { useEffect, useRef } from "react";

interface WaveParticle {
  xPosition: number;
  phase: number;
  velocity: number;
  spread: number;
  depth: number;
  radius: number;
  opacity: number;
}

export default function GlassBackground() {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const renderSurface = canvas as HTMLCanvasElement;
    const context = canvas.getContext("2d", { alpha: true })!;

    const motionPreference = window.matchMedia("(prefers-reduced-motion: reduce)");
    let frameId = 0;
    let lastFrameTime = 0;
    let canvasWidth = 0;
    let canvasHeight = 0;
    let particles: WaveParticle[] = [];

    function waveHeight(xPosition: number, time: number, depth = 1) {
      const progress = xPosition / Math.max(canvasWidth, 1);
      const amplitude = Math.min(canvasHeight * 0.095, 82);
      return canvasHeight * 0.52
        + Math.sin(progress * Math.PI * 2 - time * 0.52 * depth) * amplitude * 0.58
        + Math.sin(progress * Math.PI * 4 + time * 0.31 * depth) * amplitude * 0.3
        + Math.sin(progress * Math.PI * 6 - time * 0.2 * depth) * amplitude * 0.12;
    }

    function resizeCanvas() {
      const pixelRatio = Math.min(window.devicePixelRatio || 1, 1.5);
      canvasWidth = window.innerWidth;
      canvasHeight = window.innerHeight;
      renderSurface.width = Math.round(canvasWidth * pixelRatio);
      renderSurface.height = Math.round(canvasHeight * pixelRatio);
      context.setTransform(pixelRatio, 0, 0, pixelRatio, 0, 0);

      const particleCount = Math.max(150, Math.min(720, Math.round((canvasWidth * canvasHeight) / 3000)));
      particles = Array.from({ length: particleCount }, () => ({
        xPosition: Math.random() * canvasWidth,
        phase: Math.random() * Math.PI * 2,
        velocity: 8 + Math.random() * 34,
        spread: (Math.random() - 0.5) * Math.min(canvasHeight * 0.19, 150),
        depth: 0.58 + Math.random() * 0.82,
        radius: Math.random() > 0.94 ? 1.7 : 0.55 + Math.random() * 0.8,
        opacity: 0.16 + Math.random() * 0.54,
      }));

      renderFrame(0, false);
    }

    function drawEnergyLines(time: number) {
      const lineColors = [
        "rgba(0, 229, 255, 0.16)",
        "rgba(85, 199, 255, 0.28)",
        "rgba(37, 139, 255, 0.34)",
        "rgba(85, 199, 255, 0.18)",
        "rgba(0, 229, 255, 0.12)",
      ];

      context.save();
      context.globalCompositeOperation = "lighter";
      for (let lineIndex = 0; lineIndex < lineColors.length; lineIndex += 1) {
        context.beginPath();
        for (let sampleIndex = 0; sampleIndex <= 96; sampleIndex += 1) {
          const xPosition = (sampleIndex / 96) * canvasWidth;
          const lineOffset = (lineIndex - 2) * Math.min(canvasHeight * 0.012, 10);
          const yPosition = waveHeight(xPosition, time, 0.8 + lineIndex * 0.1) + lineOffset;
          if (sampleIndex === 0) context.moveTo(xPosition, yPosition);
          else context.lineTo(xPosition, yPosition);
        }
        context.strokeStyle = lineColors[lineIndex];
        context.lineWidth = lineIndex === 2 ? 1.7 : 0.8;
        context.stroke();
      }
      context.restore();
    }

    function drawParticles(time: number, moveParticles: boolean, deltaSeconds: number) {
      context.save();
      context.globalCompositeOperation = "lighter";
      for (let particleIndex = 0; particleIndex < particles.length; particleIndex += 1) {
        const particle = particles[particleIndex];
        if (moveParticles) {
          particle.xPosition += particle.velocity * deltaSeconds;
          if (particle.xPosition > canvasWidth + 2) particle.xPosition = -2;
        }

        const drift = Math.sin(particle.phase + time * particle.depth * 1.4) * particle.spread;
        const yPosition = waveHeight(particle.xPosition, time, particle.depth) + drift;
        const hue = particleIndex % 5 === 0 ? "0, 229, 255" : "85, 199, 255";

        if (particleIndex % 4 === 0) {
          context.beginPath();
          context.moveTo(particle.xPosition, yPosition);
          context.lineTo(particle.xPosition - particle.velocity * 0.22, yPosition - 1.5);
          context.strokeStyle = `rgba(${hue}, ${particle.opacity * 0.28})`;
          context.lineWidth = particle.radius * 0.65;
          context.stroke();
        }

        context.beginPath();
        context.arc(particle.xPosition, yPosition, particle.radius, 0, Math.PI * 2);
        context.fillStyle = `rgba(${hue}, ${particle.opacity})`;
        context.fill();
      }
      context.restore();
    }

    function renderFrame(timestamp: number, moveParticles: boolean) {
      const time = timestamp / 1000;
      const deltaSeconds = lastFrameTime ? Math.min((timestamp - lastFrameTime) / 1000, 0.05) : 0;
      lastFrameTime = timestamp;
      context.clearRect(0, 0, canvasWidth, canvasHeight);

      const glow = context.createRadialGradient(
        canvasWidth * 0.52,
        canvasHeight * 0.52,
        0,
        canvasWidth * 0.52,
        canvasHeight * 0.52,
        canvasWidth * 0.58,
      );
      glow.addColorStop(0, "rgba(22, 119, 255, 0.12)");
      glow.addColorStop(0.48, "rgba(8, 50, 104, 0.07)");
      glow.addColorStop(1, "rgba(5, 11, 24, 0)");
      context.fillStyle = glow;
      context.fillRect(0, 0, canvasWidth, canvasHeight);

      drawEnergyLines(time);
      drawParticles(time, moveParticles, deltaSeconds);
    }

    function animate(timestamp: number) {
      if (document.hidden) return;
      if (timestamp - lastFrameTime >= 1000 / 30) renderFrame(timestamp, true);
      frameId = window.requestAnimationFrame(animate);
    }

    function updateMotionPreference() {
      window.cancelAnimationFrame(frameId);
      lastFrameTime = 0;
      if (motionPreference.matches) renderFrame(0, false);
      else if (!document.hidden) frameId = window.requestAnimationFrame(animate);
    }

    function handleVisibilityChange() {
      window.cancelAnimationFrame(frameId);
      if (!document.hidden && !motionPreference.matches) {
        frameId = window.requestAnimationFrame(animate);
      }
    }

    resizeCanvas();
    if (!motionPreference.matches) frameId = window.requestAnimationFrame(animate);
    window.addEventListener("resize", resizeCanvas, { passive: true });
    document.addEventListener("visibilitychange", handleVisibilityChange);
    motionPreference.addEventListener("change", updateMotionPreference);

    return () => {
      window.removeEventListener("resize", resizeCanvas);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
      motionPreference.removeEventListener("change", updateMotionPreference);
      window.cancelAnimationFrame(frameId);
    };
  }, []);

  return (
    <div className="bg-energy-scene" aria-hidden="true">
      <canvas ref={canvasRef} />
    </div>
  );
}
