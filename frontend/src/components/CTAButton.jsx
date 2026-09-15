import React from 'react';

const CTAButton = ({ children, variant = 'primary', onClick, className = '' }) => {
  const baseClass = 'cta-button';
  const variantClass = `${baseClass}--${variant}`;

  return (
    <button
      className={`${baseClass} ${variantClass} ${className}`}
      onClick={onClick}
    >
      <span className="cta-button__text">{children}</span>
      {variant === 'primary' && (
        <div className="cta-button__glow" aria-hidden="true"></div>
      )}
    </button>
  );
};

export default CTAButton;
