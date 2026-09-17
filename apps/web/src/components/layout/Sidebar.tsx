import React from 'react';
import { NavLink } from 'react-router-dom';
import { useShellContext } from '../../state/shell/shell-context';

export interface NavItem {
  id: string;
  label: string;
  path: string;
  icon?: string;
  description?: string;
}

export interface SidebarProps {
  seriesId: string;
  items?: NavItem[];
}

export const Sidebar: React.FC<SidebarProps> = ({
  seriesId,
  items = [
    { id: 'overview', label: 'Overview', path: `/series/${seriesId}`, icon: '☲', description: 'Narrative summary & overview' },
    { id: 'timeline', label: 'Timeline Feed', path: `/series/${seriesId}/timeline`, icon: '◷', description: 'Chronological event stream' },
    { id: 'characters', label: 'Characters', path: `/series/${seriesId}/characters`, icon: '♟', description: 'Entity arcs and state profiles' },
    { id: 'graph', label: 'Intelligence Graph', path: `/series/${seriesId}/graph`, icon: '⚯', description: 'Network topology and flows' },
    { id: 'causality', label: 'Causal Chains', path: `/series/${seriesId}/causality`, icon: '↯', description: 'Deterministic cause and effect' },
    { id: 'narrative', label: 'Narrative Arc', path: `/series/${seriesId}/narrative`, icon: '☍', description: 'Story phases and character trajectories' },
    { id: 'what-if', label: 'What If', path: `/series/${seriesId}/what-if`, icon: '⑂', description: 'Counterfactual sandbox & divergence' },
  ],
}) => {
  const { isSidebarCollapsed } = useShellContext();

  return (
    <div
      aria-label="Story Intelligence Sidebar"
      style={{
        width: isSidebarCollapsed ? '64px' : 'var(--tsi-sidebar-width)',
        backgroundColor: 'var(--tsi-surface-primary)',
        borderRight: '1px solid var(--tsi-border-subtle)',
        display: 'flex',
        flexDirection: 'column',
        flexShrink: 0,
        overflowY: 'auto',
        overflowX: 'hidden',
        transition: 'width 0.18s cubic-bezier(0.16, 1, 0.3, 1)',
      }}
    >
      {!isSidebarCollapsed && (
        <div style={{ padding: '16px 12px 8px' }}>
          <span
            style={{
              fontSize: '0.6875rem',
              textTransform: 'uppercase',
              letterSpacing: '0.08em',
              color: 'var(--tsi-text-muted)',
              paddingLeft: '8px',
            }}
          >
            Investigation Views
          </span>
        </div>
      )}

      <nav
        style={{
          display: 'flex',
          flexDirection: 'column',
          gap: '3px',
          padding: isSidebarCollapsed ? '16px 8px 8px' : '0 8px',
        }}
      >
        {items.map((item) => (
          <NavLink
            key={item.id}
            to={item.path}
            end={item.id === 'overview'}
            title={isSidebarCollapsed ? `${item.label} — ${item.description || ''}` : undefined}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: isSidebarCollapsed ? '0' : '10px',
              justifyContent: isSidebarCollapsed ? 'center' : 'flex-start',
              padding: isSidebarCollapsed ? '10px 0' : '8px 12px',
              borderRadius: 'var(--tsi-radius-md)',
              fontSize: '0.875rem',
              fontWeight: isActive ? 600 : 400,
              color: isActive ? 'var(--tsi-text-primary)' : 'var(--tsi-text-secondary)',
              backgroundColor: isActive ? 'var(--tsi-surface-elevated)' : 'transparent',
              borderLeft: isActive
                ? '3px solid var(--tsi-accent-primary)'
                : '3px solid transparent',
              textDecoration: 'none',
              transition: 'all 0.12s ease',
              position: 'relative',
            })}
          >
            {item.icon && (
              <span
                style={{
                  fontSize: '1.125rem',
                  color: 'var(--tsi-accent-primary)',
                  width: '20px',
                  textAlign: 'center',
                  flexShrink: 0,
                }}
              >
                {item.icon}
              </span>
            )}
            {!isSidebarCollapsed && (
              <div style={{ display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
                <span style={{ whiteSpace: 'nowrap', textOverflow: 'ellipsis', overflow: 'hidden' }}>
                  {item.label}
                </span>
              </div>
            )}
          </NavLink>
        ))}
      </nav>
    </div>
  );
};
