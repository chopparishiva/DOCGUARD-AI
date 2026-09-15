import React from 'react';

const DemoIndicator = ({ mode = 'demo' }) => {
  const label = mode === 'live' ? 'LIVE ANALYSIS' : 'DEMO MODE';
  const cls = mode === 'live' ? 'demo-indicator demo-indicator--live' : 'demo-indicator';
  return (
    <div className={cls} role="status" aria-label={label + ' active'}>
      <span className="demo-indicator__dot" aria-hidden="true"></span>
      <span className="demo-indicator__text">{label}</span>
    </div>
  );
};

export default DemoIndicator;