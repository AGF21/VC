'use client';

import type { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface HeroProps {
  title: ReactNode;
  description: string;
  actions?: ReactNode;
  className?: string;
  showLogo?: boolean;
}

export function Hero({ title, description, actions, className, showLogo = true }: HeroProps) {
  return (
    <section className={cn('relative py-12 sm:py-16 md:py-20 lg:py-24', className)}>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-center">
        {/* Left side - Content */}
        <div className="space-y-6 lg:pr-8">
          {showLogo && (
            <div className="flex lg:justify-start justify-center mb-6">
              <span style={{ fontFamily: 'Impact, Haettenschweiler, "Arial Narrow Bold", sans-serif', color: 'white', fontSize: '3rem', letterSpacing: '0.05em' }}>zest</span>
            </div>
          )}
          <h1 className="text-5xl sm:text-6xl md:text-7xl lg:text-8xl font-bold leading-tight text-left">
            {title}
          </h1>
          <p className="text-lg sm:text-xl md:text-2xl text-foreground/70 max-w-xl text-left">
            {description}
          </p>
        </div>

        {/* Right side - Actions */}
        <div className="flex flex-col items-start lg:items-end gap-4">{actions}</div>
      </div>
    </section>
  );
}
