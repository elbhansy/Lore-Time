import React, { createContext, useContext, useState, ReactNode, useCallback } from 'react';

/**
 * Phase 6.2 Shell Context & Inspector State Contract.
 * 
 * Manages:
 * - Sidebar collapsed/expanded state (with responsive awareness)
 * - Inspector panel open/closed state & contextual content payload
 * - Command palette open/closed state
 * - Strict presentation boundaries: zero story or causal domain intelligence here.
 */

export interface InspectorPayload {
  title: string;
  subtitle?: string;
  badge?: {
    label: string;
    variant?: 'default' | 'neutral' | 'success' | 'warning' | 'error' | 'temporal';
  };
  content: ReactNode;
}

export interface ShellContextState {
  // Sidebar
  isSidebarCollapsed: boolean;
  toggleSidebar: () => void;
  setSidebarCollapsed: (collapsed: boolean) => void;

  // Inspector
  isInspectorOpen: boolean;
  inspectorPayload: InspectorPayload | null;
  openInspector: (payload: InspectorPayload) => void;
  closeInspector: () => void;
  toggleInspector: () => void;

  // Command Palette
  isCommandPaletteOpen: boolean;
  openCommandPalette: () => void;
  closeCommandPalette: () => void;
  toggleCommandPalette: () => void;
}

const ShellContext = createContext<ShellContextState | undefined>(undefined);

export interface ShellProviderProps {
  children: ReactNode;
}

export const ShellProvider: React.FC<ShellProviderProps> = ({ children }) => {
  const [isSidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [isInspectorOpen, setIsInspectorOpen] = useState(false);
  const [inspectorPayload, setInspectorPayload] = useState<InspectorPayload | null>(null);
  const [isCommandPaletteOpen, setIsCommandPaletteOpen] = useState(false);

  const toggleSidebar = useCallback(() => {
    setSidebarCollapsed((prev) => !prev);
  }, []);

  const openInspector = useCallback((payload: InspectorPayload) => {
    setInspectorPayload(payload);
    setIsInspectorOpen(true);
  }, []);

  const closeInspector = useCallback(() => {
    setIsInspectorOpen(false);
  }, []);

  const toggleInspector = useCallback(() => {
    setIsInspectorOpen((prev) => !prev);
  }, []);

  const openCommandPalette = useCallback(() => {
    setIsCommandPaletteOpen(true);
  }, []);

  const closeCommandPalette = useCallback(() => {
    setIsCommandPaletteOpen(false);
  }, []);

  const toggleCommandPalette = useCallback(() => {
    setIsCommandPaletteOpen((prev) => !prev);
  }, []);

  const value: ShellContextState = {
    isSidebarCollapsed,
    toggleSidebar,
    setSidebarCollapsed,
    isInspectorOpen,
    inspectorPayload,
    openInspector,
    closeInspector,
    toggleInspector,
    isCommandPaletteOpen,
    openCommandPalette,
    closeCommandPalette,
    toggleCommandPalette,
  };

  return <ShellContext.Provider value={value}>{children}</ShellContext.Provider>;
};

export const useShellContext = (): ShellContextState => {
  const ctx = useContext(ShellContext);
  if (!ctx) {
    throw new Error('useShellContext must be used within a ShellProvider');
  }
  return ctx;
};
