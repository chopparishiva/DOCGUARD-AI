import React from 'react';
import CTAButton from './CTAButton';
import StatItem from './StatItem';

const Hero = ({ onAnalyzeClick, onSeeItInAction }) => {
  const stats = [
    { value: '18+', label: 'API endpoints analyzed' },
    { value: '94%', label: 'documentation synchronization' },
    { value: '24/7', label: 'API change monitoring' },
  ];

  return (
    <section className="hero">
      {/* Hero video treatment - CSS gradient simulation */}
      <div className="hero-background" aria-hidden="true">
        <div className="hero-gradient"></div>
      </div>

      {/* Hero content */}
      <div className="hero-content">
        {/* Badge */}
        <div className="hero-badge animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
          <span className="badge-text">Autonomous API Documentation Agent</span>
        </div>

        {/* Main heading with Instrument Serif italic treatment */}
        <h1 className="hero-title animate-fade-in-up" style={{ animationDelay: '0.2s' }}>
          Keep your API docs in sync{' '}
          <span className="serif-italic">automatically</span>.
        </h1>

        {/* Lede paragraph */}
        <p className="hero-lede animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
          Detect API changes, understand what changed, and automatically update
          and validate your OpenAPI documentation.
        </p>

        {/* CTA buttons */}
        <div className="hero-cta animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
          <CTAButton
            variant="primary"
            onClick={onAnalyzeClick}
          >
            Analyze Repository
          </CTAButton>
          <CTAButton variant="secondary" onClick={onSeeItInAction}>
            See it in action
          </CTAButton>
        </div>

        {/* Bottom stats */}
        <div className="hero-stats animate-fade-in-up" style={{ animationDelay: '0.5s' }}>
          {stats.map((stat, index) => (
            <StatItem
              key={index}
              value={stat.value}
              label={stat.label}
            />
          ))}
        </div>
      </div>
    </section>
  );
};

export default Hero;
