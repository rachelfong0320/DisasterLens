"use client"

import { useState } from "react";

export function useReportGenerator() {
  const [isGenerating, setIsGenerating] = useState(false);

  const generateReport = async () => {
    setIsGenerating(true);
    
    // Small delay to ensure any "Processing" states are rendered if needed
    setTimeout(() => {
      window.print();
      setIsGenerating(false);
    }, 100);
  };

  return { generateReport, isGenerating };
}