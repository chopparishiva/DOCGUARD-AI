import React, { useEffect, useRef, useState } from 'react';
import { validateRepositoryUrl } from '../services/mapResult';

/**
 * Compact repository URL prompt — the smallest possible interaction for
 * LIVE analysis. Rendered as a subtle glass overlay on the hero, using
 * the existing visual language (blurred panel, pill buttons, demo-status
 * accents). Never a big form, never a new page.
 */
const RepositoryPrompt = ({ onSubmit, onCancel, notice = null }) => {
  const [value, setValue] = useState('');
  const [error, setError] = useState(null);
  const inputRef = useRef(null);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = () => {
    const message = validateRepositoryUrl(value);
    if (message) {
      setError(message);
      return;
    }
    setError(null);
    onSubmit(value.trim());
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') handleSubmit();
    if (e.key === 'Escape') onCancel();
  };

  return (
    <div className="repo-prompt" role="dialog" aria-label="Analyze a live repository">
      <div className="repo-prompt__card">
        <p className="repo-prompt__title">Analyze a repository</p>
        <p className="repo-prompt__hint">
          Paste a public GitHub URL. DocGuard AI will detect endpoint changes
          against the existing OpenAPI documentation.
        </p>

        <input
          ref={inputRef}
          className={`repo-prompt__input ${error ? 'has-error' : ''}`}
          type="text"
          placeholder="https://github.com/owner/repo"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={handleKeyDown}
          spellCheck={false}
          autoComplete="off"
        />

        {notice && <p className="repo-prompt__notice">{notice}</p>}
        {error && <p className="repo-prompt__error">{error}</p>}

        <div className="repo-prompt__actions">
          <button className="cta-button cta-button--primary repo-prompt__btn" onClick={handleSubmit}>
            <span className="cta-button__text">Analyze</span>
            <div className="cta-button__glow" aria-hidden="true"></div>
          </button>
          <button className="cta-button cta-button--secondary repo-prompt__btn" onClick={onCancel}>
            <span className="cta-button__text">Cancel</span>
          </button>
        </div>
      </div>
    </div>
  );
};

export default RepositoryPrompt;