"use client";

import React from "react";
import { ThemeProvider } from "@/context/ThemeContext";
import { LayoutProvider } from "@/context/LayoutContext";
import { ToastProvider } from "@/context/ToastContext";
import { ErrorBoundary } from "@/components/ui/ErrorBoundary";
import { Navbar } from "./Navbar";
import { Sidebar } from "./Sidebar";
import { SearchModal } from "@/components/ui/SearchModal";

interface MainLayoutProps {
  children: React.ReactNode;
}

export const MainLayoutContent: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen flex flex-col bg-slate-50 dark:bg-[#0b0f19] text-slate-900 dark:text-slate-100 transition-colors duration-200">
      <Navbar />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 p-4 sm:p-6 lg:p-8 overflow-y-auto max-w-7xl mx-auto w-full">
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </div>
      <SearchModal />
    </div>
  );
};

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <ThemeProvider>
      <LayoutProvider>
        <ToastProvider>
          <MainLayoutContent>{children}</MainLayoutContent>
        </ToastProvider>
      </LayoutProvider>
    </ThemeProvider>
  );
};
