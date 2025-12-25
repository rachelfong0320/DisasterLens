"use client";

import Link from "next/link";
import { Flame, Zap, AlertTriangle, Home, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <main className="min-h-screen bg-background flex items-center justify-center relative overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-destructive/5 to-accent/10 pointer-events-none" />

      {/* Animated floating disaster elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <Flame className="absolute top-[20%] left-[15%] w-8 h-8 text-destructive/20 animate-bounce-slow" />
        <Zap className="absolute top-[60%] right-[20%] w-6 h-6 text-accent/30 animate-pulse" />
        <AlertTriangle className="absolute bottom-[30%] left-[25%] w-7 h-7 text-destructive/25 animate-bounce-slow" />
        <Flame className="absolute top-[40%] right-[10%] w-5 h-5 text-destructive/15 animate-pulse" />
      </div>

      <div className="relative px-4 sm:px-6 lg:px-8 py-12 max-w-3xl mx-auto text-center">
        {/* Main disaster illustration */}
        <div className="mb-8 flex justify-center items-center gap-4">
          <div className="relative">
            {/* Meteor/crash effect */}
            <div className="absolute -top-6 -left-6 w-24 h-24 bg-destructive/20 rounded-full blur-2xl animate-pulse" />
            <div className="relative bg-card border-2 border-destructive/30 rounded-3xl p-8 shadow-xl">
              <div className="flex items-center justify-center gap-3">
                <Flame className="w-16 h-16 text-destructive animate-bounce-slow" />
                <span className="text-7xl sm:text-8xl font-bold bg-gradient-to-br from-destructive to-destructive/60 bg-clip-text text-transparent">
                  404
                </span>
                <Zap className="w-16 h-16 text-accent animate-pulse" />
              </div>
            </div>
            <div className="absolute -bottom-4 -right-4 w-20 h-20 bg-accent/20 rounded-full blur-xl animate-pulse" />
          </div>
        </div>

        {/* Error message */}
        <div className="mb-8">
          <h1 className="text-3xl sm:text-4xl lg:text-5xl font-bold tracking-tight mb-4 bg-gradient-to-br from-foreground to-foreground/70 bg-clip-text text-transparent text-balance">
            Houston, we have a problem
          </h1>
          <div className="flex items-center justify-center gap-2 text-destructive/80 mb-6">
            <AlertTriangle className="w-5 h-5" />
            <p className="text-lg sm:text-xl font-medium">
              Page crashed and burned
            </p>
            <AlertTriangle className="w-5 h-5" />
          </div>
          <p className="text-muted-foreground text-base sm:text-lg max-w-md mx-auto leading-relaxed">
            The page you're looking for has been caught in a meteor shower and
            is currently unavailable.
          </p>
        </div>

        {/* Action buttons */}
        <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
          <Link
            href="/"
            className="group inline-flex items-center gap-2 bg-accent hover:bg-accent/90 text-accent-foreground px-6 py-3 rounded-xl font-semibold transition-all duration-200 shadow-md hover:shadow-lg hover:scale-105"
          >
            <Home className="w-5 h-5 group-hover:scale-110 transition-transform" />
            Return to Safety
          </Link>
          <button
            onClick={() => window.history.back()}
            className="group inline-flex items-center gap-2 bg-card hover:bg-muted text-foreground border-2 border-border hover:border-accent/50 px-6 py-3 rounded-xl font-semibold transition-all duration-200 hover:scale-105"
          >
            <ArrowLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
            Go Back
          </button>
        </div>

        {/* Additional helpful info */}
        <div className="mt-12 pt-8 border-t border-border/50">
          <p className="text-sm text-muted-foreground">
            Error Code:{" "}
            <span className="font-mono text-destructive font-semibold">
              404_DISASTER_DETECTED
            </span>
          </p>
        </div>
      </div>
    </main>
  );
}
