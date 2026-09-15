import React, { useCallback, useState } from 'react';
import Navigation from './components/Navigation';
import Hero from './components/Hero';
import DemoWorkflow from './components/DemoWorkflow';
import DemoIndicator from './components/DemoIndicator';
import RepositoryPrompt from './components/RepositoryPrompt';
import { DEMO_STEPS } from './data/demoData';
import { analyzeRepository, getDocumentation } from './services/api';
import { mapAnalysisToWorkflow } from './services/mapResult';
import './styles/global.css';
import './styles/hero.css';
import './styles/demo.css';
import './styles/responsive.css';

function App() {
  const [mode, setMode] = useState('demo'); // 'demo' | 'live'
  const [ui, setUi] = useState('idle'); // 'idle' | 'prompt' | 'running' | 'complete'
  const [workflow, setWorkflow] = useState(DEMO_STEPS);
  const [result, setResult] = useState(null);
  const [notice, setNotice] = useState(null);

  // Check for reduced motion preference
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /** Launch the offline deterministic demo (no backend, no network). */
  const launchDemo = useCallback(() => {
    setMode('demo');
    setWorkflow(DEMO_STEPS);
    setUi('running');
  }, []);

  /** Run LIVE analysis against the backend; fall back to demo on failure. */
  const runLiveAnalysis = useCallback(async (repositoryUrl) => {
    setMode('live');
    setNotice(null);
    setUi('running');
    try {
      const backend = await analyzeRepository(repositoryUrl, { demoMode: false });
      setWorkflow(mapAnalysisToWorkflow(backend));
      setResult(backend);
      // Fetch the generated documentation (non-blocking, best-effort).
      if (backend.analysis_id) {
        getDocumentation(backend.analysis_id)
          .then((doc) => setResult((prev) => (prev ? { ...prev, documentation: doc } : prev)))
          .catch(() => { /* documentation fetch is best-effort */ });
      }
    } catch (err) {
      // Backend unavailable / timeout → graceful fallback to DEMO MODE.
      if (err.name === 'AbortError') {
        setNotice('Request timed out — running DEMO MODE');
      } else if (!err.status) {
        setNotice('Backend unavailable — running DEMO MODE');
      } else {
        // A real backend error: surface a concise message, stay in prompt.
        setNotice(`Live analysis failed — ${err.message}`);
        setUi('prompt');
        return;
      }
      setMode('demo');
      setWorkflow(DEMO_STEPS);
      setUi('running');
    }
  }, []);

  /** Called when the workflow animation plays out. */
  const handleWorkflowComplete = useCallback(() => {
    setUi('complete');
    // After the polished animation, restore the hero.
    setTimeout(() => {
      setUi('idle');
      setWorkflow(DEMO_STEPS);
      setNotice(null);
      setResult(null);
    }, 1200);
  }, []);

  const validationPassed = result?.summary?.validation_passed !== false;
  const finalStatus = validationPassed ? 'synchronized' : 'outdated';
  const completeText = validationPassed
    ? 'Documentation Synchronized'
    : 'Validation failed — docs out of sync';
  const showWorkflow = ui === 'running';
  const showPrompt = ui === 'prompt';

  return (
    <div className={`app ${prefersReducedMotion ? 'reduced-motion' : ''}`}>
      {/* Grain effect overlay */}
      <div className="grain-overlay" aria-hidden="true"></div>

      {/* Mode indicator */}
      <DemoIndicator mode={mode} />

      {/* Navigation */}
      <Navigation />

      {/* Main content */}
      <main className="main-content">
        {/* Hero section */}
        <Hero
          onAnalyzeClick={() => {
            setNotice(null);
            setUi('prompt');
          }}
          onSeeItInAction={launchDemo}
        />

        {/* Compact URL prompt for LIVE analysis */}
        {showPrompt && (
          <RepositoryPrompt
            onSubmit={runLiveAnalysis}
            onCancel={() => setUi('idle')}
            notice={notice}
          />
        )}

        {/* Analysis workflow visualization */}
        {showWorkflow && (
          <DemoWorkflow
            steps={workflow}
            notice={notice}
            finalStatus={finalStatus}
            completeText={completeText}
            onComplete={handleWorkflowComplete}
          />
        )}
      </main>
    </div>
  );
}

export default App;