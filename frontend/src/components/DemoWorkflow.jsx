import React, { useState, useEffect, useRef } from 'react';
import { DEMO_STEPS } from '../data/demoData';

/** Animation window per step — keep the exact existing demo cadence. */
const STEP_WINDOW_MS = 850;

const DemoWorkflow = ({
  onComplete,
  steps = DEMO_STEPS,
  completeText = 'Documentation Synchronized',
  finalStatus = 'synchronized', // 'synchronized' | 'outdated'
  notice = null,
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [completedSteps, setCompletedSteps] = useState([]);
  const [overallStatus, setOverallStatus] = useState('analyzing');
  const timerRefs = useRef([]);

  const isOutdated = finalStatus === 'outdated';

  // Run the animation sequence on mount
  useEffect(() => {
    // Clear any existing timers
    timerRefs.current.forEach(clearTimeout);

    // Each step is "active" (running) for its window, then completes when
    // the next step takes the stage.
    steps.forEach((_, index) => {
      const runTimer = setTimeout(() => {
        setActiveStep(index);
      }, index * STEP_WINDOW_MS);

      const doneTimer = setTimeout(() => {
        setCompletedSteps(prev => (prev.includes(index) ? prev : [...prev, index]));
      }, (index + 1) * STEP_WINDOW_MS);

      timerRefs.current.push(runTimer, doneTimer);
    });

    // Final completion state
    const finalTimer = setTimeout(() => {
      setCompletedSteps(prev =>
        prev.includes(steps.length - 1) ? prev : [...prev, steps.length - 1]
      );
      setOverallStatus('complete');
      if (onComplete) {
        timerRefs.current.push(setTimeout(onComplete, 1400));
      }
    }, (steps.length + 1) * STEP_WINDOW_MS);

    timerRefs.current.push(finalTimer);

    return () => {
      timerRefs.current.forEach(clearTimeout);
    };
  }, []);

  return (
    <section
      className={`demo-workflow ${overallStatus === 'complete' ? 'is-complete' : ''}`}
    >
      <div className="demo-workflow__header">
        <div className={`demo-status ${overallStatus === 'complete'
          ? (isOutdated ? 'status-outdated' : 'status-complete')
          : 'status-running'}`}>
          <span className="demo-status__dot"></span>
          <span className="demo-status__label">
            {overallStatus === 'complete'
              ? (isOutdated ? 'Synchronization failed' : 'Synchronized')
              : 'Analysis running'}
          </span>
        </div>
      </div>

      {notice && (
        <div className="demo-workflow__notice" role="status">
          {notice}
        </div>
      )}

      <div className="demo-workflow__steps">
        {steps.map((step, index) => {
          const isActive = activeStep === index;
          const isCompleted = completedSteps.includes(index);
          const isLast = index === steps.length - 1;

          return (
            <React.Fragment key={step.id || step.step}>
              <div
                className={`workflow-step ${
                  isCompleted ? 'is-complete' : ''
                } ${isActive ? 'is-active' : ''}`}
              >
                <div className="workflow-step__icon">
                  {isCompleted ? (
                    <CheckIcon />
                  ) : isActive ? (
                    <SpinnerIcon />
                  ) : (
                    <div className="workflow-step__pending"></div>
                  )}
                </div>
                <div className="workflow-step__content">
                  <span className="workflow-step__title">{step.step}</span>
                  <span className="workflow-step__detail">
                    {isCompleted ? step.detail : step.pending}
                  </span>
                </div>
              </div>

              {!isLast && (
                <div className={`workflow-connector ${isCompleted ? 'is-complete' : ''}`}>
                  <ConnectorIcon />
                </div>
              )}
            </React.Fragment>
          );
        })}
      </div>

      <div className="demo-workflow__footer">
        <span className={`demo-workflow__result ${isOutdated ? 'is-outdated' : ''}`}>
          {overallStatus === 'complete' ? (
            <>
              {isOutdated ? <AlertIcon /> : <CheckIcon />} {completeText}
            </>
          ) : (
            <>Processing repository…</>
          )}
        </span>
      </div>
    </section>
  );
};

const CheckIcon = () => (
  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="20 6 9 17 4 12"></polyline>
  </svg>
);

const AlertIcon = () => (
  <svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"></circle>
    <line x1="12" y1="8" x2="12" y2="12"></line>
    <line x1="12" y1="16" x2="12.01" y2="16"></line>
  </svg>
);

const SpinnerIcon = () => (
  <svg className="spinner" viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round">
    <path d="M21 12a9 9 0 1 1-6.219-8.56"></path>
  </svg>
);

const ConnectorIcon = () => (
  <svg viewBox="0 0 24 24" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
    <path d="M5 12h14"></path>
  </svg>
);

export default DemoWorkflow;