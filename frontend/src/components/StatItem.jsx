import React from 'react';

const StatItem = ({ value, label }) => {
  return (
    <div className="stat-item">
      <span className="stat-value">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
};

export default StatItem;
