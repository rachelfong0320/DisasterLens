"use client";

import * as React from "react";
import { X, AlertTriangle, CheckCircle2, AlertCircle } from "lucide-react";

export type ToastVariant = "info" | "success" | "error";

interface DisasterToastProps {
  variant: ToastVariant;
  title: string;
  description?: string;
  onClose: () => void;
  duration?: number;
}

const variantStyles = {
  info: {
    bg: "#1e3a8a",
    border: "#3b82f6",
    text: "#dbeafe",
    icon: AlertCircle,
    stripe: "#60a5fa",
  },
  success: {
    bg: "#287245ff",
    border: "#22c55e",
    text: "#dcfce7",
    icon: CheckCircle2,
    stripe: "#4ade80",
  },
  error: {
    bg: "#991b1b",
    border: "#ef4444",
    text: "#fee2e2",
    icon: AlertTriangle,
    stripe: "#f87171",
  },
};

export function DisasterToast({
  variant,
  title,
  description,
  onClose,
  duration = 5000,
}: DisasterToastProps) {
  const styles = variantStyles[variant];
  const Icon = styles.icon;

  React.useEffect(() => {
    if (duration) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  return (
    <div
      className="relative w-full max-w-md overflow-hidden rounded-lg border-2 p-4 animate-in slide-in-from-top-full duration-300"
      style={{
        backgroundColor: styles.bg,
        borderColor: styles.border,
        color: styles.text,
        boxShadow: `0 10px 15px -3px ${styles.border}33`,
      }}
      role="alert"
    >
      {/* Emergency stripe pattern */}
      <div
        className="absolute inset-x-0 top-0 h-1 bg-repeat-x"
        style={{
          backgroundImage: `repeating-linear-gradient(45deg, transparent, transparent 10px, ${styles.stripe}4D 10px, ${styles.stripe}4D 20px)`,
        }}
      />

      <div className="flex items-start gap-3">
        {/* Icon container with glow effect */}
        <div
          className="flex-shrink-0 rounded-md p-2"
          style={{ backgroundColor: `${styles.text}33` }}
        >
          <Icon className="h-5 w-5" strokeWidth={2.5} />
        </div>

        {/* Content */}
        <div className="flex-1 space-y-1">
          <h3 className="font-bold text-base leading-tight tracking-tight">
            {title}
          </h3>
          {description && (
            <p className="text-sm opacity-90 leading-relaxed">{description}</p>
          )}
        </div>

        {/* Close button */}
        <button
          onClick={onClose}
          className="flex-shrink-0 rounded-sm opacity-70 transition-opacity hover:opacity-100 focus:opacity-100 focus:outline-none focus:ring-2 focus:ring-offset-2"
          style={{ boxShadow: `0 0 0 2px ${styles.text}` }}
          aria-label="Close notification"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {/* Progress bar */}
      {duration && (
        <div
          className="absolute inset-x-0 bottom-0 h-1 overflow-hidden rounded-b-lg"
          style={{ backgroundColor: `${styles.text}1A` }}
        >
          <div
            className="h-full"
            style={{
              backgroundColor: `${styles.stripe}66`,
              animation: `shrink ${duration}ms linear forwards`,
            }}
          />
        </div>
      )}

      <style jsx>{`
        @keyframes shrink {
          from {
            width: 100%;
          }
          to {
            width: 0%;
          }
        }
      `}</style>
    </div>
  );
}

// Toast Container Component
export function DisasterToastContainer({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div
      className="fixed right-4 z-50 flex flex-col gap-3 w-full max-w-md pointer-events-none"
      style={{ top: "calc(64px + 16px)" }}
    >
      <div className="pointer-events-auto">{children}</div>
    </div>
  );
}
