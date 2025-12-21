"use client";

import { useState, useCallback } from "react";

export interface Toast {
  id: string;
  variant: "info" | "success" | "error";
  title: string;
  description?: string;
  duration?: number;
}

export function useDisasterToast() {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((toast: Omit<Toast, "id">) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { ...toast, id }]);
    return id;
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((toast) => toast.id !== id));
  }, []);

  const info = useCallback(
    (title: string, description?: string, duration?: number) => {
      return showToast({ variant: "info", title, description, duration });
    },
    [showToast]
  );

  const success = useCallback(
    (title: string, description?: string, duration?: number) => {
      return showToast({ variant: "success", title, description, duration });
    },
    [showToast]
  );

  const error = useCallback(
    (title: string, description?: string, duration?: number) => {
      return showToast({ variant: "error", title, description, duration });
    },
    [showToast]
  );

  return {
    toasts,
    showToast,
    removeToast,
    info,
    success,
    error,
  };
}
