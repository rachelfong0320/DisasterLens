import type React from "react";
export default function PageContainer({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <main className="min-h-screen bg-background">
      {/* Subtle gradient background */}
      <div className="absolute inset-0 bg-gradient-to-br from-background via-background to-secondary/20 pointer-events-none" />

      <div className="relative px-4 sm:px-6 lg:px-8 py-12 sm:py-16 lg:py-20">
        <div className="max-w-4xl mx-auto">
          {/* Title section with refined typography */}
          <div className="mb-10 sm:mb-14">
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold tracking-tight text-balance leading-[1.1] bg-gradient-to-br from-foreground to-foreground/70 bg-clip-text text-transparent">
              {title}
            </h1>
            <div className="mt-4 h-1 w-20 bg-gradient-to-r from-accent to-accent/40 rounded-full" />
          </div>

          {/* Content area with elegant card styling */}
          <div className="bg-card border border-border rounded-2xl shadow-sm overflow-hidden">
            <div className="px-6 sm:px-10 lg:px-14 py-8 sm:py-12">
              <div className="prose prose-neutral dark:prose-invert max-w-none prose-headings:font-bold prose-headings:tracking-tight prose-h2:text-3xl prose-h2:mt-10 prose-h2:mb-6 prose-h3:text-2xl prose-h3:mt-8 prose-h3:mb-4 prose-p:leading-relaxed prose-p:text-foreground/90 prose-a:text-accent prose-a:no-underline hover:prose-a:underline prose-a:font-medium prose-strong:text-foreground prose-strong:font-semibold prose-code:text-accent prose-code:bg-muted prose-code:px-1.5 prose-code:py-0.5 prose-code:rounded-md prose-code:font-mono prose-code:text-sm prose-code:before:content-none prose-code:after:content-none prose-pre:bg-muted prose-pre:border prose-pre:border-border">
                {children}
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
